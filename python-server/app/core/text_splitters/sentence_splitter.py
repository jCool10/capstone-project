from typing import List, Dict, Any, Optional, Callable, Union
import re

from .base import TextSplitter
from ..document import Document

class SentenceSplitter(TextSplitter):
    """Split text into sentences."""
    
    def __init__(
        self,
        separator: str = ".",
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        tokenizer: Optional[Callable[[str], List[int]]] = None,
        paragraph_separator: str = "\n\n",
        secondary_chunking_regex: Optional[str] = None,
        keep_separator: bool = True,
        strip_whitespace: bool = True
    ):
        """Initialize with parameters."""
        self.separator = separator
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.tokenizer = tokenizer
        self.paragraph_separator = paragraph_separator
        self.secondary_chunking_regex = secondary_chunking_regex
        self.keep_separator = keep_separator
        self.strip_whitespace = strip_whitespace
        
    def _get_chunk_len(self, text: str) -> int:
        """Get the length of a chunk of text."""
        if self.tokenizer:
            # Count tokens if a tokenizer is provided
            return len(self.tokenizer(text))
        # Otherwise count characters
        return len(text)
        
    def split_text(self, text: str) -> List[str]:
        """Split text into chunks."""
        # Step 1: Split by paragraphs first
        if self.paragraph_separator and self.paragraph_separator in text:
            paragraphs = text.split(self.paragraph_separator)
        else:
            paragraphs = [text]
            
        # Step 2: Split paragraphs by sentence separator
        sentences = []
        for paragraph in paragraphs:
            if self.secondary_chunking_regex:
                # Use regex for more complex sentence splitting
                pattern = self.secondary_chunking_regex
                splits = re.split(pattern, paragraph)
                for split in splits:
                    if split.strip():  # Skip empty splits
                        if self.keep_separator and self.separator:
                            sentences.append(split + self.separator)
                        else:
                            sentences.append(split)
            else:
                # Use simple separator splitting
                if self.separator:
                    paragraph_sentences = paragraph.split(self.separator)
                    for sent in paragraph_sentences:
                        if sent.strip():  # Skip empty sentences
                            if self.keep_separator:
                                sentences.append(sent + self.separator)
                            else:
                                sentences.append(sent)
                else:
                    # No separator specified, add whole paragraph
                    sentences.append(paragraph)
        
        # Step 3: Create chunks with overlap
        chunks = []
        current_chunk = []
        current_chunk_len = 0
        
        for sentence in sentences:
            sentence_to_add = sentence.strip() if self.strip_whitespace else sentence
            sentence_len = self._get_chunk_len(sentence_to_add)
            
            # If adding this sentence would exceed chunk size and we have content
            if current_chunk_len + sentence_len > self.chunk_size and current_chunk:
                # Add the current chunk to the list
                chunks.append(self.paragraph_separator.join(current_chunk) if self.paragraph_separator else "".join(current_chunk))
                
                # Create overlap for next chunk
                overlap_len = 0
                overlap_chunk = []
                
                # Add sentences from the end of the current chunk until we hit overlap limit
                for sent in reversed(current_chunk):
                    sent_len = self._get_chunk_len(sent)
                    if overlap_len + sent_len <= self.chunk_overlap:
                        overlap_chunk.insert(0, sent)
                        overlap_len += sent_len
                    else:
                        break
                
                # Start new chunk with overlap
                current_chunk = overlap_chunk
                current_chunk_len = overlap_len
            
            # Add the sentence to the current chunk
            current_chunk.append(sentence_to_add)
            current_chunk_len += sentence_len
        
        # Add the last chunk if it exists
        if current_chunk:
            chunks.append(self.paragraph_separator.join(current_chunk) if self.paragraph_separator else "".join(current_chunk))
            
        return chunks
        
    def split_documents(self, documents: List[Document]) -> List[Document]:
        """Split documents into chunks."""
        split_documents = []
        
        for doc in documents:
            text = doc.page_content
            text_splits = self.split_text(text)
            
            for i, split_text in enumerate(text_splits):
                # Create new metadata dict for the split
                new_metadata = {
                    **doc.metadata,
                    "chunk": i,
                    "chunk_size": self.chunk_size,
                    "chunk_overlap": self.chunk_overlap
                }
                
                # Create new document with the split text
                split_doc = Document(
                    page_content=split_text,
                    metadata=new_metadata
                )
                split_documents.append(split_doc)
                
        return split_documents 