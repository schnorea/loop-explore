"""
File discovery module for finding C/C++ source files.
"""

import logging
from pathlib import Path
from typing import List, Set

from .config import Config


class FileDiscovery:
    """Handles discovery of C/C++ source files in a directory tree."""
    
    def __init__(self, config: Config):
        """Initialize file discovery with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def discover_files(self) -> List[Path]:
        """Discover all C/C++ source files in the configured path."""
        discovered_files = []
        
        try:
            discovered_files = self._traverse_directory(self.config.source_path)
            self.logger.info(f"Discovered {len(discovered_files)} source files")
            
        except Exception as e:
            self.logger.error(f"Error during file discovery: {e}")
            
        return discovered_files
    
    def _traverse_directory(self, directory: Path) -> List[Path]:
        """Recursively traverse directory to find source files."""
        files = []
        
        try:
            for item in directory.iterdir():
                if item.is_file():
                    if self.config.should_include_file(item):
                        files.append(item)
                        self.logger.debug(f"Including file: {item}")
                    else:
                        self.logger.debug(f"Excluding file: {item}")
                        
                elif item.is_dir():
                    # Skip hidden directories and common build directories
                    if self._should_skip_directory(item):
                        self.logger.debug(f"Skipping directory: {item}")
                        continue
                        
                    # Recursively process subdirectory
                    try:
                        subdir_files = self._traverse_directory(item)
                        files.extend(subdir_files)
                    except PermissionError:
                        self.logger.warning(f"Permission denied accessing directory: {item}")
                    except Exception as e:
                        self.logger.warning(f"Error accessing directory {item}: {e}")
                        
        except PermissionError:
            self.logger.warning(f"Permission denied accessing directory: {directory}")
        except Exception as e:
            self.logger.error(f"Error traversing directory {directory}: {e}")
            
        return files
    
    def _should_skip_directory(self, directory: Path) -> bool:
        """Check if a directory should be skipped during traversal."""
        skip_dirs = {
            '.git', '.svn', '.hg',  # Version control
            'build', 'builds', 'Build', 'BUILD',  # Build directories
            'cmake-build-debug', 'cmake-build-release',  # CMake build dirs
            'out', 'output', 'bin', 'obj',  # Output directories
            '.vscode', '.idea',  # IDE directories
            'node_modules',  # Node.js
            '__pycache__', '.pytest_cache',  # Python
            'target',  # Rust/Java
            '.vs',  # Visual Studio
        }
        
        # Skip hidden directories (starting with .)
        if directory.name.startswith('.') and directory.name not in {'.', '..'}:
            # Allow some specific hidden directories that might contain source
            allowed_hidden = {'.config', '.src'}
            if directory.name not in allowed_hidden:
                return True
        
        # Skip known build/output directories
        if directory.name in skip_dirs:
            return True
            
        # Check exclude patterns
        dir_str = str(directory)
        for pattern in self.config.exclude_patterns:
            if pattern in dir_str:
                return True
                
        return False
    
    def get_file_info(self, file_path: Path) -> dict:
        """Get metadata information about a file."""
        try:
            stat = file_path.stat()
            return {
                'size_bytes': stat.st_size,
                'last_modified': stat.st_mtime,
                'permissions': oct(stat.st_mode)[-3:],
            }
        except Exception as e:
            self.logger.warning(f"Could not get file info for {file_path}: {e}")
            return {
                'size_bytes': 0,
                'last_modified': 0,
                'permissions': '000',
            }