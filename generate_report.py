#!/usr/bin/env python3
"""
Generate a summary report of the EnergyPlus Loop Analysis
"""

import json
from collections import Counter
from pathlib import Path

def generate_summary_report(json_file):
    """Generate a comprehensive text summary report"""
    
    print("Loading EnergyPlus Analysis Data...")
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Extract key metrics
    total_files = len(data['source_files'])
    total_loops = data['metadata']['total_loops_found']
    analysis_duration = data['metadata']['analysis_duration_seconds']
    total_functions_in_call_graph = len(data.get('call_graph', {}))
    
    # File analysis
    files_with_loops = 0
    total_functions = 0
    total_function_calls = 0
    loop_types = Counter()
    file_extensions = Counter()
    functions_per_file = []
    loops_per_file = []
    
    for file_path, file_data in data['source_files'].items():
        file_ext = Path(file_path).suffix
        file_extensions[file_ext] += 1
        
        functions = file_data.get('functions', {})
        total_functions += len(functions)
        functions_per_file.append(len(functions))
        
        file_loops = 0
        file_function_calls = 0
        
        for func_data in functions.values():
            loops = func_data.get('loops', [])
            file_loops += len(loops)
            
            for loop_data in loops:
                loop_type = loop_data.get('loop_type', 'unknown')
                loop_types[loop_type] += 1
                
                operations = loop_data.get('operations', {})
                function_calls = operations.get('function_calls', [])
                file_function_calls += len(function_calls)
        
        loops_per_file.append(file_loops)
        total_function_calls += file_function_calls
        
        if file_loops > 0:
            files_with_loops += 1
    
    # Call graph analysis
    call_graph_stats = {}
    top_called_functions = Counter()
    
    if 'call_graph' in data:
        call_graph = data['call_graph']
        call_graph_stats = {
            'total_functions': len(call_graph),
            'functions_with_calls': sum(1 for func_data in call_graph.values() if func_data.get('calls')),
            'functions_called_by_others': sum(1 for func_data in call_graph.values() if func_data.get('called_by')),
            'functions_with_loop_calls': sum(1 for func_data in call_graph.values() if func_data.get('calls_in_loops')),
        }
        
        # Count function call frequency
        for func_name, func_data in call_graph.items():
            calls = func_data.get('calls', [])
            top_called_functions.update(calls)
    
    # Find top files by various metrics
    file_metrics = []
    for file_path, file_data in data['source_files'].items():
        functions = file_data.get('functions', {})
        total_loops_in_file = sum(len(func.get('loops', [])) for func in functions.values())
        total_calls_in_file = 0
        
        for func_data in functions.values():
            for loop_data in func_data.get('loops', []):
                operations = loop_data.get('operations', {})
                total_calls_in_file += len(operations.get('function_calls', []))
        
        file_name = Path(file_path).name
        file_metrics.append({
            'file': file_name,
            'functions': len(functions),
            'loops': total_loops_in_file,
            'function_calls': total_calls_in_file
        })
    
    # Sort to get top files
    top_files_by_loops = sorted(file_metrics, key=lambda x: x['loops'], reverse=True)[:10]
    top_files_by_functions = sorted(file_metrics, key=lambda x: x['functions'], reverse=True)[:10]
    top_files_by_calls = sorted(file_metrics, key=lambda x: x['function_calls'], reverse=True)[:10]
    
    # Generate the report
    report = f"""
# EnergyPlus Loop Analysis Summary Report
Generated from: {json_file}
Analysis Date: {data['metadata']['generated_at']}
Analysis Duration: {analysis_duration/60:.1f} minutes ({analysis_duration:.2f} seconds)

## Overall Statistics
- **Total Files Analyzed**: {total_files:,}
- **Total Functions Found**: {total_functions:,}
- **Total Loops Found**: {total_loops:,}
- **Total Function Calls in Loops**: {total_function_calls:,}
- **Files with Loops**: {files_with_loops:,} ({100*files_with_loops/total_files:.1f}%)
- **Files without Loops**: {total_files - files_with_loops:,} ({100*(total_files-files_with_loops)/total_files:.1f}%)

## File Type Distribution
"""
    
    for ext, count in file_extensions.most_common():
        percentage = 100 * count / total_files
        report += f"- **{ext or 'No extension'}**: {count} files ({percentage:.1f}%)\n"
    
    report += f"""
## Loop Analysis
- **Average Loops per File**: {sum(loops_per_file)/len(loops_per_file):.1f}
- **Max Loops in Single File**: {max(loops_per_file)}
- **Files with 10+ Loops**: {sum(1 for x in loops_per_file if x >= 10)}
- **Files with 50+ Loops**: {sum(1 for x in loops_per_file if x >= 50)}

### Loop Types Distribution
"""
    
    for loop_type, count in loop_types.most_common():
        percentage = 100 * count / total_loops if total_loops > 0 else 0
        report += f"- **{loop_type}**: {count:,} ({percentage:.1f}%)\n"
    
    report += f"""
## Function Analysis
- **Average Functions per File**: {sum(functions_per_file)/len(functions_per_file):.1f}
- **Max Functions in Single File**: {max(functions_per_file)}
- **Average Function Calls per Loop**: {total_function_calls/total_loops if total_loops > 0 else 0:.1f}

## Call Graph Statistics
"""
    
    if call_graph_stats:
        report += f"""- **Total Functions in Call Graph**: {call_graph_stats['total_functions']:,}
- **Functions Making Calls**: {call_graph_stats['functions_with_calls']:,}
- **Functions Called by Others**: {call_graph_stats['functions_called_by_others']:,}
- **Functions with Loop Calls**: {call_graph_stats['functions_with_loop_calls']:,}
"""
    
    report += f"""
## Top 10 Files by Loop Count
"""
    for i, file_data in enumerate(top_files_by_loops, 1):
        report += f"{i}. **{file_data['file']}**: {file_data['loops']} loops, {file_data['functions']} functions\n"
    
    report += f"""
## Top 10 Files by Function Count
"""
    for i, file_data in enumerate(top_files_by_functions, 1):
        report += f"{i}. **{file_data['file']}**: {file_data['functions']} functions, {file_data['loops']} loops\n"
    
    report += f"""
## Top 10 Files by Function Calls in Loops
"""
    for i, file_data in enumerate(top_files_by_calls, 1):
        report += f"{i}. **{file_data['file']}**: {file_data['function_calls']} function calls, {file_data['loops']} loops\n"
    
    report += f"""
## Top 15 Most Called Functions
"""
    for i, (func_name, count) in enumerate(top_called_functions.most_common(15), 1):
        report += f"{i}. **{func_name}**: {count:,} calls\n"
    
    report += f"""
## Key Insights
1. **Scale**: This is a massive codebase with {total_files} files and {total_loops:,} loops
2. **Loop Density**: {100*files_with_loops/total_files:.1f}% of files contain loops, indicating significant computational complexity
3. **Function Call Intensity**: {total_function_calls:,} function calls within loops shows high inter-component coupling
4. **Analysis Efficiency**: Processed {total_files} files in {analysis_duration/60:.1f} minutes ({total_files/(analysis_duration/60):.1f} files/minute)

## Generated Visualizations
The following charts were generated:
- **energyplus_overview_analysis.png**: Overall distribution and summary statistics
- **energyplus_detailed_analysis.png**: Detailed analysis with top functions and complexity metrics
- **energyplus_top_files_analysis.png**: Analysis of most complex files by various metrics
- **energyplus_function_network_analysis.png**: Function call network analysis and connectivity

---
*Report generated by Loop Explorer v1.0.0*
"""
    
    return report

if __name__ == "__main__":
    report = generate_summary_report('energyplus.json')
    
    # Save to file
    with open('EnergyPlus_Analysis_Report.md', 'w') as f:
        f.write(report)
    
    print("Summary report generated: EnergyPlus_Analysis_Report.md")
    print("\n" + "="*80)
    print(report)