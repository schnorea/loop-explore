# Loop Extractor Implementation Plan

## Overview

This document outlines the implementation plan and data structure design for the Loop Extractor tool, a Python-based utility that uses Clang AST to analyze C/C++ codebases and extract comprehensive loop information for High-Performance Computing (HPC) optimization.

## Implementation Plan

### Phase 1: Core Infrastructure

#### 1.1 Project Setup
- **Environment Setup**
  - Set up Python environment with required dependencies (libclang, clang AST bindings)
  - Create modular project structure for extensibility
  - Implement configuration management for different C/C++ standards and compiler flags
  - Set up logging and error handling framework

- **Dependencies**
  ```
  libclang-py3
  clang
  json
  pathlib
  argparse
  logging
  ```

#### 1.2 File Discovery Engine
- **Directory Traversal**
  - Implement recursive directory traversal
  - Filter for C/C++ source files (.c, .cpp, .cc, .cxx, .h, .hpp)
  - Handle symbolic links and permission issues
  - Support for inclusion/exclusion patterns
  - Basic compiler flag handling (standard includes and defines)

#### 1.3 Clang AST Parser Integration
- **AST Framework**
  - Set up libclang bindings and initialization
  - Implement AST traversal framework using visitor pattern
  - Create base classes for different AST node types
  - Handle parsing errors and incomplete translations

- **Core Components**
  ```
  ASTParser: Main parsing interface
  NodeVisitor: Base visitor class
  LoopVisitor: Specialized for loop detection
  FunctionVisitor: Function and method analysis
  CallGraphBuilder: Function call relationship tracking
  ```

### Phase 2: Loop Detection and Analysis

#### 2.1 Individual Loop Structure Detection
- **Loop Type Recognition**
  - Identify for loops (CXXForStmt, ForStmt)
  - Identify while loops (WhileStmt)
  - Identify do-while loops (DoStmt)
  - Handle range-based for loops (CXXForRangeStmt)

- **Loop Bounds Extraction**
  - Parse initialization expressions
  - Extract loop conditions and termination criteria
  - Identify increment/decrement operations
  - Estimate iteration counts where possible
  - In the case of dynamic loop counts, create a parameter based equation that could be used to calculate loop count.

- **Source Location Mapping**
  - Capture precise file paths and line numbers
  - Map loops to containing functions/methods/classes
  - (Place this in backlog) Handle macro expansions and template instantiations

#### 2.2 Loop Nesting Analysis
- **Hierarchical Structure**
  - Build nested loop trees with depth tracking
  - Identify parent-child relationships between loops
  - Handle complex nesting scenarios (irregular patterns)

- **Function Call Integration**
  - Track function calls within loop bodies
  - Build call graph relationships 
  - Identify recursive calls and indirect calls
  - Map function definitions to their locations

#### 2.3 Loop Content Analysis
- **Operation Classification**
  - Arithmetic operations (add, subtract, multiply, divide)
  - Logical operations (AND, OR, NOT, comparisons)
  - Bitwise operations
  - Assignment operations
  - Function calls and method invocations

- **Memory Access Pattern Detection**
  - Array indexing patterns (1D, 2D, multi-dimensional)
  - Pointer arithmetic and dereferencing
  - Structure and class member access
  - Stride pattern analysis (sequential, strided, random)
  - Read/write classification

- **Data Flow Analysis**
  - Variable usage tracking within loops
  - Loop-carried dependencies identification
  - Memory aliasing detection
  - Constant propagation within loops

### Phase 3: Data Model and Storage

#### 3.1 JSON Schema Design
- **Extensible Architecture**
  - Versioned schema for backward compatibility
  - Extension points for future analysis
  - Modular data organization
  - Validation schema definition

#### 3.2 Data Serialization
- **Output Generation**
  - Pretty-printed JSON with consistent formatting
  - Incremental analysis support
  - Data integrity validation
  - Error reporting and debugging information

## JSON Output Structure

### Top-Level Schema

```json
{
  "metadata": {
    "version": "1.0.0",
    "generated_at": "2025-10-04T10:30:00Z",
    "tool_version": "1.0.0",
    "scan_path": "/path/to/source/code",
    "compiler_flags": ["-std=c++17", "-I/usr/include"],
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
    },
    "functions_with_loops": 67
  },
  "source_files": { /* File-based organization */ },
  "call_graph": { /* Function relationship mapping */ },
  "extensions": { /* Future analysis data */ }
}
```

### File Structure Organization

Each source file is organized hierarchically:

```
source_files/
├── {file_path}/
│   ├── file_info: metadata about the file
│   ├── classes/
│   │   └── {class_name}/
│   │       ├── location: source location info
│   │       └── methods/
│   │           └── {method_name}/
│   │               ├── location, parameters, return_type
│   │               └── loops: array of loop objects
│   └── functions/
│       └── {function_name}/
│           ├── location, parameters, return_type
│           └── loops: array of loop objects
```

### Loop Object Structure

Each loop contains comprehensive analysis data:

