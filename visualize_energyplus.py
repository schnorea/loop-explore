#!/usr/bin/env python3
"""
EnergyPlus Loop Analysis Visualization Dashboard
Creates comprehensive charts and graphs from energyplus.json analysis results
"""

import json
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import seaborn as sns
import pandas as pd
import numpy as np
from collections import Counter, defaultdict
import math
from pathlib import Path

# Set style for better-looking plots
plt.style.use('seaborn-v0_8')
sns.set_palette("husl")

def load_data(json_file):
    """Load and parse the EnergyPlus analysis JSON file"""
    print(f"Loading data from {json_file}...")
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    print(f"Loaded analysis of {len(data['source_files'])} files")
    print(f"Total loops found: {data['metadata']['total_loops_found']}")
    print(f"Analysis duration: {data['metadata']['analysis_duration_seconds']:.2f} seconds")
    
    return data

def extract_metrics(data):
    """Extract key metrics for visualization"""
    metrics = {
        'total_files': len(data['source_files']),
        'total_loops': data['metadata']['total_loops_found'],
        'total_functions': 0,
        'total_function_calls': 0,
        'files_with_loops': 0,
        'loop_types': Counter(),
        'functions_per_file': [],
        'loops_per_file': [],
        'function_calls_per_loop': [],
        'file_sizes': [],
        'files_by_extension': Counter(),
        'top_function_calls': Counter(),
        'call_graph_stats': {}
    }
    
    # Extract call graph statistics
    if 'call_graph' in data:
        call_graph = data['call_graph']
        metrics['call_graph_stats'] = {
            'total_functions': len(call_graph),
            'functions_with_calls': sum(1 for func_data in call_graph.values() if func_data.get('calls')),
            'functions_called_by_others': sum(1 for func_data in call_graph.values() if func_data.get('called_by')),
            'functions_with_loop_calls': sum(1 for func_data in call_graph.values() if func_data.get('calls_in_loops')),
        }
        
        # Top functions by number of calls
        for func_name, func_data in call_graph.items():
            calls = func_data.get('calls', [])
            metrics['top_function_calls'].update(calls)
    
    # Process each source file
    for file_path, file_data in data['source_files'].items():
        file_ext = Path(file_path).suffix
        metrics['files_by_extension'][file_ext] += 1
        
        functions = file_data.get('functions', {})
        metrics['total_functions'] += len(functions)
        metrics['functions_per_file'].append(len(functions))
        
        file_loops = 0
        file_function_calls = 0
        
        for func_name, func_data in functions.items():
            loops = func_data.get('loops', [])
            file_loops += len(loops)
            
            for loop_data in loops:
                # Count loop types
                loop_type = loop_data.get('loop_type', 'unknown')
                metrics['loop_types'][loop_type] += 1
                
                # Count function calls in this loop
                operations = loop_data.get('operations', {})
                function_calls = operations.get('function_calls', [])
                file_function_calls += len(function_calls)
                metrics['function_calls_per_loop'].append(len(function_calls))
        
        metrics['loops_per_file'].append(file_loops)
        metrics['total_function_calls'] += file_function_calls
        
        if file_loops > 0:
            metrics['files_with_loops'] += 1
    
    return metrics

