#!/usr/bin/env python3
"""
Loop Bounds Extractor
Extracts and analyzes loop bounds information from EnergyPlus analysis JSON
"""

import json
import csv
import pandas as pd
from collections import Counter, defaultdict
from pathlib import Path
import re

def extract_loop_bounds(json_file):
    """Extract all loop bounds from the analysis JSON file"""
    print(f"Loading data from {json_file}...")
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    loop_bounds_data = []
    loop_bounds_stats = {
        'total_loops': 0,
        'loops_with_bounds': 0,
        'initialization_patterns': Counter(),
        'condition_patterns': Counter(),
        'increment_patterns': Counter(),
        'iteration_estimates': Counter()
    }
    
    print("Extracting loop bounds...")
    
    for file_path, file_data in data['source_files'].items():
        file_name = Path(file_path).name
        
        for func_name, func_data in file_data.get('functions', {}).items():
            for loop_idx, loop_data in enumerate(func_data.get('loops', [])):
                loop_bounds_stats['total_loops'] += 1
                
                # Extract basic loop info
                loop_info = {
                    'file_name': file_name,
                    'file_path': file_path,
                    'function_name': func_name,
                    'loop_index': loop_idx,
                    'loop_type': loop_data.get('type', 'unknown'),
                    'start_line': loop_data.get('location', {}).get('start_line', 'unknown'),
                    'end_line': loop_data.get('location', {}).get('end_line', 'unknown'),
                }
                
                # Extract loop bounds if available
                if 'loop_bounds' in loop_data:
                    loop_bounds_stats['loops_with_bounds'] += 1
                    bounds = loop_data['loop_bounds']
                    
                    initialization = bounds.get('initialization', '')
                    condition = bounds.get('condition', '')
                    increment = bounds.get('increment', '')
                    estimated_iterations = bounds.get('estimated_iterations', 'unknown')
                    
                    # Update statistics
                    loop_bounds_stats['initialization_patterns'][initialization] += 1
                    loop_bounds_stats['condition_patterns'][condition] += 1
                    loop_bounds_stats['increment_patterns'][increment] += 1
                    loop_bounds_stats['iteration_estimates'][estimated_iterations] += 1
                    
                    # Add to loop info
                    loop_info.update({
                        'has_bounds': True,
                        'initialization': initialization,
                        'condition': condition,
                        'increment': increment,
                        'estimated_iterations': estimated_iterations
                    })
                else:
                    loop_info.update({
                        'has_bounds': False,
                        'initialization': '',
                        'condition': '',
                        'increment': '',
                        'estimated_iterations': 'unknown'
                    })
                
                loop_bounds_data.append(loop_info)
    
    return loop_bounds_data, loop_bounds_stats

def analyze_loop_patterns(loop_bounds_data):
    """Analyze patterns in loop bounds"""
    print("Analyzing loop patterns...")
    
    patterns = {
        'variable_patterns': defaultdict(list),
        'operator_patterns': defaultdict(list),
        'increment_types': defaultdict(list),
        'iteration_ranges': defaultdict(list)
    }
    
    for loop_info in loop_bounds_data:
        if not loop_info['has_bounds']:
            continue
            
        init = loop_info['initialization']
        condition = loop_info['condition']
        increment = loop_info['increment']
        
        # Extract variable names from initialization
        init_match = re.search(r'(\w+)\s*=', init)
        if init_match:
            var_name = init_match.group(1)
            patterns['variable_patterns'][var_name].append(loop_info)
        
        # Extract comparison operators from condition
        for op in ['<=', '>=', '<', '>', '==', '!=']:
            if op in condition:
                patterns['operator_patterns'][op].append(loop_info)
                break
        
        # Categorize increment types
        if '++' in increment:
            patterns['increment_types']['pre/post_increment'].append(loop_info)
        elif '--' in increment:
            patterns['increment_types']['pre/post_decrement'].append(loop_info)
        elif '+=' in increment:
            patterns['increment_types']['compound_addition'].append(loop_info)
        elif '-=' in increment:
            patterns['increment_types']['compound_subtraction'].append(loop_info)
        else:
            patterns['increment_types']['other'].append(loop_info)
    
    return patterns

