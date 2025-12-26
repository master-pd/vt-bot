"""
Advanced File Handler
Professional file operations with async support
"""

import os
import json
import csv
import pickle
import zipfile
import tarfile
import hashlib
import shutil
import asyncio
import aiofiles
from pathlib import Path
from typing import Any, List, Dict, Union, Optional
from datetime import datetime

from utils.logger import setup_logger
from utils.error_handler import handle_errors, async_handle_errors
from config import DATA_DIR, BACKUP_DIR

logger = setup_logger(__name__)

class FileHandler:
    """Advanced file handler with async support"""
    
    def __init__(self, base_dir: Path = DATA_DIR):
        self.base_dir = base_dir
        self.base_dir.mkdir(parents=True, exist_ok=True)
    
    @async_handle_errors
    async def read_file(self, file_path: Union[str, Path], mode: str = "r") -> str:
        """Read file content asynchronously"""
        path = self._resolve_path(file_path)
        
        async with aiofiles.open(path, mode, encoding='utf-8') as f:
            return await f.read()
    
    @async_handle_errors
    async def write_file(self, file_path: Union[str, Path], content: str, mode: str = "w") -> bool:
        """Write content to file asynchronously"""
        path = self._resolve_path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(path, mode, encoding='utf-8') as f:
            await f.write(content)
        
        return True
    
    @async_handle_errors
    async def read_json(self, file_path: Union[str, Path]) -> Any:
        """Read JSON file asynchronously"""
        content = await self.read_file(file_path)
        return json.loads(content)
    
    @async_handle_errors
    async def write_json(self, file_path: Union[str, Path], data: Any, indent: int = 2) -> bool:
        """Write data to JSON file asynchronously"""
        content = json.dumps(data, indent=indent, default=str, ensure_ascii=False)
        return await self.write_file(file_path, content)
    
    @async_handle_errors
    async def read_lines(self, file_path: Union[str, Path]) -> List[str]:
        """Read file lines asynchronously"""
        content = await self.read_file(file_path)
        return [line.strip() for line in content.splitlines() if line.strip()]
    
    @async_handle_errors
    async def write_lines(self, file_path: Union[str, Path], lines: List[str]) -> bool:
        """Write lines to file asynchronously"""
        content = "\n".join(lines)
        return await self.write_file(file_path, content)
    
    @async_handle_errors
    async def append_line(self, file_path: Union[str, Path], line: str) -> bool:
        """Append line to file asynchronously"""
        path = self._resolve_path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        async with aiofiles.open(path, "a", encoding='utf-8') as f:
            await f.write(line + "\n")
        
        return True
    
    @async_handle_errors
    async def read_csv(self, file_path: Union[str, Path]) -> List[Dict[str, Any]]:
        """Read CSV file asynchronously"""
        path = self._resolve_path(file_path)
        
        async with aiofiles.open(path, "r", encoding='utf-8') as f:
            content = await f.read()
        
        # Parse CSV
        lines = content.strip().splitlines()
        if not lines:
            return []
        
        reader = csv.DictReader(lines)
        return list(reader)
    
    @async_handle_errors
    async def write_csv(self, file_path: Union[str, Path], data: List[Dict[str, Any]]) -> bool:
        """Write data to CSV file asynchronously"""
        if not data:
            return False
        
        path = self._resolve_path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        fieldnames = data[0].keys()
        
        async with aiofiles.open(path, "w", encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            
            # Write header
            await asyncio.get_event_loop().run_in_executor(
                None, writer.writeheader
            )
            
            # Write rows
            for row in data:
                await asyncio.get_event_loop().run_in_executor(
                    None, writer.writerow, row
                )
        
        return True
    
    @async_handle_errors
    async def file_exists(self, file_path: Union[str, Path]) -> bool:
        """Check if file exists"""
        path = self._resolve_path(file_path)
        return path.exists()
    
    @async_handle_errors
    async def delete_file(self, file_path: Union[str, Path]) -> bool:
        """Delete file"""
        path = self._resolve_path(file_path)
        
        if path.exists():
            path.unlink()
            return True
        
        return False
    
    @async_handle_errors
    async def copy_file(self, src_path: Union[str, Path], dst_path: Union[str, Path]) -> bool:
        """Copy file"""
        src = self._resolve_path(src_path)
        dst = self._resolve_path(dst_path)
        
        if not src.exists():
            return False
        
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # Use asyncio for file copy
        await asyncio.get_event_loop().run_in_executor(
            None, shutil.copy2, src, dst
        )
        
        return True
    
    @async_handle_errors
    async def move_file(self, src_path: Union[str, Path], dst_path: Union[str, Path]) -> bool:
        """Move file"""
        src = self._resolve_path(src_path)
        dst = self._resolve_path(dst_path)
        
        if not src.exists():
            return False
        
        dst.parent.mkdir(parents=True, exist_ok=True)
        
        # Use asyncio for file move
        await asyncio.get_event_loop().run_in_executor(
            None, shutil.move, src, dst
        )
        
        return True
    
    @async_handle_errors
    async def list_files(self, directory: Union[str, Path], pattern: str = "*") -> List[Path]:
        """List files in directory matching pattern"""
        dir_path = self._resolve_path(directory)
        
        if not dir_path.exists():
            return []
        
        files = []
        for file_path in dir_path.glob(pattern):
            if file_path.is_file():
                files.append(file_path.relative_to(self.base_dir))
        
        return files
    
    @async_handle_errors
    async def create_directory(self, directory: Union[str, Path]) -> bool:
        """Create directory"""
        dir_path = self._resolve_path(directory)
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    
    @async_handle_errors
    async def delete_directory(self, directory: Union[str, Path]) -> bool:
        """Delete directory recursively"""
        dir_path = self._resolve_path(directory)
        
        if dir_path.exists():
            await asyncio.get_event_loop().run_in_executor(
                None, shutil.rmtree, dir_path
            )
            return True
        
        return False
    
    @async_handle_errors
    async def get_file_info(self, file_path: Union[str, Path]) -> Dict[str, Any]:
        """Get file information"""
        path = self._resolve_path(file_path)
        
        if not path.exists():
            return {}
        
        stat = path.stat()
        
        return {
            "path": str(path.relative_to(self.base_dir)),
            "size": stat.st_size,
            "size_human": self._format_size(stat.st_size),
            "created": datetime.fromtimestamp(stat.st_ctime),
            "modified": datetime.fromtimestamp(stat.st_mtime),
            "accessed": datetime.fromtimestamp(stat.st_atime),
            "is_file": path.is_file(),
            "is_dir": path.is_dir(),
            "extension": path.suffix.lower(),
            "name": path.name,
            "parent": str(path.parent.relative_to(self.base_dir))
        }
    
    @async_handle_errors
    async def calculate_hash(self, file_path: Union[str, Path], algorithm: str = "md5") -> str:
        """Calculate file hash"""
        path = self._resolve_path(file_path)
        
        if not path.exists():
            return ""
        
        hash_func = getattr(hashlib, algorithm, hashlib.md5)()
        
        async with aiofiles.open(path, "rb") as f:
            while chunk := await f.read(8192):
                hash_func.update(chunk)
        
        return hash_func.hexdigest()
    
    @async_handle_errors
    async def backup_file(self, file_path: Union[str, Path], backup_dir: Path = BACKUP_DIR) -> bool:
        """Create backup of file"""
        src = self._resolve_path(file_path)
        
        if not src.exists():
            return False
        
        # Create backup directory with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{src.stem}_{timestamp}{src.suffix}"
        backup_path = backup_dir / backup_name
        
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        return await self.copy_file(src, backup_path)
    
    @async_handle_errors
    async def create_archive(
        self, 
        source_dir: Union[str, Path], 
        archive_path: Union[str, Path],
        format: str = "zip"
    ) -> bool:
        """Create archive of directory"""
        source = self._resolve_path(source_dir)
        archive = self._resolve_path(archive_path)
        
        if not source.exists():
            return False
        
        archive.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "zip":
            await asyncio.get_event_loop().run_in_executor(
                None, self._create_zip_archive, source, archive
            )
        elif format == "tar":
            await asyncio.get_event_loop().run_in_executor(
                None, self._create_tar_archive, source, archive
            )
        else:
            raise ValueError(f"Unsupported archive format: {format}")
        
        return True
    
    @async_handle_errors
    async def extract_archive(
        self, 
        archive_path: Union[str, Path], 
        extract_dir: Union[str, Path]
    ) -> bool:
        """Extract archive"""
        archive = self._resolve_path(archive_path)
        extract_to = self._resolve_path(extract_dir)
        
        if not archive.exists():
            return False
        
        extract_to.mkdir(parents=True, exist_ok=True)
        
        if archive.suffix.lower() == ".zip":
            await asyncio.get_event_loop().run_in_executor(
                None, self._extract_zip_archive, archive, extract_to
            )
        elif archive.suffix.lower() in [".tar", ".gz", ".bz2", ".xz"]:
            await asyncio.get_event_loop().run_in_executor(
                None, self._extract_tar_archive, archive, extract_to
            )
        else:
            raise ValueError(f"Unsupported archive format: {archive.suffix}")
        
        return True
    
    @async_handle_errors
    async def search_files(
        self, 
        directory: Union[str, Path], 
        pattern: str, 
        recursive: bool = True
    ) -> List[Path]:
        """Search for files matching pattern"""
        dir_path = self._resolve_path(directory)
        
        if not dir_path.exists():
            return []
        
        files = []
        
        if recursive:
            search_path = dir_path.rglob(pattern)
        else:
            search_path = dir_path.glob(pattern)
        
        for file_path in search_path:
            if file_path.is_file():
                files.append(file_path.relative_to(self.base_dir))
        
        return files
    
    @async_handle_errors
    async def find_duplicate_files(
        self, 
        directory: Union[str, Path], 
        algorithm: str = "md5"
    ) -> Dict[str, List[str]]:
        """Find duplicate files by hash"""
        dir_path = self._resolve_path(directory)
        
        if not dir_path.exists():
            return {}
        
        # Get all files
        all_files = []
        for file_path in dir_path.rglob("*"):
            if file_path.is_file():
                all_files.append(file_path)
        
        # Calculate hashes
        hash_dict = {}
        for file_path in all_files:
            file_hash = await self.calculate_hash(file_path, algorithm)
            if file_hash not in hash_dict:
                hash_dict[file_hash] = []
            
            hash_dict[file_hash].append(str(file_path.relative_to(self.base_dir)))
        
        # Return only duplicates
        return {hash_value: files for hash_value, files in hash_dict.items() if len(files) > 1}
    
    # Helper methods
    def _resolve_path(self, path: Union[str, Path]) -> Path:
        """Resolve path relative to base directory"""
        if isinstance(path, str):
            path = Path(path)
        
        if path.is_absolute():
            return path
        else:
            return self.base_dir / path
    
    @staticmethod
    def _format_size(size_bytes: int) -> str:
        """Format size in human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    @staticmethod
    def _create_zip_archive(source: Path, archive: Path):
        """Create ZIP archive"""
        with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(source)
                    zipf.write(file_path, arcname)
    
    @staticmethod
    def _create_tar_archive(source: Path, archive: Path):
        """Create TAR archive"""
        with tarfile.open(archive, 'w:gz') as tar:
            tar.add(source, arcname=source.name)
    
    @staticmethod
    def _extract_zip_archive(archive: Path, extract_to: Path):
        """Extract ZIP archive"""
        with zipfile.ZipFile(archive, 'r') as zipf:
            zipf.extractall(extract_to)
    
    @staticmethod
    def _extract_tar_archive(archive: Path, extract_to: Path):
        """Extract TAR archive"""
        with tarfile.open(archive, 'r:*') as tar:
            tar.extractall(extract_to)

# Global file handler instance
file_handler = FileHandler()

# Convenience functions
async def read_json(file_path: Union[str, Path]) -> Any:
    """Read JSON file (convenience function)"""
    return await file_handler.read_json(file_path)

async def write_json(file_path: Union[str, Path], data: Any) -> bool:
    """Write JSON file (convenience function)"""
    return await file_handler.write_json(file_path, data)

async def read_lines(file_path: Union[str, Path]) -> List[str]:
    """Read file lines (convenience function)"""
    return await file_handler.read_lines(file_path)

async def write_lines(file_path: Union[str, Path], lines: List[str]) -> bool:
    """Write lines to file (convenience function)"""
    return await file_handler.write_lines(file_path, lines)

async def backup_database():
    """Create database backup"""
    from config import DATABASE_PATH
    return await file_handler.backup_file(DATABASE_PATH)