import os
import glob
from typing import List, Dict, Any, Optional, Union, Callable
from pathlib import Path
from tqdm import tqdm

from .base import BaseLoader
from .file_loader import FileLoader
from ..document import Document

class DirectoryLoader(BaseLoader):
    """Load documents from a directory."""
    
    def __init__(
        self,
        path: str,
        glob_pattern: str = "*.*",
        recursive: bool = False,
        exclude_hidden: bool = True,
        loader_kwargs: Optional[Dict[str, Any]] = None,
        use_multithreading: bool = False,
        max_concurrency: Optional[int] = None,
        show_progress: bool = False
    ):
        """Initialize with directory path."""
        self.path = path
        self.glob_pattern = glob_pattern
        self.recursive = recursive
        self.exclude_hidden = exclude_hidden
        self.loader_kwargs = loader_kwargs or {}
        self.use_multithreading = use_multithreading
        self.max_concurrency = max_concurrency
        self.show_progress = show_progress
        
    def is_hidden(self, path: Path) -> bool:
        """Check if a path is hidden."""
        return any(part.startswith(".") and part not in [".", ".."] for part in path.parts)
        
    def _get_file_paths(self) -> List[str]:
        """Get all file paths in the directory."""
        if self.recursive:
            pattern = os.path.join(self.path, "**", self.glob_pattern)
            file_paths = glob.glob(pattern, recursive=True)
        else:
            pattern = os.path.join(self.path, self.glob_pattern)
            file_paths = glob.glob(pattern)
            
        # Filter out directories and optionally hidden files
        valid_paths = []
        for file_path in file_paths:
            path_obj = Path(file_path)
            if path_obj.is_file() and (not self.exclude_hidden or not self.is_hidden(path_obj)):
                valid_paths.append(file_path)
                
        return valid_paths
        
    def load(self) -> List[Document]:
        """Load documents from the directory."""
        file_paths = self._get_file_paths()
        
        if not file_paths:
            print(f"No files found in {self.path} matching pattern {self.glob_pattern}")
            return []
            
        # Use sequential or multithreaded loading
        if self.use_multithreading and len(file_paths) > 1:
            return self._load_concurrent(file_paths)
        else:
            return self._load_sequential(file_paths)
            
    def _load_sequential(self, file_paths: List[str]) -> List[Document]:
        """Load documents sequentially."""
        documents = []
        file_paths_iter = tqdm(file_paths, desc="Loading files") if self.show_progress else file_paths
        for file_path in file_paths_iter:
            try:
                loader = FileLoader(file_path=file_path, **self.loader_kwargs)
                docs = loader.load()
                documents.extend(docs)
            except Exception as e:
                    print(f"Error loading {file_path}: {e}")
                
        return documents
        
    def _load_concurrent(self, file_paths: List[str]) -> List[Document]:
        """Load documents concurrently."""
        import concurrent.futures
        
        documents = []
        max_workers = self.max_concurrency or min(32, os.cpu_count() + 4)
        
        def load_file(file_path: str) -> List[Document]:
            try:
                loader = FileLoader(file_path=file_path, **self.loader_kwargs)
                return loader.load()
            except Exception as e:
                print(f"Error loading {file_path}: {e}")
                return []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_path = {executor.submit(load_file, path): path for path in file_paths}
            
            if self.show_progress:
                for future in tqdm(concurrent.futures.as_completed(future_to_path), total=len(file_paths), desc="Loading files"):
                    path = future_to_path[future]
                    try:
                        docs = future.result()
                        documents.extend(docs)
                    except Exception as e:
                        print(f"Error loading {path}: {e}")
            else:
                for future in concurrent.futures.as_completed(future_to_path):
                    path = future_to_path[future]
                    try:
                        docs = future.result()
                        documents.extend(docs)
                    except Exception as e:
                        print(f"Error loading {path}: {e}")
                    
        return documents