def export_to_csv(loop_bounds_data, filename):
    """Export loop bounds data to CSV"""
    print(f"Exporting data to {filename}...")
    
    df = pd.DataFrame(loop_bounds_data)
    df.to_csv(filename, index=False)
    print(f"Exported {len(loop_bounds_data)} loop records to {filename}")

def export_to_json(loop_bounds_data, filename):
    """Export loop bounds data to JSON"""
    print(f"Exporting data to {filename}...")
    
    with open(filename, 'w') as f:
        json.dump(loop_bounds_data, f, indent=2)
    print(f"Exported {len(loop_bounds_data)} loop records to {filename}")

def generate_summary_report(loop_bounds_stats, patterns, output_file):
    """Generate a summary report of loop bounds analysis"""
    
    report = f"""# Loop Bounds Analysis Report

## Overview
- **Total Loops**: {loop_bounds_stats['total_loops']:,}
- **Loops with Bounds**: {loop_bounds_stats['loops_with_bounds']:,}
- **Coverage**: {100 * loop_bounds_stats['loops_with_bounds'] / loop_bounds_stats['total_loops']:.1f}%

## Initialization Patterns (Top 20)
"""
    
    for pattern, count in loop_bounds_stats['initialization_patterns'].most_common(20):
        if pattern:  # Skip empty patterns
            report += f"- `{pattern}`: {count} loops\n"
    
    report += f"""
## Condition Patterns (Top 20)
"""
    
    for pattern, count in loop_bounds_stats['condition_patterns'].most_common(20):
        if pattern:  # Skip empty patterns  
            report += f"- `{pattern}`: {count} loops\n"
    
    report += f"""
## Increment Patterns (Top 20)
"""
    
    for pattern, count in loop_bounds_stats['increment_patterns'].most_common(20):
        if pattern:  # Skip empty patterns
            report += f"- `{pattern}`: {count} loops\n"
    
    report += f"""
## Variable Name Analysis
"""
    
    var_counts = {var: len(loops) for var, loops in patterns['variable_patterns'].items()}
    sorted_vars = sorted(var_counts.items(), key=lambda x: x[1], reverse=True)
    
    for var_name, count in sorted_vars[:15]:
        report += f"- **{var_name}**: {count} loops\n"
    
    report += f"""
## Comparison Operators
"""
    
    for op, loops in patterns['operator_patterns'].items():
        report += f"- **{op}**: {len(loops)} loops\n"
    
    report += f"""
## Increment Types
"""
    
    for inc_type, loops in patterns['increment_types'].items():
        report += f"- **{inc_type}**: {len(loops)} loops\n"
    
    report += f"""
## Iteration Estimates
"""
    
    for estimate, count in loop_bounds_stats['iteration_estimates'].most_common(10):
        if estimate != 'unknown':
            report += f"- **{estimate}**: {count} loops\n"
    
    unknown_count = loop_bounds_stats['iteration_estimates']['unknown']
    report += f"- **unknown**: {unknown_count} loops\n"
    
    with open(output_file, 'w') as f:
        f.write(report)
    
    print(f"Summary report saved to {output_file}")
    return report

