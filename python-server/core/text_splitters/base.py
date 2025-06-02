from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional, Callable

# Import Document từ module cha
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from document import Document

class TextSplitter(ABC):
    """Base class for text splitters."""
    
    @abstractmethod
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split the documents."""
        pass
        
    @abstractmethod
    def split_text(self, text: str) -> List[str]:
        """Split the text."""
        pass 