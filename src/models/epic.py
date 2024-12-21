from pydantic import BaseModel, Field
from typing import List, Optional
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
    role: str
    action: str
    benefit: str
    external_references: Optional[List[ExternalReference]] = None
    
    def __str__(self) -> str:
        action = self.action.replace("eu quero ", "")
        return f"Como {self.role}, eu quero {action} para que {self.benefit}"

class Epic(BaseModel):
    title: str
    description: str
    objectives: List[str]
    user_stories: List[UserStory]
    acceptance_criteria: List[str]
    success_metrics: List[str]
    external_references: Optional[List[ExternalReference]] = None
    embedding: Optional[List[float]] = None
    tags: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "draft"
    
    def to_markdown(self) -> str:
        """Convert the epic to markdown format."""
        markdown = f"## {self.title}\n\n"
        
        markdown += "### Descrição\n"
        markdown += f"{self.description}\n\n"
        
        markdown += "### Objetivos\n"
        for obj in self.objectives:
            markdown += f"- {obj}\n"
        markdown += "\n"
        
        markdown += "### User Stories\n"
        for story in self.user_stories:
            markdown += f"- {str(story)}\n"
            if story.external_references:
                for ref in story.external_references:
                    markdown += f"  - {ref.source.value}: [{ref.external_id}]({ref.url}) - {ref.status}\n"
        markdown += "\n"
        
        markdown += "### Critérios de Aceitação\n"
        for criteria in self.acceptance_criteria:
            markdown += f"- {criteria}\n"
        markdown += "\n"
        
        markdown += "### Métricas de Sucesso\n"
        for metric in self.success_metrics:
            markdown += f"- {metric}\n"
        markdown += "\n"
        
        if self.external_references:
            markdown += "### Referências Externas\n"
            for ref in self.external_references:
                markdown += f"- {ref.source.value}: [{ref.external_id}]({ref.url}) - {ref.status}\n"
        
        if self.tags:
            markdown += "### Tags\n"
            markdown += ", ".join(self.tags)
            markdown += "\n\n"
        
        return markdown

    def to_embedding_text(self) -> str:
        """Convert epic to text format for embedding generation."""
        text = f"{self.title}\n\n"
        text += f"{self.description}\n\n"
        
        text += "Objetivos:\n"
        text += "\n".join(self.objectives) + "\n\n"
        
        text += "User Stories:\n"
        text += "\n".join(str(story) for story in self.user_stories) + "\n\n"
        
        text += "Critérios de Aceitação:\n"
        text += "\n".join(self.acceptance_criteria) + "\n\n"
        
        text += "Métricas de Sucesso:\n"
        text += "\n".join(self.success_metrics)
        
        return text