```json
{
  "loop_id": "unique_identifier",
  "type": "for_loop|while_loop|do_while_loop",
  "location": {
    "start_line": 28,
    "end_line": 42,
    "start_column": 8,
    "end_column": 9
  },
  "loop_bounds": {
    "initialization": "int i = 0",
    "condition": "i < rows",
    "increment": "++i",
    "estimated_iterations": "dynamic|constant|unknown"
  },
  "nesting_level": 1,
  "nested_loops": [ /* Array of nested loop objects */ ],
  "operations": {
    "arithmetic": [ /* Arithmetic operations */ ],
    "assignments": [ /* Assignment operations */ ],
    "function_calls": [ /* Function call operations */ ]
  },
  "memory_access": {
    "reads": [ /* Memory read operations */ ],
    "writes": [ /* Memory write operations */ ]
  },
  "function_calls": [ /* Detailed function call info */ ],
  "extensions": { /* Future analysis data */ }
}
```

### Memory Access Pattern Structure

```json
{
  "variable": "data",
  "access_pattern": "data[i][k]",
  "access_type": "1d_array|2d_array|pointer|struct_member",
  "stride_pattern": "sequential|row_major|column_major|strided|random",
  "line": 32,
  "dependencies": [ /* Array of dependent variables */ ]
}
```

## Complete Example

### Matrix Multiplication Example

```json
{
  "metadata": {
    "version": "1.0.0",
    "generated_at": "2025-10-04T10:30:00Z",
    "tool_version": "1.0.0",
    "scan_path": "/path/to/source/code",
    "compiler_flags": ["-std=c++17", "-I/usr/include"],
    "total_files_scanned": 1,
    "total_loops_found": 4
  },
  "analysis_summary": {
    "loop_types": {
      "for_loops": 4,
      "while_loops": 0,
      "do_while_loops": 0
    },
    "nesting_levels": {
      "max_depth": 3,
      "average_depth": 2.0
    },
    "functions_with_loops": 2
  },
  "source_files": {
    "/path/to/source/main.cpp": {
      "file_info": {
        "size_bytes": 2048,
        "last_modified": "2025-10-01T15:20:00Z",
        "includes": ["<iostream>", "<vector>", "\"utils.h\""],
        "total_loops": 4
      },
      "classes": {
        "Matrix": {
          "location": {
            "start_line": 10,
            "end_line": 50
          },
          "methods": {
            "multiply": {
              "location": {
                "start_line": 25,
                "end_line": 45
              },
              "parameters": ["const Matrix& other"],
              "return_type": "Matrix",
              "loops": [
                {
                  "loop_id": "loop_001",
                  "type": "for_loop",
                  "location": {
                    "start_line": 28,
                    "end_line": 42,
                    "start_column": 8,
                    "end_column": 9
                  },
                  "loop_bounds": {
                    "initialization": "int i = 0",
                    "condition": "i < rows",
                    "increment": "++i",
                    "estimated_iterations": "dynamic"
                  },
                  "nesting_level": 1,
                  "nested_loops": [
                    {
                      "loop_id": "loop_002",
                      "type": "for_loop",
                      "location": {
                        "start_line": 29,
                        "end_line": 41,
                        "start_column": 12,
                        "end_column": 13
                      },
                      "loop_bounds": {
                        "initialization": "int j = 0",
                        "condition": "j < cols",
                        "increment": "++j",
                        "estimated_iterations": "dynamic"
                      },
                      "nesting_level": 2,
                      "nested_loops": [
                        {
                          "loop_id": "loop_003",
                          "type": "for_loop",
                          "location": {
                            "start_line": 31,
                            "end_line": 39,
                            "start_column": 16,
                            "end_column": 17
                          },
                          "loop_bounds": {
                            "initialization": "int k = 0",
                            "condition": "k < other.cols",
                            "increment": "++k",
                            "estimated_iterations": "dynamic"
                          },
                          "nesting_level": 3,
                          "nested_loops": [],
                          "operations": {
                            "arithmetic": [
                              {
                                "type": "multiplication",
                                "operands": ["data[i][k]", "other.data[k][j]"],
                                "line": 32
                              },
                              {
                                "type": "addition",
                                "operands": ["result[i][j]", "temp"],
                                "line": 33
                              }
                            ],
                            "assignments": [
                              {
                                "target": "result[i][j]",
                                "source": "result[i][j] + data[i][k] * other.data[k][j]",
                                "line": 33
                              }
                            ]
                          },
                          "memory_access": {
                            "reads": [
                              {
                                "variable": "data",
                                "access_pattern": "data[i][k]",
                                "access_type": "2d_array",
                                "stride_pattern": "row_major",
                                "line": 32
                              },
                              {
                                "variable": "other.data",
                                "access_pattern": "other.data[k][j]",
                                "access_type": "2d_array",
                                "stride_pattern": "column_major",
                                "line": 32
                              }
                            ],
                            "writes": [
                              {
                                "variable": "result",
                                "access_pattern": "result[i][j]",
                                "access_type": "2d_array",
                                "stride_pattern": "row_major",
                                "line": 33
                              }
                            ]
                          },
                          "function_calls": [],
                          "extensions": {
                            "parallelization_potential": {
                              "vectorizable": true,
                              "parallelizable": true,
                              "dependencies": ["loop_carried_dependency"]
                            }
                          }
                        }
                      ],
                      "operations": {
                        "assignments": [
                          {
                            "target": "result[i][j]",
                            "source": "0",
                            "line": 30
                          }
                        ]
                      },
                      "memory_access": {
                        "writes": [
                          {
                            "variable": "result",
                            "access_pattern": "result[i][j]",
                            "access_type": "2d_array",
                            "stride_pattern": "row_major",
                            "line": 30
                          }
                        ]
                      },
                      "function_calls": []
                    }
                  ],
                  "operations": {},
                  "memory_access": {},
                  "function_calls": []
                }
              ]
            }
          }
        }
      },
      "functions": {
        "main": {
          "location": {
            "start_line": 55,
            "end_line": 75
          },
          "parameters": ["int argc", "char* argv[]"],
          "return_type": "int",
          "loops": [
            {
              "loop_id": "loop_004",
              "type": "for_loop",
              "location": {
                "start_line": 60,
                "end_line": 65,
                "start_column": 4,
                "end_column": 5
              },
              "loop_bounds": {
                "initialization": "int i = 1",
                "condition": "i < argc",
                "increment": "++i",
                "estimated_iterations": "argc-1"
              },
              "nesting_level": 1,
              "nested_loops": [],
              "operations": {
                "function_calls": [
                  {
                    "function": "std::cout.operator<<",
                    "arguments": ["argv[i]"],
                    "line": 61
                  }
                ]
              },
              "memory_access": {
                "reads": [
                  {
                    "variable": "argv",
                    "access_pattern": "argv[i]",
                    "access_type": "1d_array",
                    "stride_pattern": "sequential",
                    "line": 61
                  }
                ]
              },
              "function_calls": [
                {
                  "function": "std::cout.operator<<",
                  "location": {
                    "line": 61,
                    "column": 8
                  },
                  "resolved": true,
                  "definition_file": "<iostream>"
                }
              ]
            }
          ]
        }
      }
    }
  },
  "call_graph": {
    "Matrix::multiply": {
      "calls": [],
      "called_by": ["main"],
      "calls_in_loops": []
    },
    "main": {
      "calls": ["Matrix::multiply", "std::cout.operator<<"],
      "called_by": [],
      "calls_in_loops": ["std::cout.operator<<"]
    }
  },
  "extensions": {
    "future_analysis": {
      "placeholder": "Reserved for future analysis data"
    }
  }
}
```

