"""
JSON output module for generating analysis results.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any
from datetime import datetime

from .config import Config
from . import __version__


class JSONOutput:
    """Handles generation and output of analysis results in JSON format."""
    
    def __init__(self, config: Config):
        """Initialize JSON output handler with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def generate_output(self, analysis_results: Dict[str, Any], source_files: List[Path], 
                       total_loops: int, start_time: datetime) -> Dict[str, Any]:
        """Generate the complete JSON output structure."""
        end_time = datetime.now()
        
        # Generate metadata
        metadata = {
            'version': '1.0.0',
            'generated_at': end_time.isoformat(),
            'tool_version': __version__,
            'scan_path': str(self.config.source_path),
            'compiler_flags': self.config.get_compiler_flags(),
            'total_files_scanned': len(source_files),
            'total_loops_found': total_loops,
            'analysis_duration_seconds': (end_time - start_time).total_seconds(),
        }
        
        # Generate analysis summary
        analysis_summary = self._generate_analysis_summary(analysis_results)
        
        # Generate call graph
        call_graph = self._generate_call_graph(analysis_results)
        
        # Complete output structure
        output_data = {
            'metadata': metadata,
            'analysis_summary': analysis_summary,
            'source_files': analysis_results,
            'call_graph': call_graph,
            'extensions': {
                'future_analysis': {
                    'placeholder': 'Reserved for future analysis data'
                }
            }
        }
        
        return output_data
    
    def _generate_analysis_summary(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from analysis results."""
        loop_types = {
            'for_loops': 0,
            'while_loops': 0,
            'do_while_loops': 0,
            'range_for_loops': 0,
        }
        
        nesting_levels = []
        functions_with_loops = 0
        
        for file_path, file_data in analysis_results.items():
            # Count loop types and collect nesting levels
            self._count_loops_in_container(file_data.get('functions', {}), loop_types, nesting_levels)
            
            # Count loops in class methods
            for class_data in file_data.get('classes', {}).values():
                self._count_loops_in_container(class_data.get('methods', {}), loop_types, nesting_levels)
            
            # Count global loops
            for loop in file_data.get('global_loops', []):
                loop_type = loop.get('type', 'unknown')
                if loop_type in loop_types:
                    loop_types[loop_type] += 1
                nesting_levels.append(loop.get('nesting_level', 1))
            
            # Count functions with loops
            for func_data in file_data.get('functions', {}).values():
                if func_data.get('loops'):
                    functions_with_loops += 1
            
            for class_data in file_data.get('classes', {}).values():
                for method_data in class_data.get('methods', {}).values():
                    if method_data.get('loops'):
                        functions_with_loops += 1
        
        # Calculate nesting statistics
        max_depth = max(nesting_levels) if nesting_levels else 0
        avg_depth = sum(nesting_levels) / len(nesting_levels) if nesting_levels else 0
        
        return {
            'loop_types': loop_types,
            'nesting_levels': {
                'max_depth': max_depth,
                'average_depth': round(avg_depth, 2),
            },
            'functions_with_loops': functions_with_loops,
        }
    
    def _count_loops_in_container(self, container: Dict[str, Any], loop_types: Dict[str, int], 
                                 nesting_levels: List[int]) -> None:
        """Count loops in a container (functions or methods)."""
        for item_data in container.values():
            loops = item_data.get('loops', [])
            self._count_loops_recursive(loops, loop_types, nesting_levels)
    
    def _count_loops_recursive(self, loops: List[Dict], loop_types: Dict[str, int], 
                              nesting_levels: List[int]) -> None:
        """Recursively count loops and collect nesting levels."""
        for loop in loops:
            loop_type = loop.get('type', 'unknown')
            if loop_type in loop_types:
                loop_types[loop_type] += 1
            
            nesting_level = loop.get('nesting_level', 1)
            nesting_levels.append(nesting_level)
            
            # Process nested loops
            nested_loops = loop.get('nested_loops', [])
            self._count_loops_recursive(nested_loops, loop_types, nesting_levels)
    
    def _generate_call_graph(self, analysis_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate call graph from analysis results."""
        call_graph = {}
        
        try:
            for file_path, file_data in analysis_results.items():
                # Process functions
                for func_name, func_data in file_data.get('functions', {}).items():
                    if func_name not in call_graph:
                        call_graph[func_name] = {
                            'calls': [],
                            'called_by': [],
                            'calls_in_loops': [],
                        }
                    
                    # Extract function calls from loops
                    self._extract_calls_from_loops(func_data.get('loops', []), call_graph[func_name])
                
                # Process class methods
                for class_name, class_data in file_data.get('classes', {}).items():
                    for method_name, method_data in class_data.get('methods', {}).items():
                        qualified_name = f"{class_name}::{method_name}"
                        
                        if qualified_name not in call_graph:
                            call_graph[qualified_name] = {
                                'calls': [],
                                'called_by': [],
                                'calls_in_loops': [],
                            }
                        
                        # Extract function calls from loops
                        self._extract_calls_from_loops(method_data.get('loops', []), call_graph[qualified_name])
        
        except Exception as e:
            self.logger.warning(f"Error generating call graph: {e}")
        
        return call_graph
    
    def _extract_calls_from_loops(self, loops: List[Dict], call_info: Dict[str, List]) -> None:
        """Extract function calls from loops for call graph."""
        for loop in loops:
            # Extract calls from this loop
            for call in loop.get('function_calls', []):
                function_name = call.get('function', '')
                if function_name and function_name not in call_info['calls_in_loops']:
                    call_info['calls_in_loops'].append(function_name)
                if function_name and function_name not in call_info['calls']:
                    call_info['calls'].append(function_name)
            
            # Process nested loops
            nested_loops = loop.get('nested_loops', [])
            self._extract_calls_from_loops(nested_loops, call_info)
    
    def write_output(self, output_data: Dict[str, Any], output_path: str) -> None:
        """Write the analysis results to a JSON file."""
        try:
            output_file = Path(output_path)
            
            # Create directory if it doesn't exist
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Write JSON with pretty formatting
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Analysis results written to: {output_file}")
            
        except Exception as e:
            self.logger.error(f"Error writing output file {output_path}: {e}")
            raise
    
    def validate_output(self, output_data: Dict[str, Any]) -> bool:
        """Validate the output data structure."""
        try:
            # Check required top-level keys
            required_keys = {'metadata', 'analysis_summary', 'source_files', 'call_graph', 'extensions'}
            if not all(key in output_data for key in required_keys):
                return False
            
            # Validate metadata
            metadata = output_data['metadata']
            metadata_keys = {'version', 'generated_at', 'tool_version', 'scan_path', 'total_files_scanned', 'total_loops_found'}
            if not all(key in metadata for key in metadata_keys):
                return False
            
            # Validate analysis summary
            summary = output_data['analysis_summary']
            if 'loop_types' not in summary or 'nesting_levels' not in summary:
                return False
            
            self.logger.debug("Output validation passed")
            return True
            
        except Exception as e:
            self.logger.error(f"Output validation failed: {e}")
            return False