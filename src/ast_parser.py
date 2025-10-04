"""
Clang AST parser module for parsing C/C++ source files.
"""

import logging
from pathlib import Path
from typing import Optional, List

try:
    import clang.cindex as clang
    from clang.cindex import TranslationUnit, CursorKind, Cursor
except ImportError as e:
    raise ImportError("libclang not found. Please install with: pip install libclang") from e

from .config import Config


class ASTParser:
    """Handles parsing of C/C++ source files using Clang AST."""
    
    def __init__(self, config: Config):
        """Initialize AST parser with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.index = None
        self._initialize_clang()
    
    def _initialize_clang(self) -> None:
        """Initialize Clang library."""
        try:
            # Try to find libclang in common locations
            possible_paths = [
                '/usr/local/Cellar/llvm/21.1.1/lib/libclang.dylib',  # Homebrew macOS Intel
                '/opt/homebrew/lib/libclang.dylib',  # Homebrew macOS ARM
                '/usr/local/lib/libclang.dylib',  # macOS generic
                '/usr/lib/llvm-16/lib/libclang.so.1',  # Linux
                '/usr/lib/libclang.so.1',  # Linux generic
            ]
            
            for path in possible_paths:
                if Path(path).exists():
                    clang.conf.set_library_file(path)
                    self.logger.debug(f"Using libclang at: {path}")
                    break
            else:
                # Let clang find it automatically
                self.logger.debug("Using automatic libclang detection")
        except Exception as e:
            self.logger.debug(f"Error setting libclang path: {e}")
            # Continue and try automatic detection
        
        try:
            self.index = clang.Index.create()
            self.logger.info("Clang AST parser initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize Clang: {e}")
            raise
    
    def parse_file(self, file_path: Path) -> Optional[TranslationUnit]:
        """Parse a single source file and return the translation unit."""
        if self.index is None:
            self.logger.error("Clang index not initialized")
            return None
        
        try:
            # Get compiler flags
            flags = self.config.get_compiler_flags()
            
            # Add file-specific flags if needed
            if file_path.suffix in {'.hpp', '.h', '.hxx'}:
                # For header files, add C++ flag to ensure proper parsing
                flags.append('-x')
                flags.append('c++')
            
            self.logger.debug(f"Parsing {file_path} with flags: {flags}")
            
            # Parse the file
            translation_unit = self.index.parse(
                str(file_path),
                args=flags,
                options=TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD
            )
            
            if translation_unit is None:
                self.logger.error(f"Failed to parse {file_path}")
                return None
            
            # Check for parsing errors
            diagnostics = list(translation_unit.diagnostics)
            if diagnostics:
                error_count = sum(1 for d in diagnostics if d.severity >= clang.Diagnostic.Error)
                warning_count = sum(1 for d in diagnostics if d.severity == clang.Diagnostic.Warning)
                
                if error_count > 0:
                    self.logger.warning(f"Parse errors in {file_path}: {error_count} errors, {warning_count} warnings")
                    for diag in diagnostics:
                        if diag.severity >= clang.Diagnostic.Error:
                            self.logger.debug(f"  Error: {diag}")
                elif warning_count > 0:
                    self.logger.debug(f"Parse warnings in {file_path}: {warning_count} warnings")
            
            self.logger.debug(f"Successfully parsed {file_path}")
            return translation_unit
            
        except Exception as e:
            self.logger.error(f"Exception parsing {file_path}: {e}")
            return None
    
    def get_cursor_location(self, cursor: Cursor) -> dict:
        """Get location information for a cursor."""
        try:
            location = cursor.location
            extent = cursor.extent
            
            return {
                'file': str(location.file) if location.file else '',
                'line': location.line,
                'column': location.column,
                'start_line': extent.start.line,
                'end_line': extent.end.line,
                'start_column': extent.start.column,
                'end_column': extent.end.column,
            }
        except Exception as e:
            self.logger.debug(f"Error getting cursor location: {e}")
            return {
                'file': '',
                'line': 0,
                'column': 0,
                'start_line': 0,
                'end_line': 0,
                'start_column': 0,
                'end_column': 0,
            }
    
    def get_source_text(self, cursor: Cursor) -> str:
        """Get the source text for a cursor."""
        try:
            extent = cursor.extent
            if extent.start.file and extent.end.file:
                # Read the file and extract the relevant portion
                file_path = Path(extent.start.file.name)
                if file_path.exists():
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                    
                    start_line = extent.start.line - 1  # Convert to 0-based
                    end_line = extent.end.line - 1
                    
                    if start_line == end_line:
                        # Single line
                        if start_line < len(lines):
                            line = lines[start_line]
                            return line[extent.start.column-1:extent.end.column-1]
                    else:
                        # Multiple lines
                        result_lines = []
                        for i in range(start_line, min(end_line + 1, len(lines))):
                            if i == start_line:
                                result_lines.append(lines[i][extent.start.column-1:])
                            elif i == end_line:
                                result_lines.append(lines[i][:extent.end.column-1])
                            else:
                                result_lines.append(lines[i])
                        return ''.join(result_lines)
        except Exception as e:
            self.logger.debug(f"Error getting source text: {e}")
        
        return ""
    
    def is_in_file(self, cursor: Cursor, target_file: Path) -> bool:
        """Check if a cursor is located in the target file."""
        try:
            location = cursor.location
            if location.file:
                cursor_file = Path(location.file.name).resolve()
                target_file = target_file.resolve()
                return cursor_file == target_file
        except:
            pass
        return False