## Key Design Features

### 1. Extensible Architecture
- **Extension Points**: The `extensions` field at multiple levels allows for future analysis without breaking existing parsers
- **Versioned Schema**: Metadata includes version information for backward compatibility
- **Modular Organization**: Clear separation between different types of analysis data

### 2. Hierarchical Organization
- **File-Based Structure**: Top-level organization by source files maintains project structure
- **Code Organization Respect**: Classes, methods, and functions are properly nested
- **Scope Awareness**: Loops are associated with their containing scope (function/method)

### 3. Comprehensive Loop Information
- **Precise Location**: Line and column numbers for accurate source mapping
- **Loop Characteristics**: Type, bounds, nesting level, and iteration estimates
- **Content Analysis**: Operations, memory access patterns, and function calls
- **Nesting Relationships**: Parent-child relationships between nested loops

### 4. Memory Access Analysis
- **Pattern Recognition**: Sequential, strided, row-major, column-major access patterns
- **Read/Write Classification**: Separate tracking of memory reads and writes
- **Variable Dependencies**: Identification of data dependencies within loops

### 5. Call Graph Integration
- **Function Relationships**: Tracks which functions call which other functions
- **Loop Context**: Identifies function calls that occur within loop contexts
- **Cross-Reference Support**: Enables analysis of function calls across file boundaries

### 6. Future-Proof Design
- **Reserved Sections**: Extension fields for future analysis capabilities
- **Incremental Analysis**: Structure supports adding new analysis types without modification
- **Tool Integration**: Format designed to support downstream HPC optimization tools

## Implementation Priorities

1. **Phase 1**: Core infrastructure and basic loop detection
2. **Phase 2**: Advanced analysis (nesting, memory patterns, operations)
3. **Phase 3**: Output generation and validation
4. **Future**: Analysis tools and optimization recommendations

## Backlog (Future Enhancements)

### Build System Integration
- **Advanced Compiler Configuration**
  - Parse compile_commands.json for compiler flags
  - Support for CMake, Make, and other build systems
  - Handle different compiler configurations
  - Integration with popular C/C++ build systems
  - Automatic detection of project build configuration

### Advanced AST Features
- **Template and Macro Handling**
  - Handle macro expansions and template instantiations
  - Template specialization analysis
  - Macro-generated loop detection

### Enhanced Analysis
- **Cross-File Analysis**
  - Inter-procedural analysis across compilation units
  - Global call graph construction
  - Cross-module dependency tracking

This design provides a solid foundation for HPC loop analysis while maintaining flexibility for future enhancements and specialized analysis requirements.