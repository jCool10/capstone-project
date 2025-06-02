from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

class Chain(ABC):
    """Base class for chains."""
    
    @abstractmethod
    def run(self, input_data: Union[str, Dict[str, Any]], **kwargs) -> Any:
        """Run the chain on input data."""
        pass
        
    def invoke(self, input_data: Union[str, Dict[str, Any]], **kwargs) -> Any:
        """Alias for run."""
        return self.run(input_data, **kwargs)
        
    def __call__(self, input_data: Union[str, Dict[str, Any]], **kwargs) -> Any:
        """Call the chain on input data."""
        return self.run(input_data, **kwargs) 