def create_focused_extracts(loop_bounds_data):
    """Create focused extracts for specific analysis"""
    
    # Extract loops with specific patterns
    focused_extracts = {}
    
    # 1. Loops with numeric bounds (likely fixed iteration count)
    numeric_bounds = []
    for loop in loop_bounds_data:
        if loop['has_bounds']:
            init = loop['initialization']
            condition = loop['condition']
            # Look for numeric patterns like "i = 0", "i < 10", etc.
            if re.search(r'=\s*\d+', init) and re.search(r'[<>=]+\s*\d+', condition):
                numeric_bounds.append(loop)
    
    focused_extracts['numeric_bounds'] = numeric_bounds
    
    # 2. Loops with array/container bounds
    array_bounds = []
    for loop in loop_bounds_data:
        if loop['has_bounds']:
            condition = loop['condition']
            # Look for patterns like ".size()", ".length", "[i]", etc.
            if any(pattern in condition for pattern in ['.size()', '.length', '.count', 'Size', 'Num', 'Max']):
                array_bounds.append(loop)
    
    focused_extracts['container_bounds'] = array_bounds
    
    # 3. Complex nested loops (multiple variables)
    complex_loops = []
    seen_functions = set()
    for loop in loop_bounds_data:
        func_key = f"{loop['file_name']}::{loop['function_name']}"
        if func_key in seen_functions:
            # This function has multiple loops - potentially nested
            complex_loops.append(loop)
        else:
            seen_functions.add(func_key)
    
    focused_extracts['potential_nested'] = complex_loops
    
    return focused_extracts

def main():
    """Main function to extract and analyze loop bounds"""
    json_file = 'energyplus.json'
    
    try:
        # Extract loop bounds data
        loop_bounds_data, loop_bounds_stats = extract_loop_bounds(json_file)
        
        # Analyze patterns
        patterns = analyze_loop_patterns(loop_bounds_data)
        
        # Export to different formats
        export_to_csv(loop_bounds_data, 'loop_bounds_data.csv')
        export_to_json(loop_bounds_data, 'loop_bounds_data.json')
        
        # Generate summary report
        report = generate_summary_report(loop_bounds_stats, patterns, 'loop_bounds_analysis_report.md')
        
        # Create focused extracts
        focused_extracts = create_focused_extracts(loop_bounds_data)
        
        # Export focused extracts
        for extract_name, extract_data in focused_extracts.items():
            export_to_csv(extract_data, f'loop_bounds_{extract_name}.csv')
            print(f"Created focused extract: loop_bounds_{extract_name}.csv ({len(extract_data)} loops)")
        
        # Print summary to console
        print("\n" + "="*80)
        print("LOOP BOUNDS EXTRACTION SUMMARY")
        print("="*80)
        print(f"Total loops found: {loop_bounds_stats['total_loops']:,}")
        print(f"Loops with bounds: {loop_bounds_stats['loops_with_bounds']:,}")
        print(f"Coverage: {100 * loop_bounds_stats['loops_with_bounds'] / loop_bounds_stats['total_loops']:.1f}%")
        
        print(f"\nTop 5 most common initialization patterns:")
        for pattern, count in loop_bounds_stats['initialization_patterns'].most_common(5):
            if pattern and len(pattern) > 0:
                print(f"  {pattern}: {count} loops")
        
        print(f"\nTop 5 most common condition patterns:")
        for pattern, count in loop_bounds_stats['condition_patterns'].most_common(5):
            if pattern and len(pattern) > 0:
                print(f"  {pattern}: {count} loops")
        
        print(f"\nTop 5 most common increment patterns:")
        for pattern, count in loop_bounds_stats['increment_patterns'].most_common(5):
            if pattern and len(pattern) > 0:
                print(f"  {pattern}: {count} loops")
        
        print(f"\nFiles generated:")
        print(f"  - loop_bounds_data.csv (all loop data)")
        print(f"  - loop_bounds_data.json (all loop data)")
        print(f"  - loop_bounds_analysis_report.md (summary report)")
        for extract_name in focused_extracts:
            print(f"  - loop_bounds_{extract_name}.csv (focused extract)")
        
    except FileNotFoundError:
        print(f"Error: Could not find {json_file}")
        print("Please ensure the EnergyPlus analysis JSON file exists in the current directory.")
    except Exception as e:
        print(f"Error extracting loop bounds: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()