from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class UserStory(BaseModel):
    role: str = Field(..., description="The user role in the story")
    action: str = Field(..., description="What the user wants to do")
    benefit: str = Field(..., description="The benefit or value the user gets")

class Epic(BaseModel):
    id: Optional[str] = None
    title: str = Field(..., description="Title of the epic")
    description: str = Field(..., description="Detailed description of the epic")
    user_stories: List[UserStory] = Field(default_factory=list, description="List of user stories in this epic")
    acceptance_criteria: Optional[List[str]] = Field(default=None, description="Acceptance criteria for the epic")
    external_references: Optional[List[str]] = None
    embedding: Optional[List[float]] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    status: str = Field("draft", description="Status of the epic")
    priority: str = Field("medium", description="Priority of the epic")
    story_points: Optional[int] = Field(None, description="Story points estimation")
    tags: Optional[List[str]] = Field(default=None, description="Tags for categorizing the epic")
