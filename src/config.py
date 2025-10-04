"""
Configuration management for Loop Extractor.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import List


@dataclass
class Config:
    """Configuration class for Loop Extractor."""
    
    source_path: Path
    output_path: Path
    include_patterns: List[str]
    exclude_patterns: List[str]
    cpp_standard: str
    log_level: str
    
    # Default file extensions to search for
    DEFAULT_EXTENSIONS = {'.c', '.cpp', '.cc', '.cxx', '.h', '.hpp', '.hxx'}
    
    # Default include directories
    DEFAULT_INCLUDES = [
        '/usr/include', 
        '/usr/local/include',
        '/usr/local/Cellar/llvm/21.1.1/include/c++/v1',  # macOS libcxx
        '/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/include/c++/v1',  # Xcode
    ]
    
    # Compiler flags based on C++ standard
    STANDARD_FLAGS = {
        'c++11': ['-std=c++11'],
        'c++14': ['-std=c++14'],
        'c++17': ['-std=c++17'],
        'c++20': ['-std=c++20'],
    }
    
    def get_compiler_flags(self) -> List[str]:
        """Get compiler flags for the specified C++ standard."""
        flags = self.STANDARD_FLAGS.get(self.cpp_standard, ['-std=c++17'])
        
        # Add default include directories (avoid duplicates)
        added_includes = set()
        for include_dir in self.DEFAULT_INCLUDES:
            if Path(include_dir).exists() and include_dir not in added_includes:
                flags.append(f'-I{include_dir}')
                added_includes.add(include_dir)
        
        return flags
    
    def should_include_file(self, file_path: Path) -> bool:
        """Check if a file should be included based on patterns."""
        file_str = str(file_path)
        
        # Check extension
        if file_path.suffix not in self.DEFAULT_EXTENSIONS:
            return False
        
        # Check exclude patterns
        for pattern in self.exclude_patterns:
            if pattern in file_str:
                return False
        
        # Check include patterns (if specified)
        if self.include_patterns:
            for pattern in self.include_patterns:
                if pattern in file_str:
                    return True
            return False
        
        return True