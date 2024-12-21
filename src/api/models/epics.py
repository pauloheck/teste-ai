from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from enum import Enum

class EpicSource(str, Enum):
    INTERNAL = "internal"
    JIRA = "jira"
    AZURE_DEVOPS = "azure_devops"

class ExternalReference(BaseModel):
    source: EpicSource
    external_id: str
    url: str
    status: str
    last_sync: datetime

class UserStory(BaseModel):
    role: str = Field(..., description="The user role in the story")
    action: str = Field(..., description="What the user wants to do")
    benefit: str = Field(..., description="The benefit or value the user gets")
    external_references: Optional[List[ExternalReference]] = None

class Epic(BaseModel):
    id: Optional[str] = None
    title: str = Field(..., description="Title of the epic")
    description: str = Field(..., description="Detailed description of the epic")
    objectives: List[str] = Field(..., description="List of objectives for this epic")
    user_stories: List[UserStory] = Field(..., description="List of user stories in this epic")
    acceptance_criteria: List[str] = Field(..., description="Acceptance criteria for the epic")
    success_metrics: List[str] = Field(..., description="Success metrics for the epic")
    external_references: Optional[List[ExternalReference]] = None
    embedding: Optional[List[float]] = None
    tags: List[str] = Field(default_factory=list, description="Tags for categorizing the epic")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = Field("draft", description="Status of the epic")
    priority: str = Field("medium", description="Priority of the epic")
