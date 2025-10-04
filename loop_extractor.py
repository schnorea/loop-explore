#!/usr/bin/env python3
"""
Loop Extractor - Main Entry Point

A Python-based utility that uses Clang AST to analyze C/C++ codebases 
and extract comprehensive loop information for High-Performance Computing (HPC) optimization.
"""

import argparse
import sys
import logging
import json
from pathlib import Path
from datetime import datetime

from src.config import Config
from src.file_discovery import FileDiscovery
from src.ast_parser import ASTParser
from src.loop_analyzer import LoopAnalyzer
from src.json_output import JSONOutput


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('loop_extractor.log')
        ]
    )


def create_argument_parser() -> argparse.ArgumentParser:
    """Create and configure the argument parser."""
    parser = argparse.ArgumentParser(
        description='Extract loop information from C/C++ codebases',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s src/                              # Analyze all files in src/
  %(prog)s src/ -o results.json              # Save results to specific file  
  %(prog)s --resume-from-checkpoint file.checkpoint.json  # Resume from checkpoint
        """
    )
    
    parser.add_argument(
        'path',
        type=str,
        nargs='?',
        help='Path to the source code directory to analyze'
    )
    
    parser.add_argument(
        '-o', '--output',
        type=str,
        default='loop_analysis.json',
        help='Output JSON file path (default: loop_analysis.json)'
    )
    
    parser.add_argument(
        '--include',
        action='append',
        help='Include pattern for files (can be specified multiple times)'
    )
    
    parser.add_argument(
        '--exclude',
        action='append',
        help='Exclude pattern for files (can be specified multiple times)'
    )
    
    parser.add_argument(
        '--cpp-standard',
        type=str,
        default='c++17',
        choices=['c++11', 'c++14', 'c++17', 'c++20'],
        help='C++ standard to use for parsing (default: c++17)'
    )
    
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (default: INFO)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output'
    )
    
    parser.add_argument(
        '--checkpoint-frequency',
        type=int,
        default=50,
        help='Save checkpoint every N files (default: 50)'
    )
    
    parser.add_argument(
        '--resume-from-checkpoint',
        type=str,
        help='Resume analysis from a checkpoint file'
    )
    
    return parser


def main() -> int:
    """Main entry point."""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Setup logging
    log_level = 'DEBUG' if args.verbose else args.log_level
    setup_logging(log_level)
    logger = logging.getLogger(__name__)
    
    try:
        # Handle checkpoint resume
        resume_data = None
        if args.resume_from_checkpoint:
            checkpoint_path = Path(args.resume_from_checkpoint)
            if not checkpoint_path.exists():
                logger.error(f"Checkpoint file does not exist: {args.resume_from_checkpoint}")
                return 1
            
            logger.info(f"Resuming from checkpoint: {checkpoint_path}")
            with open(checkpoint_path, 'r') as f:
                resume_data = json.load(f)
            
            # Extract configuration from checkpoint
            source_path = Path(resume_data['metadata']['scan_path'])
            output_path = checkpoint_path.with_suffix('.json')
            logger.info(f"Resuming analysis of: {source_path}")
            logger.info(f"Output will be written to: {output_path}")
        else:
            if not args.path:
                parser.error("path argument is required when not resuming from checkpoint")
            
            # Validate input path
            source_path = Path(args.path)
            if not source_path.exists():
                logger.error(f"Source path does not exist: {args.path}")
                return 1
                
            if not source_path.is_dir():
                logger.error(f"Source path is not a directory: {args.path}")
                return 1
            
            output_path = Path(args.output)
            logger.info(f"Starting loop analysis of: {source_path}")
        
        start_time = datetime.now()
        
        # Create configuration
        config = Config(
            source_path=source_path,
            output_path=output_path,
            include_patterns=args.include or [],
            exclude_patterns=args.exclude or [],
            cpp_standard=args.cpp_standard,
            log_level=log_level
        )
        if args.resume_from_checkpoint:
            try:
                with open(args.resume_from_checkpoint, 'r', encoding='utf-8') as f:
                    resume_data = json.load(f)
                logger.info(f"Resuming from checkpoint: {args.resume_from_checkpoint}")
                logger.info(f"Previous progress: {resume_data['metadata'].get('files_processed', 0)} files processed")
            except Exception as e:
                logger.error(f"Failed to load checkpoint {args.resume_from_checkpoint}: {e}")
                return 1
        
        # Phase 1: File Discovery
        logger.info("Phase 1: Discovering source files...")
        file_discovery = FileDiscovery(config)
        source_files = file_discovery.discover_files()
        
        if not source_files:
            logger.warning("No source files found to analyze")
            return 0
            
        logger.info(f"Found {len(source_files)} source files to analyze")
        
        # If resuming, filter out already processed files
        start_index = 0
        if resume_data:
            processed_files = set(resume_data.get('source_files', {}).keys())
            # Filter source_files to only include unprocessed ones
            remaining_files = [f for f in source_files if str(f) not in processed_files]
            start_index = len(source_files) - len(remaining_files)
            source_files = remaining_files
            logger.info(f"Resuming: {len(remaining_files)} files remaining to process")
        
        # Phase 2: AST Parsing and Loop Analysis
        logger.info("Phase 2: Parsing and analyzing loops...")
        ast_parser = ASTParser(config)
        loop_analyzer = LoopAnalyzer(config)
        
        # Initialize analysis state
        analysis_results = resume_data.get('source_files', {}) if resume_data else {}
        total_loops = sum(loop_analyzer.count_loops(file_data) for file_data in analysis_results.values()) if resume_data else 0
        processed_count = start_index
        total_files = len(source_files) + start_index  # Total including already processed
        
        # Checkpoint file path
        checkpoint_file = Path(args.output).with_suffix('.checkpoint.json')
        
        def save_checkpoint():
            """Save current analysis results as a checkpoint."""
            try:
                json_output = JSONOutput(config)
                # For checkpoint, we need to include all processed files
                all_processed_files = list(analysis_results.keys())
                all_processed_paths = [Path(f) for f in all_processed_files]
                
                checkpoint_data = json_output.generate_output(
                    analysis_results=analysis_results,
                    source_files=all_processed_paths,
                    total_loops=total_loops,
                    start_time=start_time
                )
                checkpoint_data['metadata']['checkpoint'] = True
                checkpoint_data['metadata']['files_processed'] = processed_count
                checkpoint_data['metadata']['files_remaining'] = total_files - processed_count
                
                json_output.write_output(checkpoint_data, str(checkpoint_file))
                logger.info(f"Checkpoint saved: {checkpoint_file} ({processed_count}/{total_files} files)")
            except Exception as e:
                logger.error(f"Failed to save checkpoint: {e}")
        
        try:
            for i, source_file in enumerate(source_files, 1):
                # Progress indication with time estimates
                current_progress = start_index + i
                progress_pct = (current_progress / total_files) * 100
                
                # Estimate remaining time
                elapsed_time = (datetime.now() - start_time).total_seconds()
                if i > 1:  # Avoid division by zero
                    avg_time_per_file = elapsed_time / i
                    remaining_files = len(source_files) - i
                    estimated_remaining = avg_time_per_file * remaining_files
                    eta_str = f", ETA: {estimated_remaining/60:.1f}min"
                else:
                    eta_str = ""
                
                logger.info(f"Progress: {current_progress}/{total_files} ({progress_pct:.1f}%){eta_str} - Analyzing: {source_file.name}")
                
                try:
                    # Parse AST
                    translation_unit = ast_parser.parse_file(source_file)
                    if translation_unit is None:
                        logger.warning(f"Failed to parse: {source_file}")
                        continue
                    
                    # Analyze loops
                    file_analysis = loop_analyzer.analyze_file(translation_unit, source_file)
                    analysis_results[str(source_file)] = file_analysis
                    
                    # Count loops for summary
                    file_loop_count = loop_analyzer.count_loops(file_analysis)
                    total_loops += file_loop_count
                    
                    logger.debug(f"Found {file_loop_count} loops in {source_file}")
                    
                except Exception as e:
                    logger.error(f"Error analyzing {source_file}: {e}")
                    continue
                finally:
                    processed_count = start_index + i
                    
                    # Save checkpoint based on frequency or on last file
                    if i % args.checkpoint_frequency == 0 or i == len(source_files):
                        save_checkpoint()
                        
        except KeyboardInterrupt:
            logger.info(f"Analysis interrupted by user after processing {processed_count}/{total_files} files")
            logger.info("Saving checkpoint with current results...")
            save_checkpoint()
            
            # Generate partial output
            logger.info("Generating partial results...")
            json_output = JSONOutput(config)
            
            # Include all processed files in the output
            all_processed_files = list(analysis_results.keys())
            all_processed_paths = [Path(f) for f in all_processed_files]
            
            output_data = json_output.generate_output(
                analysis_results=analysis_results,
                source_files=all_processed_paths,
                total_loops=total_loops,
                start_time=start_time
            )
            
            # Mark as interrupted
            output_data['metadata']['interrupted'] = True
            output_data['metadata']['files_processed'] = processed_count
            output_data['metadata']['files_remaining'] = total_files - processed_count
            
            json_output.write_output(output_data, args.output)
            
            logger.info(f"Partial analysis complete!")
            logger.info(f"Files processed: {processed_count}/{total_files}")
            logger.info(f"Total loops found: {total_loops}")
            logger.info(f"Partial results written to: {args.output}")
            logger.info(f"Checkpoint saved to: {checkpoint_file}")
            
            return 0
        
        # Phase 3: Generate Output
        logger.info("Phase 3: Generating JSON output...")
        json_output = JSONOutput(config)
        
        # Include all processed files in final output
        all_processed_files = list(analysis_results.keys())
        all_processed_paths = [Path(f) for f in all_processed_files]
        
        output_data = json_output.generate_output(
            analysis_results=analysis_results,
            source_files=all_processed_paths,
            total_loops=total_loops,
            start_time=start_time
        )
        
        json_output.write_output(output_data, args.output)
        
        # Clean up checkpoint file on successful completion
        if checkpoint_file.exists():
            try:
                checkpoint_file.unlink()
                logger.info("Checkpoint file cleaned up")
            except Exception as e:
                logger.warning(f"Could not remove checkpoint file: {e}")
        
        end_time = datetime.now()
        duration = end_time - start_time
        
        logger.info(f"Analysis complete!")
        logger.info(f"Files analyzed: {len(analysis_results)}")
        logger.info(f"Total loops found: {total_loops}")
        logger.info(f"Duration: {duration.total_seconds():.2f} seconds")
        logger.info(f"Output written to: {args.output}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("Analysis interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        logger.debug("Exception details:", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())