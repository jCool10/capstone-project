from typing import Any, Dict, List, Optional, Union
import os
import torch
from transformers import (
    AutoTokenizer,
    AutoModelForCausalLM,
    AutoModelForSeq2SeqLM,
    PreTrainedModel,
    PreTrainedTokenizer
)

from .base import BaseLLM

class HuggingFaceLLM(BaseLLM):
    """HuggingFace language model implementation."""
    
    def __init__(
        self,
        model_name: str,
        cache_folder: Optional[str] = None,
        device: Optional[str] = None,
        max_length: int = 2048,
        max_new_tokens: int = 512,
        temperature: float = 0.7,
        top_p: float = 0.9,
        top_k: int = 50,
        num_return_sequences: int = 1,
        trust_remote_code: bool = False,
        torch_dtype: Optional[str] = None
    ):
        """Initialize with model name and parameters."""
        self.model_name = model_name
        self.cache_folder = cache_folder
        self.max_length = max_length
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature
        self.top_p = top_p
        self.top_k = top_k
        self.num_return_sequences = num_return_sequences
        self.trust_remote_code = trust_remote_code
        self.torch_dtype = torch_dtype
        
        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        else:
            self.device = device or "cpu"
            
        # Initialize model and tokenizer
        self._model = None
        self._tokenizer = None
        self._model_type = None
        
    @property
    def model(self) -> PreTrainedModel:
        """Lazy load the model."""
        if self._model is None:
            self._load_model()
        return self._model
        
    @property
    def tokenizer(self) -> PreTrainedTokenizer:
        """Lazy load the tokenizer."""
        if self._tokenizer is None:
            self._load_tokenizer()
        return self._tokenizer
        
    def _load_tokenizer(self):
        """Load the tokenizer."""
        try:
            # Set cache directory if provided
            cache_kwargs = {}
            if self.cache_folder:
                cache_kwargs["cache_dir"] = self.cache_folder
                
            # Load tokenizer
            self._tokenizer = AutoTokenizer.from_pretrained(
                self.model_name,
                trust_remote_code=self.trust_remote_code,
                **cache_kwargs
            )
            
            # Ensure pad token is set
            if self._tokenizer.pad_token is None:
                self._tokenizer.pad_token = self._tokenizer.eos_token
                
        except Exception as e:
            raise ValueError(f"Error loading tokenizer: {e}")
            
    def _load_model(self):
        """Load the model."""
        try:
            # Set cache directory if provided
            cache_kwargs = {}
            if self.cache_folder:
                cache_kwargs["cache_dir"] = self.cache_folder
                
            # Determine model type and load appropriate model
            if "t5" in self.model_name.lower() or "bart" in self.model_name.lower():
                self._model = AutoModelForSeq2SeqLM.from_pretrained(
                    self.model_name,
                    trust_remote_code=self.trust_remote_code,
                    torch_dtype=self._get_torch_dtype(),
                    **cache_kwargs
                )
                self._model_type = "seq2seq"
            else:
                self._model = AutoModelForCausalLM.from_pretrained(
                    self.model_name,
                    trust_remote_code=self.trust_remote_code,
                    torch_dtype=torch.bfloat16,
                    use_cache=True,
                    device_map="auto",
                    **cache_kwargs
                )
                self._model_type = "causal"
                
            # Move model to device
            # self._model.to(self.device)
            
        except Exception as e:
            raise ValueError(f"Error loading model: {e}")
            
    def _get_torch_dtype(self) -> torch.dtype:
        """Get the appropriate torch dtype."""
        if self.torch_dtype == "float16":
            return torch.float16
        elif self.torch_dtype == "bfloat16":
            return torch.bfloat16
        return torch.float32
        
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt."""
        # Tokenize input with padding and attention mask
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_length - self.max_new_tokens,
            return_attention_mask=True
        )
        
        # Move to device
        input_ids = inputs.input_ids.to(self.model.device)
        attention_mask = inputs.attention_mask.to(self.model.device)
        
        # Set generation parameters
        gen_kwargs = {
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "num_return_sequences": self.num_return_sequences,
            "do_sample": True,
            "attention_mask": attention_mask,
            **kwargs
        }
        
        # Generate
        with torch.no_grad():
            if self._model_type == "seq2seq":
                outputs = self.model.generate(
                    input_ids=input_ids,
                    **gen_kwargs
                )
            else:
                outputs = self.model.generate(
                    input_ids=input_ids,
                    pad_token_id=self.tokenizer.pad_token_id,
                    **gen_kwargs
                )
                
        # Decode and return
        return self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
    def batch_generate(self, prompts: List[str], **kwargs) -> List[str]:
        """Generate text based on multiple prompts."""
        # Tokenize inputs with padding and attention mask
        batch_inputs = self.tokenizer(
            prompts,
            return_tensors="pt",
            padding=True,
            truncation=True,
            max_length=self.max_length - self.max_new_tokens,
            return_attention_mask=True
        )
        
        # Move to device
        input_ids = batch_inputs.input_ids.to(self.model.device)
        attention_mask = batch_inputs.attention_mask.to(self.model.device)
        
        # Set generation parameters
        gen_kwargs = {
            "max_new_tokens": self.max_new_tokens,
            "temperature": self.temperature,
            "top_p": self.top_p,
            "top_k": self.top_k,
            "num_return_sequences": self.num_return_sequences,
            "do_sample": True,
            "attention_mask": attention_mask,
            **kwargs
        }
        
        # Generate
        with torch.no_grad():
            if self._model_type == "seq2seq":
                outputs = self.model.generate(
                    input_ids=input_ids,
                    **gen_kwargs
                )
            else:
                outputs = self.model.generate(
                    input_ids=input_ids,
                    pad_token_id=self.tokenizer.pad_token_id,
                    **gen_kwargs
                )
                
        # Decode outputs
        results = []
        for i, output_id in enumerate(outputs):
            input_length = len(batch_inputs.input_ids[i])
            output_text = self.tokenizer.decode(
                output_id[input_length:],
                skip_special_tokens=True
            )
            results.append(output_text)
            
        return results
        
    def get_num_tokens(self, text: str) -> int:
        """Get the number of tokens in a text."""
        return len(self.tokenizer.encode(text)) 