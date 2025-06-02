# langchain_lite/document_loaders/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

# Import Document từ module cha
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from document import Document

class BaseLoader(ABC):
    """Base class for all document loaders."""
    
    @abstractmethod
    def load(self) -> List[Document]:
        """Load documents from the source."""
        pass