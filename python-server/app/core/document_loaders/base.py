# langchain_lite/document_loaders/base.py
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

from ..document import Document

class BaseLoader(ABC):
    """Base class for all document loaders."""
    
    @abstractmethod
    def load(self) -> List[Document]:
        """Load documents from the source."""
        pass