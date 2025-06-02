from typing import List, Dict, Any, Optional, Callable, Union
import os
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModel
from tqdm import tqdm

from .base import Embeddings

class HuggingFaceEmbedding(Embeddings):
    """HuggingFace embedding model implementation."""
    
    def __init__(
        self,
        model_name: str,
        normalize: bool = True,
        cache_folder: Optional[str] = None,
        device: Optional[str] = None,
        trust_remote_code: bool = False,
        batch_size: int = 32,
        show_progress: bool = True
    ):
        """Initialize with model name and parameters."""
        self.model_name = model_name
        self.normalize = normalize
        self.cache_folder = cache_folder
        self.trust_remote_code = trust_remote_code
        self.batch_size = batch_size
        self.show_progress = show_progress
        
        # Determine device
        if device == "auto":
            self.device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
        else:
            self.device = device or "cpu"
            
        print(f"Loading embedding model {model_name} on {self.device}...")
        
        # Set cache directory if provided
        cache_kwargs = {}
        if self.cache_folder:
            os.makedirs(self.cache_folder, exist_ok=True)
            cache_kwargs["cache_dir"] = self.cache_folder
            
        # Load tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            self.model_name,
            trust_remote_code=self.trust_remote_code,
            **cache_kwargs
        )
        
        # Load model
        self.model = AutoModel.from_pretrained(
            self.model_name,
            trust_remote_code=self.trust_remote_code,
            **cache_kwargs
        )
        
        # Move model to device and set to eval mode
        self.model.to(self.device)
        self.model.eval()
        
        print(f"Embedding model loaded successfully!")
            
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Get embeddings for a list of texts."""
        all_embeddings = []
        
        # Process in batches
        for i in tqdm(range(0, len(texts), self.batch_size), 
                     desc="Generating embeddings",
                     disable=not self.show_progress):
            batch_texts = texts[i:i + self.batch_size]
            
            # Tokenize texts
            encoded_input = self.tokenizer(
                batch_texts,
                padding=True,
                truncation=True,
                return_tensors="pt"
            )
            
            # Move to device
            encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
            
            # Get embeddings
            with torch.no_grad():
                model_output = self.model(**encoded_input)
                embeddings = model_output.last_hidden_state.mean(dim=1)
                
                if self.normalize:
                    embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                    
            # Convert to list and extend
            batch_embeddings = embeddings.cpu().numpy().tolist()
            all_embeddings.extend(batch_embeddings)
                
        return all_embeddings
        
    def embed_query(self, text: str) -> List[float]:
        """Get embedding for a single text."""
        # Tokenize text
        encoded_input = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            return_tensors="pt"
        )
        
        # Move to device
        encoded_input = {k: v.to(self.device) for k, v in encoded_input.items()}
        
        # Get embedding
        with torch.no_grad():
            model_output = self.model(**encoded_input)
            embedding = model_output.last_hidden_state.mean(dim=1)
            
            if self.normalize:
                embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
                
        # Convert to list
        return embedding.cpu().numpy().tolist()[0] 