"""
Loop analysis module for extracting loop information from AST.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

try:
    from clang.cindex import TranslationUnit, CursorKind, Cursor, TypeKind
except ImportError as e:
    raise ImportError("libclang not found. Please install with: pip install libclang") from e

from .config import Config
from .ast_parser import ASTParser


class LoopAnalyzer:
    """Analyzes AST to extract comprehensive loop information."""
    
    def __init__(self, config: Config):
        """Initialize loop analyzer with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.ast_parser = ASTParser(config)
        
        # Loop types mapping
        self.LOOP_TYPES = {
            CursorKind.FOR_STMT: 'for_loop',
            CursorKind.WHILE_STMT: 'while_loop',
            CursorKind.DO_STMT: 'do_while_loop',
            CursorKind.CXX_FOR_RANGE_STMT: 'range_for_loop',
        }
        
        # Operation types for classification
        self.ARITHMETIC_OPS = {
            '+', '-', '*', '/', '%', '++', '--', '+=', '-=', '*=', '/=', '%='
        }
        
        self.LOGICAL_OPS = {
            '&&', '||', '!', '==', '!=', '<', '>', '<=', '>='
        }
        
        self.BITWISE_OPS = {
            '&', '|', '^', '~', '<<', '>>', '&=', '|=', '^=', '<<=', '>>='
        }
    
    def analyze_file(self, translation_unit: TranslationUnit, file_path: Path) -> Dict[str, Any]:
        """Analyze a translation unit for loop information."""
        self.logger.debug(f"Analyzing loops in {file_path}")
        
        file_analysis = {
            'file_info': self._get_file_info(file_path),
            'classes': {},
            'functions': {},
            'global_loops': [],  # Loops not in functions (rare but possible)
        }
        
        try:
            # Get the root cursor
            root_cursor = translation_unit.cursor
            
            # Analyze the file structure
            self._analyze_cursor(root_cursor, file_analysis, file_path)
            
        except Exception as e:
            self.logger.error(f"Error analyzing {file_path}: {e}")
        
        return file_analysis
    
    def _get_file_info(self, file_path: Path) -> Dict[str, Any]:
        """Get basic file information."""
        try:
            stat = file_path.stat()
            
            # Try to detect includes by reading the first few lines
            includes = []
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    for line_num, line in enumerate(f, 1):
                        if line_num > 100:  # Don't read entire file
                            break
                        line = line.strip()
                        if line.startswith('#include'):
                            includes.append(line)
            except:
                pass
            
            return {
                'size_bytes': stat.st_size,
                'last_modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                'includes': includes,
                'total_loops': 0,  # Will be updated later
            }
        except Exception as e:
            self.logger.warning(f"Could not get file info for {file_path}: {e}")
            return {
                'size_bytes': 0,
                'last_modified': datetime.now().isoformat(),
                'includes': [],
                'total_loops': 0,
            }
    
    def _analyze_cursor(self, cursor: Cursor, file_analysis: Dict[str, Any], 
                       target_file: Path, parent_context: Optional[Dict] = None) -> None:
        """Recursively analyze cursor and its children."""
        try:
            # Only analyze cursors in the target file
            if not self.ast_parser.is_in_file(cursor, target_file):
                # Allow cursors without location (like translation unit root)
                if cursor.location.file is not None:
                    return
            
            cursor_kind = cursor.kind
            self.logger.debug(f"Analyzing cursor: {cursor_kind} - {cursor.spelling}")
            
            # Handle different cursor types
            if cursor_kind == CursorKind.CLASS_DECL:
                self._analyze_class(cursor, file_analysis, target_file)
            elif cursor_kind == CursorKind.FUNCTION_DECL:
                self._analyze_function(cursor, file_analysis, target_file)
            elif cursor_kind == CursorKind.CXX_METHOD:
                # Method will be handled by class analysis
                if parent_context and parent_context.get('type') == 'class':
                    self._analyze_method(cursor, parent_context, target_file)
            elif cursor_kind in self.LOOP_TYPES:
                self._analyze_loop(cursor, file_analysis, target_file, parent_context)
            
            # Recursively analyze children
            for child in cursor.get_children():
                child_context = parent_context
                if cursor_kind == CursorKind.CLASS_DECL:
                    child_context = {'type': 'class', 'name': cursor.spelling, 'data': file_analysis['classes'].get(cursor.spelling, {})}
                elif cursor_kind in {CursorKind.FUNCTION_DECL, CursorKind.CXX_METHOD}:
                    child_context = {'type': 'function', 'name': cursor.spelling}
                
                self._analyze_cursor(child, file_analysis, target_file, child_context)
                
        except Exception as e:
            self.logger.debug(f"Error analyzing cursor {cursor.kind}: {e}")
    
    def _analyze_class(self, cursor: Cursor, file_analysis: Dict[str, Any], target_file: Path) -> None:
        """Analyze a class declaration."""
        class_name = cursor.spelling or f"anonymous_class_{cursor.location.line}"
        
        location = self.ast_parser.get_cursor_location(cursor)
        
        file_analysis['classes'][class_name] = {
            'location': {
                'start_line': location['start_line'],
                'end_line': location['end_line'],
            },
            'methods': {},
        }
        
        self.logger.debug(f"Found class: {class_name}")
    
    def _analyze_function(self, cursor: Cursor, file_analysis: Dict[str, Any], target_file: Path) -> None:
        """Analyze a function declaration."""
        function_name = cursor.spelling or f"anonymous_function_{cursor.location.line}"
        
        location = self.ast_parser.get_cursor_location(cursor)
        
        # Extract parameters
        parameters = []
        return_type = cursor.result_type.spelling if cursor.result_type else "void"
        
        for child in cursor.get_children():
            if child.kind == CursorKind.PARM_DECL:
                param_type = child.type.spelling if child.type else "unknown"
                param_name = child.spelling or ""
                parameters.append(f"{param_type} {param_name}".strip())
        
        file_analysis['functions'][function_name] = {
            'location': {
                'start_line': location['start_line'],
                'end_line': location['end_line'],
            },
            'parameters': parameters,
            'return_type': return_type,
            'loops': [],
        }
        
        self.logger.debug(f"Found function: {function_name}")
    
    def _analyze_method(self, cursor: Cursor, class_context: Dict, target_file: Path) -> None:
        """Analyze a method within a class."""
        method_name = cursor.spelling or f"anonymous_method_{cursor.location.line}"
        
        location = self.ast_parser.get_cursor_location(cursor)
        
        # Extract parameters
        parameters = []
        return_type = cursor.result_type.spelling if cursor.result_type else "void"
        
        for child in cursor.get_children():
            if child.kind == CursorKind.PARM_DECL:
                param_type = child.type.spelling if child.type else "unknown"
                param_name = child.spelling or ""
                parameters.append(f"{param_type} {param_name}".strip())
        
        if 'methods' not in class_context['data']:
            class_context['data']['methods'] = {}
        
        class_context['data']['methods'][method_name] = {
            'location': {
                'start_line': location['start_line'],
                'end_line': location['end_line'],
            },
            'parameters': parameters,
            'return_type': return_type,
            'loops': [],
        }
        
        self.logger.debug(f"Found method: {method_name} in class {class_context['name']}")
    
    def _analyze_loop(self, cursor: Cursor, file_analysis: Dict[str, Any], 
                     target_file: Path, parent_context: Optional[Dict] = None) -> None:
        """Analyze a loop statement."""
        loop_id = f"loop_{cursor.location.line}_{cursor.location.column}"
        loop_type = self.LOOP_TYPES.get(cursor.kind, 'unknown_loop')
        
        location = self.ast_parser.get_cursor_location(cursor)
        
        # Basic loop information
        loop_info = {
            'loop_id': loop_id,
            'type': loop_type,
            'location': {
                'start_line': location['start_line'],
                'end_line': location['end_line'],
                'start_column': location['start_column'],
                'end_column': location['end_column'],
            },
            'loop_bounds': self._extract_loop_bounds(cursor),
            'nesting_level': self._calculate_nesting_level(cursor),
            'nested_loops': [],
            'operations': {
                'arithmetic': [],
                'assignments': [],
                'function_calls': [],
            },
            'memory_access': {
                'reads': [],
                'writes': [],
            },
            'function_calls': [],
            'extensions': {},
        }
        
        # Analyze loop body
        self._analyze_loop_body(cursor, loop_info, target_file)
        
        # Add to appropriate container
        if parent_context:
            if parent_context['type'] == 'function':
                # Find the function and add the loop
                for func_data in file_analysis['functions'].values():
                    if (func_data['location']['start_line'] <= location['start_line'] <= 
                        func_data['location']['end_line']):
                        func_data['loops'].append(loop_info)
                        break
            elif parent_context['type'] == 'class':
                # Find the method and add the loop
                class_data = parent_context['data']
                if 'methods' in class_data:
                    for method_data in class_data['methods'].values():
                        if (method_data['location']['start_line'] <= location['start_line'] <= 
                            method_data['location']['end_line']):
                            method_data['loops'].append(loop_info)
                            break
        else:
            # Global loop (rare)
            file_analysis['global_loops'].append(loop_info)
        
        # Update total loop count
        file_analysis['file_info']['total_loops'] += 1
        
        self.logger.debug(f"Found {loop_type}: {loop_id}")
    
    def _extract_loop_bounds(self, cursor: Cursor) -> Dict[str, str]:
        """Extract loop bounds information."""
        bounds = {
            'initialization': '',
            'condition': '',
            'increment': '',
            'estimated_iterations': 'unknown',
        }
        
        try:
            if cursor.kind == CursorKind.FOR_STMT:
                # For loop: init; condition; increment
                children = list(cursor.get_children())
                if len(children) >= 3:
                    # Initialization
                    init_cursor = children[0]
                    bounds['initialization'] = self.ast_parser.get_source_text(init_cursor).strip()
                    
                    # Condition
                    cond_cursor = children[1]
                    bounds['condition'] = self.ast_parser.get_source_text(cond_cursor).strip()
                    
                    # Increment
                    inc_cursor = children[2]
                    bounds['increment'] = self.ast_parser.get_source_text(inc_cursor).strip()
                    
            elif cursor.kind == CursorKind.WHILE_STMT:
                # While loop: condition
                children = list(cursor.get_children())
                if len(children) >= 1:
                    cond_cursor = children[0]
                    bounds['condition'] = self.ast_parser.get_source_text(cond_cursor).strip()
                    
            elif cursor.kind == CursorKind.DO_STMT:
                # Do-while loop: condition is typically the last child
                children = list(cursor.get_children())
                if len(children) >= 2:
                    cond_cursor = children[-1]  # Last child is usually condition
                    bounds['condition'] = self.ast_parser.get_source_text(cond_cursor).strip()
                    
        except Exception as e:
            self.logger.debug(f"Error extracting loop bounds: {e}")
        
        return bounds
    
    def _calculate_nesting_level(self, cursor: Cursor) -> int:
        """Calculate the nesting level of a loop."""
        level = 1
        parent = cursor.semantic_parent
        
        while parent:
            if parent.kind in self.LOOP_TYPES:
                level += 1
            parent = parent.semantic_parent
        
        return level
    
    def _analyze_loop_body(self, cursor: Cursor, loop_info: Dict[str, Any], target_file: Path) -> None:
        """Analyze the body of a loop for operations and memory access."""
        try:
            # Find the loop body (usually the last child for most loop types)
            children = list(cursor.get_children())
            if not children:
                return
            
            # For most loops, the body is the last child
            body_cursor = children[-1]
            
            # Recursively analyze the body
            self._analyze_loop_body_recursive(body_cursor, loop_info, target_file)
            
        except Exception as e:
            self.logger.debug(f"Error analyzing loop body: {e}")
    
    def _analyze_loop_body_recursive(self, cursor: Cursor, loop_info: Dict[str, Any], target_file: Path) -> None:
        """Recursively analyze loop body for operations."""
        try:
            # Skip if not in target file
            if not self.ast_parser.is_in_file(cursor, target_file):
                return
            
            cursor_kind = cursor.kind
            location = self.ast_parser.get_cursor_location(cursor)
            
            # Check for nested loops
            if cursor_kind in self.LOOP_TYPES:
                nested_loop = {
                    'loop_id': f"loop_{location['start_line']}_{location['start_column']}",
                    'type': self.LOOP_TYPES[cursor_kind],
                    'location': {
                        'start_line': location['start_line'],
                        'end_line': location['end_line'],
                        'start_column': location['start_column'],
                        'end_column': location['end_column'],
                    },
                    'loop_bounds': self._extract_loop_bounds(cursor),
                    'nesting_level': loop_info['nesting_level'] + 1,
                    'nested_loops': [],
                    'operations': {'arithmetic': [], 'assignments': [], 'function_calls': []},
                    'memory_access': {'reads': [], 'writes': []},
                    'function_calls': [],
                }
                
                # Recursively analyze nested loop
                self._analyze_loop_body(cursor, nested_loop, target_file)
                loop_info['nested_loops'].append(nested_loop)
                return
            
            # Analyze operations
            if cursor_kind == CursorKind.BINARY_OPERATOR:
                self._analyze_binary_operation(cursor, loop_info, location)
            elif cursor_kind == CursorKind.UNARY_OPERATOR:
                self._analyze_unary_operation(cursor, loop_info, location)
            elif cursor_kind == CursorKind.CALL_EXPR:
                self._analyze_function_call(cursor, loop_info, location)
            elif cursor_kind in {CursorKind.DECL_REF_EXPR, CursorKind.ARRAY_SUBSCRIPT_EXPR}:
                self._analyze_memory_access(cursor, loop_info, location)
            
            # Recursively analyze children
            for child in cursor.get_children():
                self._analyze_loop_body_recursive(child, loop_info, target_file)
                
        except Exception as e:
            self.logger.debug(f"Error in recursive loop body analysis: {e}")
    
    def _analyze_binary_operation(self, cursor: Cursor, loop_info: Dict[str, Any], location: Dict) -> None:
        """Analyze binary operations."""
        try:
            # Get the operator (this is tricky with libclang, approximate from source)
            source_text = self.ast_parser.get_source_text(cursor)
            
            # Simple heuristic to detect operation type
            if any(op in source_text for op in self.ARITHMETIC_OPS):
                op_type = 'arithmetic'
            elif any(op in source_text for op in self.LOGICAL_OPS):
                op_type = 'logical'
            elif any(op in source_text for op in self.BITWISE_OPS):
                op_type = 'bitwise'
            else:
                op_type = 'unknown'
            
            operation = {
                'type': op_type,
                'expression': source_text.strip(),
                'line': location['line'],
            }
            
            if op_type in loop_info['operations']:
                loop_info['operations'][op_type].append(operation)
            else:
                loop_info['operations'].setdefault('other', []).append(operation)
                
        except Exception as e:
            self.logger.debug(f"Error analyzing binary operation: {e}")
    
    def _analyze_unary_operation(self, cursor: Cursor, loop_info: Dict[str, Any], location: Dict) -> None:
        """Analyze unary operations."""
        try:
            source_text = self.ast_parser.get_source_text(cursor)
            
            operation = {
                'type': 'unary',
                'expression': source_text.strip(),
                'line': location['line'],
            }
            
            loop_info['operations'].setdefault('unary', []).append(operation)
            
        except Exception as e:
            self.logger.debug(f"Error analyzing unary operation: {e}")
    
    def _analyze_function_call(self, cursor: Cursor, loop_info: Dict[str, Any], location: Dict) -> None:
        """Analyze function calls."""
        try:
            function_name = cursor.spelling or "unknown_function"
            
            # Extract arguments
            arguments = []
            for child in cursor.get_children():
                if child.kind != CursorKind.UNEXPOSED_EXPR:
                    arg_text = self.ast_parser.get_source_text(child).strip()
                    if arg_text:
                        arguments.append(arg_text)
            
            function_call = {
                'function': function_name,
                'arguments': arguments,
                'line': location['line'],
            }
            
            loop_info['operations']['function_calls'].append(function_call)
            
            # Also add to detailed function calls
            detailed_call = {
                'function': function_name,
                'location': {
                    'line': location['line'],
                    'column': location['column'],
                },
                'resolved': bool(cursor.referenced),
                'definition_file': str(cursor.referenced.location.file) if cursor.referenced and cursor.referenced.location.file else '',
            }
            
            loop_info['function_calls'].append(detailed_call)
            
        except Exception as e:
            self.logger.debug(f"Error analyzing function call: {e}")
    
    def _analyze_memory_access(self, cursor: Cursor, loop_info: Dict[str, Any], location: Dict) -> None:
        """Analyze memory access patterns."""
        try:
            source_text = self.ast_parser.get_source_text(cursor).strip()
            if not source_text:
                return
            
            # Determine access type
            access_type = 'unknown'
            if '[' in source_text and ']' in source_text:
                # Array access
                if source_text.count('[') == 1:
                    access_type = '1d_array'
                elif source_text.count('[') == 2:
                    access_type = '2d_array'
                else:
                    access_type = 'multi_array'
            elif '*' in source_text:
                access_type = 'pointer'
            elif '.' in source_text or '->' in source_text:
                access_type = 'struct_member'
            else:
                access_type = 'variable'
            
            # Extract variable name (simple heuristic)
            variable_name = source_text.split('[')[0].split('.')[0].split('->')[0].strip()
            
            memory_access = {
                'variable': variable_name,
                'access_pattern': source_text,
                'access_type': access_type,
                'stride_pattern': 'unknown',  # Would need more sophisticated analysis
                'line': location['line'],
            }
            
            # For now, assume all accesses are reads (write detection would need more context)
            loop_info['memory_access']['reads'].append(memory_access)
            
        except Exception as e:
            self.logger.debug(f"Error analyzing memory access: {e}")
    
    def count_loops(self, file_analysis: Dict[str, Any]) -> int:
        """Count total loops in a file analysis."""
        total = len(file_analysis.get('global_loops', []))
        
        # Count loops in functions
        for func_data in file_analysis.get('functions', {}).values():
            total += self._count_loops_recursive(func_data.get('loops', []))
        
        # Count loops in class methods
        for class_data in file_analysis.get('classes', {}).values():
            for method_data in class_data.get('methods', {}).values():
                total += self._count_loops_recursive(method_data.get('loops', []))
        
        return total
    
    def _count_loops_recursive(self, loops: List[Dict]) -> int:
        """Recursively count loops including nested ones."""
        total = len(loops)
        for loop in loops:
            total += self._count_loops_recursive(loop.get('nested_loops', []))
        return total