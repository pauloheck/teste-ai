"""Utility for chunking text into smaller pieces."""
from typing import List
import logging

logger = logging.getLogger(__name__)

class TextChunker:
    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        """Initialize text chunker.
        
        Args:
            chunk_size: Maximum size of each chunk
            overlap: Number of characters to overlap between chunks
        """
        self.chunk_size = chunk_size
        self.overlap = overlap
        
    def chunk_text(self, text: str) -> List[str]:
        """Split text into overlapping chunks.
        
        Args:
            text: Text to split into chunks
            
        Returns:
            List of text chunks
        """
        if not text:
            return []
            
        chunks = []
        start = 0
        text_length = len(text)
        
        while start < text_length:
            end = start + self.chunk_size
            
            # Adjust end to not split words
            if end < text_length:
                # Look for the last space before the end
                while end > start and text[end] != ' ':
                    end -= 1
                if end == start:  # No space found
                    end = start + self.chunk_size  # Just cut at max length
            
            chunk = text[start:end].strip()
            if chunk:  # Only add non-empty chunks
                chunks.append(chunk)
                logger.debug(f"Created chunk of size {len(chunk)}")
            
            # Move start position for next chunk, accounting for overlap
            start = end - self.overlap
            
        logger.info(f"Split text into {len(chunks)} chunks")
        return chunks
        
    def chunk_documents(self, documents: List[dict], text_field: str) -> List[dict]:
        """Split documents into chunks based on a text field.
        
        Args:
            documents: List of document dictionaries
            text_field: Field containing text to chunk
            
        Returns:
            List of chunked documents with additional metadata
        """
        chunked_docs = []
        
        for doc in documents:
            if text_field not in doc:
                logger.warning(f"Document missing {text_field} field, skipping")
                continue
                
            text = doc[text_field]
            chunks = self.chunk_text(text)
            
            for i, chunk in enumerate(chunks):
                # Create new doc with chunk and metadata
                chunked_doc = doc.copy()
                chunked_doc[text_field] = chunk
                chunked_doc['chunk_metadata'] = {
                    'chunk_index': i,
                    'total_chunks': len(chunks),
                    'original_length': len(text),
                    'chunk_length': len(chunk)
                }
                chunked_docs.append(chunked_doc)
                
        return chunked_docs
