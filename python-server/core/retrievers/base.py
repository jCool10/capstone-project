from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from document import Document

class BaseRetriever(ABC):
    """Base class for all retrievers."""
    
    @abstractmethod
    def get_relevant_documents(self, query: str, **kwargs) -> List[Document]:
        """Get documents relevant to a query."""
        pass
        
    def invoke(self, query: str, **kwargs) -> List[Document]:
        """Alias for get_relevant_documents."""
        return self.get_relevant_documents(query, **kwargs) 