from datetime import datetime
from typing import Optional, List
from enum import Enum
from pydantic import BaseModel

class ProcessingStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    DUPLICATE = "duplicate"

class DocumentProcessing(BaseModel):
    """Model for tracking document processing status"""
    id: str
    filename: str
    file_path: str
    status: ProcessingStatus
    created_at: datetime
    updated_at: datetime
    error_message: Optional[str] = None
    chunks_processed: Optional[int] = None
    embeddings_stored: Optional[int] = None
    file_hash: Optional[str] = None

class DocumentProcessingResponse(BaseModel):
    """Response model for document processing status"""
    id: str
    filename: str
    status: ProcessingStatus
    message: str
