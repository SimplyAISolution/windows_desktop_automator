"""
File system operations provider with secure path validation.
Handles file and directory operations with safety checks.
"""

import os
import shutil
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Optional

from automator.core.logger import automator_logger


class FileSystemProvider:
    """Provider for file system operations with security constraints."""
    
    def __init__(self, allowed_paths: Optional[List[str]] = None):
        """
        Initialize file system provider.
        
        Args:
            allowed_paths: List of allowed base paths for operations
        """
        self.allowed_paths = allowed_paths or [
            os.getcwd(),  # Current working directory
            os.path.join(os.getcwd(), "artifacts"),
            tempfile.gettempdir()
        ]
        
        # Normalize paths
        self.allowed_paths = [os.path.abspath(path) for path in self.allowed_paths]
    
    def read_file(self, file_path: str, encoding: str = 'utf-8') -> str:
        """
        Read text content from file.
        
        Args:
            file_path: Path to file
            encoding: Text encoding
            
        Returns:
            File content as string
        """
        step_id = automator_logger.log_step_start("read_file", file_path, encoding=encoding)
        
        try:
            validated_path = self._validate_path(file_path, must_exist=True)
            
            with open(validated_path, 'r', encoding=encoding) as f:
                content = f.read()
            
            automator_logger.log_step_success(step_id, "read_file", file_path, 
                                            result=f"{len(content)} characters")
            return content
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "read_file", file_path, e)
            raise
    
    def write_file(self, file_path: str, content: str, encoding: str = 'utf-8', 
                   create_dirs: bool = True) -> bool:
        """
        Write text content to file.
        
        Args:
            file_path: Path to file
            content: Content to write
            encoding: Text encoding
            create_dirs: Create parent directories if needed
            
        Returns:
            True if successful
        """
        step_id = automator_logger.log_step_start("write_file", file_path, 
                                                  content_length=len(content), encoding=encoding)
        
        try:
            validated_path = self._validate_path(file_path, for_write=True)
            
            if create_dirs:
                parent_dir = os.path.dirname(validated_path)
                os.makedirs(parent_dir, exist_ok=True)
            
            with open(validated_path, 'w', encoding=encoding) as f:
                f.write(content)
            
            automator_logger.log_step_success(step_id, "write_file", file_path, 
                                            result=f"{len(content)} characters written")
            return True
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "write_file", file_path, e)
            return False
    
    def append_file(self, file_path: str, content: str, encoding: str = 'utf-8') -> bool:
        """
        Append content to file.
        
        Args:
            file_path: Path to file
            content: Content to append
            encoding: Text encoding
            
        Returns:
            True if successful
        """
        step_id = automator_logger.log_step_start("append_file", file_path, 
                                                  content_length=len(content))
        
        try:
            validated_path = self._validate_path(file_path, for_write=True)
            
            with open(validated_path, 'a', encoding=encoding) as f:
                f.write(content)
            
            automator_logger.log_step_success(step_id, "append_file", file_path, 
                                            result=f"{len(content)} characters appended")
            return True
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "append_file", file_path, e)
            return False
    
    def copy_file(self, source_path: str, dest_path: str, overwrite: bool = False) -> bool:
        """
        Copy file from source to destination.
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
            overwrite: Overwrite if destination exists
            
        Returns:
            True if successful
        """
        step_id = automator_logger.log_step_start("copy_file", f"{source_path} -> {dest_path}", 
                                                  overwrite=overwrite)
        
        try:
            validated_source = self._validate_path(source_path, must_exist=True)
            validated_dest = self._validate_path(dest_path, for_write=True)
            
            if os.path.exists(validated_dest) and not overwrite:
                raise FileExistsError(f"Destination file exists: {dest_path}")
            
            # Create destination directory if needed
            dest_dir = os.path.dirname(validated_dest)
            os.makedirs(dest_dir, exist_ok=True)
            
            shutil.copy2(validated_source, validated_dest)
            
            automator_logger.log_step_success(step_id, "copy_file", f"{source_path} -> {dest_path}")
            return True
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "copy_file", f"{source_path} -> {dest_path}", e)
            return False
    
    def move_file(self, source_path: str, dest_path: str, overwrite: bool = False) -> bool:
        """
        Move file from source to destination.
        
        Args:
            source_path: Source file path
            dest_path: Destination file path
            overwrite: Overwrite if destination exists
            
        Returns:
            True if successful
        """
        step_id = automator_logger.log_step_start("move_file", f"{source_path} -> {dest_path}", 
                                                  overwrite=overwrite)
        
        try:
            validated_source = self._validate_path(source_path, must_exist=True)
            validated_dest = self._validate_path(dest_path, for_write=True)
            
            if os.path.exists(validated_dest) and not overwrite:
                raise FileExistsError(f"Destination file exists: {dest_path}")
            
            # Create destination directory if needed
            dest_dir = os.path.dirname(validated_dest)
            os.makedirs(dest_dir, exist_ok=True)
            
            shutil.move(validated_source, validated_dest)
            
            automator_logger.log_step_success(step_id, "move_file", f"{source_path} -> {dest_path}")
            return True
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "move_file", f"{source_path} -> {dest_path}", e)
            return False
    
    def delete_file(self, file_path: str, missing_ok: bool = True) -> bool:
        """
        Delete file.
        
        Args:
            file_path: Path to file
            missing_ok: Don't raise error if file doesn't exist
            
        Returns:
            True if successful
        """
        step_id = automator_logger.log_step_start("delete_file", file_path, missing_ok=missing_ok)
        
        try:
            validated_path = self._validate_path(file_path, must_exist=not missing_ok)
            
            if not os.path.exists(validated_path):
                if missing_ok:
                    automator_logger.log_step_success(step_id, "delete_file", file_path, 
                                                    result="File already deleted")
                    return True
                else:
                    raise FileNotFoundError(f"File not found: {file_path}")
            
            os.remove(validated_path)
            
            automator_logger.log_step_success(step_id, "delete_file", file_path)
            return True
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "delete_file", file_path, e)
            return False
    
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        try:
            validated_path = self._validate_path(file_path)
            return os.path.isfile(validated_path)
        except Exception:
            return False
    
    def directory_exists(self, dir_path: str) -> bool:
        """Check if directory exists."""
        try:
            validated_path = self._validate_path(dir_path)
            return os.path.isdir(validated_path)
        except Exception:
            return False
    
    def create_directory(self, dir_path: str, parents: bool = True) -> bool:
        """
        Create directory.
        
        Args:
            dir_path: Directory path
            parents: Create parent directories
            
        Returns:
            True if successful
        """
        step_id = automator_logger.log_step_start("create_directory", dir_path, parents=parents)
        
        try:
            validated_path = self._validate_path(dir_path, for_write=True)
            
            os.makedirs(validated_path, exist_ok=True)
            
            automator_logger.log_step_success(step_id, "create_directory", dir_path)
            return True
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "create_directory", dir_path, e)
            return False
    
    def list_directory(self, dir_path: str, pattern: str = "*", 
                      files_only: bool = False, dirs_only: bool = False) -> List[str]:
        """
        List directory contents.
        
        Args:
            dir_path: Directory path
            pattern: File pattern (glob)
            files_only: Return only files
            dirs_only: Return only directories
            
        Returns:
            List of file/directory names
        """
        step_id = automator_logger.log_step_start("list_directory", dir_path, 
                                                  pattern=pattern, files_only=files_only, dirs_only=dirs_only)
        
        try:
            validated_path = self._validate_path(dir_path, must_exist=True)
            
            if not os.path.isdir(validated_path):
                raise NotADirectoryError(f"Not a directory: {dir_path}")
            
            import glob
            search_path = os.path.join(validated_path, pattern)
            items = glob.glob(search_path)
            
            # Filter based on type
            if files_only:
                items = [item for item in items if os.path.isfile(item)]
            elif dirs_only:
                items = [item for item in items if os.path.isdir(item)]
            
            # Return relative names
            items = [os.path.basename(item) for item in items]
            
            automator_logger.log_step_success(step_id, "list_directory", dir_path, 
                                            result=f"{len(items)} items")
            return items
            
        except Exception as e:
            automator_logger.log_step_failure(step_id, "list_directory", dir_path, e)
            return []
    
    def get_file_info(self, file_path: str) -> Optional[Dict[str, Any]]:
        """
        Get file information.
        
        Args:
            file_path: Path to file
            
        Returns:
            Dictionary with file info or None if file doesn't exist
        """
        try:
            validated_path = self._validate_path(file_path, must_exist=True)
            
            stat = os.stat(validated_path)
            
            return {
                'size': stat.st_size,
                'modified_time': stat.st_mtime,
                'created_time': stat.st_ctime,
                'is_file': os.path.isfile(validated_path),
                'is_directory': os.path.isdir(validated_path),
                'absolute_path': os.path.abspath(validated_path)
            }
        except Exception:
            return None
    
    def _validate_path(self, path: str, must_exist: bool = False, for_write: bool = False) -> str:
        """
        Validate file path against security constraints.
        
        Args:
            path: File path to validate
            must_exist: Path must exist
            for_write: Path is for write operation
            
        Returns:
            Validated absolute path
            
        Raises:
            ValueError: If path is invalid
            FileNotFoundError: If must_exist=True and file doesn't exist
        """
        if not path or not isinstance(path, str):
            raise ValueError("Invalid file path")
        
        # Convert to absolute path
        abs_path = os.path.abspath(path)
        
        # Check if path is within allowed directories
        path_allowed = False
        for allowed in self.allowed_paths:
            try:
                # Use Path.resolve() to handle symlinks and relative paths
                if Path(abs_path).resolve().is_relative_to(Path(allowed).resolve()):
                    path_allowed = True
                    break
            except (ValueError, OSError):
                continue
        
        if not path_allowed:
            raise ValueError(f"Path not allowed: {path}")
        
        # Check existence if required
        if must_exist and not os.path.exists(abs_path):
            raise FileNotFoundError(f"Path does not exist: {path}")
        
        return abs_path
    
    def add_allowed_path(self, path: str):
        """Add path to allowed paths list."""
        abs_path = os.path.abspath(path)
        if abs_path not in self.allowed_paths:
            self.allowed_paths.append(abs_path)
