"""
Models for API and service tracking
"""
from datetime import datetime
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum
from bson import ObjectId

class TrackingType(str, Enum):
    """Types of tracking records"""
    API_REQUEST = "api_request"
    AZURE_OPENAI = "azure_openai"

class APITracking(BaseModel):
    """Base model for tracking"""
    id: str = Field(default_factory=lambda: str(ObjectId()))
    tracking_type: TrackingType
    operation: str
    model: Optional[str] = None
    status: str
    duration_ms: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    error_message: Optional[str] = None
    estimated_cost: Optional[float] = 0.0
    prompt_tokens: Optional[int] = 0
    completion_tokens: Optional[int] = 0
    metadata: Optional[Dict[str, Any]] = None
    
    # API specific fields
    endpoint: Optional[str] = None
    method: Optional[str] = None
    request_headers: Optional[Dict[str, str]] = None
    request_body: Optional[Dict[str, Any]] = None
    response_status: Optional[int] = None
    response_body: Optional[Dict[str, Any]] = None
    
    # Database specific fields
    collection: Optional[str] = None
    query: Optional[Dict[str, Any]] = None
    affected_documents: Optional[int] = None
    
    # Analysis fields
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            ObjectId: lambda v: str(v)
        }
        allow_population_by_field_name = True
