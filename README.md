# Loop Extractor

A Python-based utility that uses Clang AST to analyze C/C++ codebases and extract comprehensive loop information for High-Performance Computing (HPC) optimization.

## Overview

Loop Extractor analyzes C/C++ source code to identify and extract detailed information about loops, including:
- Individual loop structure and location
- Loop nesting relationships
- Operations within loops
- Memory access patterns
- Function calls within loops

## Features

- **Comprehensive Loop Analysis**: Detects for, while, do-while, and range-based for loops
- **Hierarchical Organization**: Organizes results by file → class/function → loop structure
- **Memory Access Pattern Detection**: Identifies array access patterns and stride information
- **Call Graph Generation**: Tracks function relationships and calls within loops
- **Extensible JSON Output**: Future-proof format for additional analysis capabilities

## Requirements

- Python 3.7+
- libclang (LLVM/Clang library)
- C/C++ source code to analyze

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Ensure libclang is available on your system:
   - **Ubuntu/Debian**: `sudo apt-get install libclang-dev`
   - **macOS**: `brew install llvm`
   - **macOS (ARM)**: `brew install llvm` (Homebrew will install ARM version)

## Usage

### Basic Usage

```bash
python loop_extractor.py /path/to/source/code
```

### Advanced Usage

```bash
python loop_extractor.py /path/to/source/code \
    --output analysis_results.json \
    --cpp-standard c++17 \
    --include "src/*" \
    --exclude "test/*" \
    --log-level DEBUG \
    --checkpoint-frequency 25
```

### Command Line Options

- `path`: Path to the source code directory to analyze (required)
- `-o, --output`: Output JSON file path (default: loop_analysis.json)
- `--include`: Include pattern for files (can be specified multiple times)
- `--exclude`: Exclude pattern for files (can be specified multiple times)
- `--cpp-standard`: C++ standard to use (c++11, c++14, c++17, c++20)
- `--log-level`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `--verbose`: Enable verbose output
- `--checkpoint-frequency`: Save checkpoint every N files (default: 50)
- `--resume-from-checkpoint`: Resume analysis from a checkpoint file

## Example

Analyze the test code:

```bash
python loop_extractor.py test_code --output test_results.json --verbose
```

This will analyze the C/C++ files in the `test_code` directory and generate a detailed JSON report.

### Large Codebase Analysis

For large codebases, use progress tracking and checkpointing:

```bash
# Analyze with progress tracking and frequent checkpoints
python loop_extractor.py /large/codebase/path \
    --output large_analysis.json \
    --checkpoint-frequency 25 \
    --verbose

# If interrupted, resume from checkpoint
python loop_extractor.py /large/codebase/path \
    --output large_analysis.json \
    --resume-from-checkpoint large_analysis.checkpoint.json
```

**Features for Large Codebases:**
- **Progress Tracking**: Shows files processed/total with percentage and ETA
- **Automatic Checkpointing**: Saves progress every N files (configurable)
- **Interrupt Recovery**: Ctrl+C saves current progress to checkpoint and generates partial results
- **Resume Capability**: Continue from where you left off using checkpoint files

## Output Format

The tool generates a comprehensive JSON file with the following structure:

```json
{
  "metadata": {
    "version": "1.0.0",
    "generated_at": "2025-10-04T10:30:00Z",
    "tool_version": "1.0.0",
    "scan_path": "/path/to/source",
    "total_files_scanned": 42,
    "total_loops_found": 156
  },
  "analysis_summary": {
    "loop_types": {
      "for_loops": 98,
      "while_loops": 45,
      "do_while_loops": 13
    },
    "nesting_levels": {
      "max_depth": 4,
      "average_depth": 1.8
    }
  },
  "source_files": {
    "/path/to/file.cpp": {
      "file_info": { /* File metadata */ },
      "classes": { /* Class and method analysis */ },
      "functions": { /* Function analysis */ }
    }
  },
  "call_graph": { /* Function relationship mapping */ },
  "extensions": { /* Reserved for future analysis */ }
}
```

### Loop Information

Each loop contains detailed information:

- **Location**: Precise line and column numbers
- **Loop Bounds**: Initialization, condition, and increment expressions
- **Nesting Level**: Depth of loop nesting
- **Operations**: Arithmetic, logical, and assignment operations
- **Memory Access**: Read/write patterns with stride analysis
- **Function Calls**: Called functions within the loop body
- **Nested Loops**: Hierarchical structure of nested loops

## Project Structure

```
loop_extractor/
├── loop_extractor.py          # Main entry point
├── requirements.txt           # Python dependencies
├── src/                      # Source code modules
│   ├── __init__.py
│   ├── config.py             # Configuration management
│   ├── file_discovery.py     # File discovery engine
│   ├── ast_parser.py         # Clang AST parser
│   ├── loop_analyzer.py      # Loop analysis engine
│   └── json_output.py        # JSON output generation
├── test_code/                # Sample C/C++ code for testing
│   ├── matrix.cpp            # Matrix multiplication example
│   └── sorting.c             # Sorting algorithms example
├── REQUIREMENTS.md           # Project requirements document
└── IMPLEMENTATION_PLAN.md    # Detailed implementation plan
```

## Development

### Architecture

The tool is designed with a modular architecture:

1. **Configuration Management** (`config.py`): Handles tool configuration and compiler flags
2. **File Discovery** (`file_discovery.py`): Discovers C/C++ source files recursively
3. **AST Parser** (`ast_parser.py`): Interfaces with libclang for AST parsing
4. **Loop Analyzer** (`loop_analyzer.py`): Extracts and analyzes loop information
5. **JSON Output** (`json_output.py`): Generates structured output format

### Extending the Tool

The tool is designed to be extensible. To add new analysis capabilities:

1. Extend the loop analysis in `loop_analyzer.py`
2. Add new data fields to the JSON structure
3. Use the `extensions` field in the output for new analysis data
4. Update the configuration as needed

## Troubleshooting

### Common Issues

1. **libclang not found**: Ensure libclang is installed and the library path is correct
2. **Parse errors**: Check that the C/C++ code compiles with the specified standard
3. **Permission errors**: Ensure read access to all source directories
4. **Memory issues**: For large codebases, consider analyzing in smaller chunks

### Debug Mode

Use `--log-level DEBUG` or `--verbose` for detailed logging:

```bash
python loop_extractor.py test_code --log-level DEBUG
```

## Contributing

This tool was designed for HPC optimization analysis. Contributions are welcome for:

- Additional loop analysis capabilities
- Enhanced memory access pattern detection
- Improved call graph analysis
- Performance optimizations
- Better error handling

## License

MIT

## Future Enhancements

See `IMPLEMENTATION_PLAN.md` for planned future enhancements including:
- Build system integration (compile_commands.json)
- Template and macro handling
- Cross-file analysis capabilities
- Advanced parallelization analysis