def create_overview_charts(metrics, data):
    """Create overview charts of the analysis"""
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle('EnergyPlus Loop Analysis Overview', fontsize=16, fontweight='bold')
    
    # 1. File types distribution
    extensions = dict(metrics['files_by_extension'].most_common())
    axes[0, 0].pie(extensions.values(), labels=extensions.keys(), autopct='%1.1f%%', startangle=90)
    axes[0, 0].set_title('Distribution of File Types')
    
    # 2. Loop types distribution
    loop_types = dict(metrics['loop_types'].most_common())
    axes[0, 1].bar(loop_types.keys(), loop_types.values(), color='skyblue')
    axes[0, 1].set_title('Loop Types Distribution')
    axes[0, 1].set_ylabel('Count')
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # 3. Files with vs without loops
    loop_data = [metrics['files_with_loops'], metrics['total_files'] - metrics['files_with_loops']]
    axes[0, 2].pie(loop_data, labels=['With Loops', 'Without Loops'], 
                   autopct='%1.1f%%', colors=['lightcoral', 'lightgray'])
    axes[0, 2].set_title('Files: With vs Without Loops')
    
    # 4. Functions per file histogram
    axes[1, 0].hist(metrics['functions_per_file'], bins=30, alpha=0.7, color='green', edgecolor='black')
    axes[1, 0].set_title('Distribution of Functions per File')
    axes[1, 0].set_xlabel('Number of Functions')
    axes[1, 0].set_ylabel('Number of Files')
    axes[1, 0].axvline(np.mean(metrics['functions_per_file']), color='red', linestyle='--', 
                       label=f'Mean: {np.mean(metrics["functions_per_file"]):.1f}')
    axes[1, 0].legend()
    
    # 5. Loops per file histogram  
    axes[1, 1].hist(metrics['loops_per_file'], bins=30, alpha=0.7, color='orange', edgecolor='black')
    axes[1, 1].set_title('Distribution of Loops per File')
    axes[1, 1].set_xlabel('Number of Loops')
    axes[1, 1].set_ylabel('Number of Files')
    axes[1, 1].axvline(np.mean(metrics['loops_per_file']), color='red', linestyle='--',
                       label=f'Mean: {np.mean(metrics["loops_per_file"]):.1f}')
    axes[1, 1].legend()
    
    # 6. Function calls per loop histogram
    axes[1, 2].hist(metrics['function_calls_per_loop'], bins=30, alpha=0.7, color='purple', edgecolor='black')
    axes[1, 2].set_title('Distribution of Function Calls per Loop')
    axes[1, 2].set_xlabel('Number of Function Calls')
    axes[1, 2].set_ylabel('Number of Loops')
    axes[1, 2].axvline(np.mean(metrics['function_calls_per_loop']), color='red', linestyle='--',
                       label=f'Mean: {np.mean(metrics["function_calls_per_loop"]):.1f}')
    axes[1, 2].legend()
    
    plt.tight_layout()
    plt.savefig('energyplus_overview_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_detailed_analysis_charts(metrics, data):
    """Create detailed analysis charts"""
    fig, axes = plt.subplots(2, 2, figsize=(16, 12))
    fig.suptitle('EnergyPlus Detailed Loop Analysis', fontsize=16, fontweight='bold')
    
    # 1. Top 20 most called functions
    top_functions = dict(metrics['top_function_calls'].most_common(20))
    if top_functions:
        y_pos = np.arange(len(top_functions))
        axes[0, 0].barh(y_pos, list(top_functions.values()), color='lightblue')
        axes[0, 0].set_yticks(y_pos)
        axes[0, 0].set_yticklabels(list(top_functions.keys()), fontsize=8)
        axes[0, 0].set_title('Top 20 Most Called Functions')
        axes[0, 0].set_xlabel('Number of Calls')
        axes[0, 0].invert_yaxis()
    
    # 2. Call graph statistics
    if metrics['call_graph_stats']:
        cg_stats = metrics['call_graph_stats']
        categories = ['Total Functions', 'Functions Making Calls', 'Functions Called by Others', 'Functions with Loop Calls']
        values = [cg_stats['total_functions'], cg_stats['functions_with_calls'], 
                 cg_stats['functions_called_by_others'], cg_stats['functions_with_loop_calls']]
        
        bars = axes[0, 1].bar(categories, values, color=['skyblue', 'lightgreen', 'lightcoral', 'gold'])
        axes[0, 1].set_title('Call Graph Statistics')
        axes[0, 1].set_ylabel('Count')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Add value labels on bars
        for bar, value in zip(bars, values):
            axes[0, 1].text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01*max(values),
                            f'{value}', ha='center', va='bottom', fontweight='bold')
    
    # 3. Complexity analysis (functions vs loops scatter)
    file_complexity_data = []
    for file_path, file_data in data['source_files'].items():
        functions = file_data.get('functions', {})
        total_loops = sum(len(func.get('loops', [])) for func in functions.values())
        file_complexity_data.append((len(functions), total_loops))
    
    if file_complexity_data:
        func_counts, loop_counts = zip(*file_complexity_data)
        axes[1, 0].scatter(func_counts, loop_counts, alpha=0.6, color='purple')
        axes[1, 0].set_title('File Complexity: Functions vs Loops')
        axes[1, 0].set_xlabel('Number of Functions')
        axes[1, 0].set_ylabel('Number of Loops')
        axes[1, 0].grid(True, alpha=0.3)
        
        # Add trend line
        if len(func_counts) > 1:
            z = np.polyfit(func_counts, loop_counts, 1)
            p = np.poly1d(z)
            axes[1, 0].plot(func_counts, p(func_counts), "r--", alpha=0.8, label=f'Trend: y={z[0]:.2f}x+{z[1]:.2f}')
            axes[1, 0].legend()
    
    # 4. Summary statistics table
    axes[1, 1].axis('off')
    summary_stats = [
        ['Total Files Analyzed', f"{metrics['total_files']:,}"],
        ['Files with Loops', f"{metrics['files_with_loops']:,} ({100*metrics['files_with_loops']/metrics['total_files']:.1f}%)"],
        ['Total Functions', f"{metrics['total_functions']:,}"],
        ['Total Loops Found', f"{metrics['total_loops']:,}"],
        ['Total Function Calls', f"{metrics['total_function_calls']:,}"],
        ['Avg Functions/File', f"{np.mean(metrics['functions_per_file']):.1f}"],
        ['Avg Loops/File', f"{np.mean(metrics['loops_per_file']):.1f}"],
        ['Avg Calls/Loop', f"{np.mean(metrics['function_calls_per_loop']):.1f}"],
        ['Analysis Duration', f"{data['metadata']['analysis_duration_seconds']:.2f}s"],
    ]
    
    table = axes[1, 1].table(cellText=summary_stats, cellLoc='left', loc='center',
                            colWidths=[0.6, 0.4])
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 2)
    axes[1, 1].set_title('Analysis Summary Statistics', pad=20)
    
    plt.tight_layout()
    plt.savefig('energyplus_detailed_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_top_files_analysis(data, top_n=15):
    """Create analysis of top files by various metrics"""
    file_metrics = []
    
    for file_path, file_data in data['source_files'].items():
        functions = file_data.get('functions', {})
        total_loops = sum(len(func.get('loops', [])) for func in functions.values())
        total_function_calls = 0
        
        for func_data in functions.values():
            for loop_data in func_data.get('loops', []):
                operations = loop_data.get('operations', {})
                total_function_calls += len(operations.get('function_calls', []))
        
        file_name = Path(file_path).name
        file_metrics.append({
            'file': file_name,
            'functions': len(functions),
            'loops': total_loops,
            'function_calls': total_function_calls,
            'complexity': len(functions) * total_loops if total_loops > 0 else 0
        })
    
    # Sort by different metrics
    top_by_loops = sorted(file_metrics, key=lambda x: x['loops'], reverse=True)[:top_n]
    top_by_functions = sorted(file_metrics, key=lambda x: x['functions'], reverse=True)[:top_n]
    top_by_calls = sorted(file_metrics, key=lambda x: x['function_calls'], reverse=True)[:top_n]
    
    fig, axes = plt.subplots(2, 2, figsize=(20, 12))
    fig.suptitle(f'Top {top_n} Files Analysis', fontsize=16, fontweight='bold')
    
    # Top files by loop count
    files = [item['file'][:30] + '...' if len(item['file']) > 30 else item['file'] for item in top_by_loops]
    loops = [item['loops'] for item in top_by_loops]
    
    y_pos = np.arange(len(files))
    bars1 = axes[0, 0].barh(y_pos, loops, color='lightcoral')
    axes[0, 0].set_yticks(y_pos)
    axes[0, 0].set_yticklabels(files, fontsize=8)
    axes[0, 0].set_title(f'Top {top_n} Files by Loop Count')
    axes[0, 0].set_xlabel('Number of Loops')
    axes[0, 0].invert_yaxis()
    
    # Add value labels
    for i, (bar, value) in enumerate(zip(bars1, loops)):
        axes[0, 0].text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                       f'{value}', va='center', fontsize=8, fontweight='bold')
    
    # Top files by function count
    files = [item['file'][:30] + '...' if len(item['file']) > 30 else item['file'] for item in top_by_functions]
    functions = [item['functions'] for item in top_by_functions]
    
    y_pos = np.arange(len(files))
    bars2 = axes[0, 1].barh(y_pos, functions, color='lightblue')
    axes[0, 1].set_yticks(y_pos)
    axes[0, 1].set_yticklabels(files, fontsize=8)
    axes[0, 1].set_title(f'Top {top_n} Files by Function Count')
    axes[0, 1].set_xlabel('Number of Functions')
    axes[0, 1].invert_yaxis()
    
    # Add value labels
    for i, (bar, value) in enumerate(zip(bars2, functions)):
        axes[0, 1].text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                       f'{value}', va='center', fontsize=8, fontweight='bold')
    
    # Top files by function calls
    files = [item['file'][:30] + '...' if len(item['file']) > 30 else item['file'] for item in top_by_calls]
    calls = [item['function_calls'] for item in top_by_calls]
    
    y_pos = np.arange(len(files))
    bars3 = axes[1, 0].barh(y_pos, calls, color='lightgreen')
    axes[1, 0].set_yticks(y_pos)
    axes[1, 0].set_yticklabels(files, fontsize=8)
    axes[1, 0].set_title(f'Top {top_n} Files by Function Calls in Loops')
    axes[1, 0].set_xlabel('Number of Function Calls')
    axes[1, 0].invert_yaxis()
    
    # Add value labels
    for i, (bar, value) in enumerate(zip(bars3, calls)):
        axes[1, 0].text(bar.get_width() + 0.1, bar.get_y() + bar.get_height()/2,
                       f'{value}', va='center', fontsize=8, fontweight='bold')
    
    # Correlation heatmap
    df = pd.DataFrame(file_metrics)
    correlation_matrix = df[['functions', 'loops', 'function_calls', 'complexity']].corr()
    
    im = axes[1, 1].imshow(correlation_matrix, cmap='coolwarm', aspect='auto', vmin=-1, vmax=1)
    axes[1, 1].set_xticks(range(len(correlation_matrix.columns)))
    axes[1, 1].set_yticks(range(len(correlation_matrix.columns)))
    axes[1, 1].set_xticklabels(correlation_matrix.columns)
    axes[1, 1].set_yticklabels(correlation_matrix.columns)
    axes[1, 1].set_title('Correlation Matrix: File Metrics')
    
    # Add correlation values to heatmap
    for i in range(len(correlation_matrix.columns)):
        for j in range(len(correlation_matrix.columns)):
            text = axes[1, 1].text(j, i, f'{correlation_matrix.iloc[i, j]:.2f}',
                                 ha="center", va="center", color="black", fontweight='bold')
    
    # Add colorbar
    plt.colorbar(im, ax=axes[1, 1], orientation='vertical', fraction=0.046, pad=0.04)
    
    plt.tight_layout()
    plt.savefig('energyplus_top_files_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def create_function_call_network_analysis(data, top_n=20):
    """Create function call network analysis"""
    if 'call_graph' not in data:
        print("No call graph data available")
        return
    
    call_graph = data['call_graph']
    
    # Find most connected functions
    function_connections = {}
    for func_name, func_data in call_graph.items():
        calls_out = len(func_data.get('calls', []))
        calls_in = len(func_data.get('called_by', []))
        loop_calls = len(func_data.get('calls_in_loops', []))
        
        function_connections[func_name] = {
            'calls_out': calls_out,
            'calls_in': calls_in,
            'loop_calls': loop_calls,
            'total_connections': calls_out + calls_in
        }
    
    # Top functions by different connection metrics
    top_by_total = sorted(function_connections.items(), 
                         key=lambda x: x[1]['total_connections'], reverse=True)[:top_n]
    top_by_calls_out = sorted(function_connections.items(), 
                             key=lambda x: x[1]['calls_out'], reverse=True)[:top_n]
    top_by_loop_calls = sorted(function_connections.items(), 
                              key=lambda x: x[1]['loop_calls'], reverse=True)[:top_n]
    
    fig, axes = plt.subplots(2, 2, figsize=(20, 12))
    fig.suptitle('Function Call Network Analysis', fontsize=16, fontweight='bold')
    
    # Most connected functions (total)
    func_names = [item[0][:25] + '...' if len(item[0]) > 25 else item[0] for item in top_by_total]
    connections = [item[1]['total_connections'] for item in top_by_total]
    
    y_pos = np.arange(len(func_names))
    axes[0, 0].barh(y_pos, connections, color='gold')
    axes[0, 0].set_yticks(y_pos)
    axes[0, 0].set_yticklabels(func_names, fontsize=8)
    axes[0, 0].set_title(f'Top {top_n} Most Connected Functions')
    axes[0, 0].set_xlabel('Total Connections (In + Out)')
    axes[0, 0].invert_yaxis()
    
    # Functions making most calls
    func_names = [item[0][:25] + '...' if len(item[0]) > 25 else item[0] for item in top_by_calls_out]
    calls_out = [item[1]['calls_out'] for item in top_by_calls_out]
    
    y_pos = np.arange(len(func_names))
    axes[0, 1].barh(y_pos, calls_out, color='lightblue')
    axes[0, 1].set_yticks(y_pos)
    axes[0, 1].set_yticklabels(func_names, fontsize=8)
    axes[0, 1].set_title(f'Top {top_n} Functions Making Most Calls')
    axes[0, 1].set_xlabel('Calls Made')
    axes[0, 1].invert_yaxis()
    
    # Functions with most loop calls
    func_names = [item[0][:25] + '...' if len(item[0]) > 25 else item[0] for item in top_by_loop_calls]
    loop_calls = [item[1]['loop_calls'] for item in top_by_loop_calls]
    
    y_pos = np.arange(len(func_names))
    axes[1, 0].barh(y_pos, loop_calls, color='lightcoral')
    axes[1, 0].set_yticks(y_pos)
    axes[1, 0].set_yticklabels(func_names, fontsize=8)
    axes[1, 0].set_title(f'Top {top_n} Functions with Most Loop Calls')
    axes[1, 0].set_xlabel('Calls in Loops')
    axes[1, 0].invert_yaxis()
    
    # Connection distribution
    total_connections = [item['total_connections'] for item in function_connections.values()]
    calls_out = [item['calls_out'] for item in function_connections.values()]
    calls_in = [item['calls_in'] for item in function_connections.values()]
    
    axes[1, 1].hist([total_connections, calls_out, calls_in], bins=30, alpha=0.7, 
                   label=['Total Connections', 'Outgoing Calls', 'Incoming Calls'],
                   color=['gold', 'lightblue', 'lightgreen'])
    axes[1, 1].set_title('Distribution of Function Connections')
    axes[1, 1].set_xlabel('Number of Connections')
    axes[1, 1].set_ylabel('Number of Functions')
    axes[1, 1].legend()
    axes[1, 1].set_yscale('log')
    
    plt.tight_layout()
    plt.savefig('energyplus_function_network_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()

def main():
    """Main function to generate all visualizations"""
    json_file = 'energyplus.json'
    
    try:
        # Load data
        data = load_data(json_file)
        
        # Extract metrics
        print("\nExtracting metrics...")
        metrics = extract_metrics(data)
        
        # Create visualizations
        print("\nCreating overview charts...")
        create_overview_charts(metrics, data)
        
        print("Creating detailed analysis charts...")
        create_detailed_analysis_charts(metrics, data)
        
        print("Creating top files analysis...")
        create_top_files_analysis(data)
        
        print("Creating function call network analysis...")
        create_function_call_network_analysis(data)
        
        print("\nAll visualizations completed!")
        print("Generated files:")
        print("- energyplus_overview_analysis.png")
        print("- energyplus_detailed_analysis.png") 
        print("- energyplus_top_files_analysis.png")
        print("- energyplus_function_network_analysis.png")
        
    except FileNotFoundError:
        print(f"Error: Could not find {json_file}")
        print("Please ensure the EnergyPlus analysis JSON file exists in the current directory.")
    except Exception as e:
        print(f"Error creating visualizations: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()