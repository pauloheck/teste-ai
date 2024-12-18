from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class UserStory(BaseModel):
    id: Optional[str] = None
    role: str = Field(..., description="The user role in the story")
    action: str = Field(..., description="What the user wants to do")
    benefit: str = Field(..., description="The benefit or value the user gets")
    epic_id: Optional[str] = Field(None, description="ID of the associated epic")
    external_references: Optional[List[str]] = None
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = Field("draft", description="Status of the user story")
    priority: str = Field("medium", description="Priority of the user story")
    acceptance_criteria: Optional[List[str]] = Field(default=None, description="Acceptance criteria for the story")
    story_points: Optional[int] = Field(None, description="Story points estimation")
    tags: Optional[List[str]] = Field(default=None, description="Tags for categorizing the story")
