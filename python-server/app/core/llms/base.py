from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union

class BaseLLM(ABC):
    """Base class for all language models."""
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text based on a prompt."""
        pass
        
    def invoke(self, prompt: str, **kwargs) -> str:
        """Alias for generate."""
        return self.generate(prompt, **kwargs)
        
    @abstractmethod
    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate text based on multiple prompts."""
        pass
        
    def get_num_tokens(self, text: str) -> int:
        """Get the number of tokens in a text."""
        # Default implementation - override in subclasses
        return len(text.split()) 