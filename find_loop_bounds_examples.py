#!/usr/bin/env python3
"""
Loop Bounds Examples Finder
Find specific loop bounds examples and display them with context
"""

import json
import re
from pathlib import Path

def find_specific_loop_bounds(json_file, search_patterns=None):
    """Find loop bounds matching specific patterns"""
    
    print(f"Loading data from {json_file}...")
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Default search patterns if none provided
    if search_patterns is None:
        search_patterns = [
            {'name': 'AbsorberNum Pattern', 'init': 'AbsorberNum = 1', 'condition': 'AbsorberNum <= NumExhaustAbsorbers'},
            {'name': 'Loop Counter Pattern', 'init': 'Loop = 1'},
            {'name': 'Surface Number Pattern', 'init': 'SurfNum = 1'},
            {'name': 'Zone Number Pattern', 'condition': 'ZoneNum <= NumOfZones'},
            {'name': 'Air Loop Pattern', 'condition': 'AirLoopNum <= NumPrimaryAirSys'},
        ]
    
    print("Searching for specific loop bounds patterns...")
    
    results = {pattern['name']: [] for pattern in search_patterns}
    
    for file_path, file_data in data['source_files'].items():
        file_name = Path(file_path).name
        
        for func_name, func_data in file_data.get('functions', {}).items():
            for loop_idx, loop_data in enumerate(func_data.get('loops', [])):
                if 'loop_bounds' not in loop_data:
                    continue
                
                bounds = loop_data['loop_bounds']
                initialization = bounds.get('initialization', '')
                condition = bounds.get('condition', '')
                increment = bounds.get('increment', '')
                estimated_iterations = bounds.get('estimated_iterations', 'unknown')
                
                # Check against each search pattern
                for pattern in search_patterns:
                    pattern_name = pattern['name']
                    matches = True
                    
                    # Check initialization pattern if specified
                    if 'init' in pattern:
                        if pattern['init'] not in initialization:
                            matches = False
                    
                    # Check condition pattern if specified  
                    if 'condition' in pattern:
                        if pattern['condition'] not in condition:
                            matches = False
                    
                    # Check increment pattern if specified
                    if 'increment' in pattern:
                        if pattern['increment'] not in increment:
                            matches = False
                    
                    if matches:
                        loop_info = {
                            'file_name': file_name,
                            'file_path': file_path,
                            'function_name': func_name,
                            'loop_index': loop_idx,
                            'loop_type': loop_data.get('loop_type', 'unknown'),
                            'start_line': loop_data.get('location', {}).get('start_line', 'unknown'),
                            'end_line': loop_data.get('location', {}).get('end_line', 'unknown'),
                            'initialization': initialization,
                            'condition': condition,
                            'increment': increment,
                            'estimated_iterations': estimated_iterations,
                            'loop_bounds': bounds
                        }
                        results[pattern_name].append(loop_info)
    
    return results

def display_loop_bounds_examples(results, max_examples_per_pattern=5):
    """Display examples of found loop bounds"""
    
    print("\n" + "="*80)
    print("LOOP BOUNDS EXAMPLES")
    print("="*80)
    
    for pattern_name, loops in results.items():
        print(f"\n{pattern_name}: {len(loops)} matches")
        print("-" * (len(pattern_name) + 20))
        
        if not loops:
            print("  No matches found")
            continue
        
        # Show up to max_examples_per_pattern examples
        for i, loop in enumerate(loops[:max_examples_per_pattern]):
            print(f"\n  Example {i+1}:")
            print(f"    File: {loop['file_name']}")
            print(f"    Function: {loop['function_name']}")
            print(f"    Lines: {loop['start_line']}-{loop['end_line']}")
            print(f"    Loop Type: {loop['loop_type']}")
            print(f"    Bounds:")
            print(f"      Initialization: {loop['initialization']}")
            print(f"      Condition: {loop['condition']}")
            print(f"      Increment: {loop['increment']}")
            print(f"      Estimated Iterations: {loop['estimated_iterations']}")
        
        if len(loops) > max_examples_per_pattern:
            print(f"    ... and {len(loops) - max_examples_per_pattern} more examples")

def export_examples_to_json(results, filename):
    """Export specific examples to JSON file"""
    
    print(f"\nExporting examples to {filename}...")
    with open(filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    total_examples = sum(len(loops) for loops in results.values())
    print(f"Exported {total_examples} loop examples to {filename}")

def search_by_variable_name(json_file, variable_names):
    """Search for loops by specific variable names"""
    
    print(f"Searching for loops with variables: {', '.join(variable_names)}")
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    results = {var_name: [] for var_name in variable_names}
    
    for file_path, file_data in data['source_files'].items():
        file_name = Path(file_path).name
        
        for func_name, func_data in file_data.get('functions', {}).items():
            for loop_idx, loop_data in enumerate(func_data.get('loops', [])):
                if 'loop_bounds' not in loop_data:
                    continue
                
                bounds = loop_data['loop_bounds']
                initialization = bounds.get('initialization', '')
                condition = bounds.get('condition', '')
                increment = bounds.get('increment', '')
                
                # Check if any of the target variables appear in the loop bounds
                for var_name in variable_names:
                    if (var_name in initialization or 
                        var_name in condition or 
                        var_name in increment):
                        
                        loop_info = {
                            'file_name': file_name,
                            'function_name': func_name,
                            'start_line': loop_data.get('location', {}).get('start_line', 'unknown'),
                            'initialization': initialization,
                            'condition': condition,
                            'increment': increment,
                            'estimated_iterations': bounds.get('estimated_iterations', 'unknown')
                        }
                        results[var_name].append(loop_info)
    
    return results

def main():
    """Main function to find and display loop bounds examples"""
    json_file = 'energyplus.json'
    
    try:
        # Find specific patterns including the AbsorberNum example
        results = find_specific_loop_bounds(json_file)
        
        # Display examples
        display_loop_bounds_examples(results)
        
        # Export examples to JSON
        export_examples_to_json(results, 'loop_bounds_examples.json')
        
        # Search for specific variable names
        print(f"\n" + "="*80)
        print("VARIABLE-SPECIFIC SEARCH")
        print("="*80)
        
        common_variables = ['AbsorberNum', 'Loop', 'SurfNum', 'ZoneNum', 'AirLoopNum', 'i', 'j', 'k']
        var_results = search_by_variable_name(json_file, common_variables)
        
        for var_name, loops in var_results.items():
            if loops:
                print(f"\n{var_name}: {len(loops)} loops")
                # Show first example
                if loops:
                    loop = loops[0]
                    print(f"  Example: {loop['file_name']} -> {loop['function_name']}")
                    print(f"    Init: {loop['initialization']}")
                    print(f"    Condition: {loop['condition']}")
                    print(f"    Increment: {loop['increment']}")
        
        print(f"\nSearch completed! Check loop_bounds_examples.json for detailed results.")
        
    except FileNotFoundError:
        print(f"Error: Could not find {json_file}")
    except Exception as e:
        print(f"Error searching for loop bounds: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()