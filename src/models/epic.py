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
    external_id: str = Field(..., description="ID do epic no sistema externo")
    url: str = Field(..., description="URL para o epic no sistema externo")
    status: str = Field(..., description="Status do epic no sistema externo")
    last_sync: datetime = Field(..., description="Última sincronização com o sistema externo")

class UserStory(BaseModel):
    role: str = Field(..., description="O papel do usuário na história")
    action: str = Field(..., description="O que o usuário quer fazer")
    benefit: str = Field(..., description="O benefício ou valor que o usuário obtém")
    external_references: Optional[List[ExternalReference]] = Field(None, description="Referências externas da história")

class Epic(BaseModel):
    id: Optional[str] = Field(None, description="ID único do epic")
    title: str = Field(..., description="Título do epic")
    description: str = Field(..., description="Descrição detalhada do epic")
    objectives: List[str] = Field(..., description="Lista de objetivos deste epic")
    user_stories: List[UserStory] = Field(..., description="Lista de histórias de usuário neste epic")
    acceptance_criteria: List[str] = Field(..., description="Critérios de aceitação do epic")
    success_metrics: List[str] = Field(..., description="Métricas de sucesso do epic")
    external_references: Optional[List[ExternalReference]] = Field(None, description="Referências externas do epic")
    embedding: Optional[List[float]] = Field(None, description="Embedding do epic para busca semântica")
    tags: List[str] = Field(default_factory=list, description="Tags para categorização do epic")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Data de criação")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Data da última atualização")
    status: str = Field("draft", description="Status do epic")
    priority: str = Field("medium", description="Prioridade do epic")

    def to_markdown(self) -> str:
        """Convert the epic to markdown format."""
        md = f"# {self.title}\n\n"
        md += f"## Descrição\n{self.description}\n\n"
        
        md += "## Objetivos\n"
        for obj in self.objectives:
            md += f"- {obj}\n"
        md += "\n"
        
        md += "## Histórias de Usuário\n"
        for story in self.user_stories:
            md += f"- Como {story.role}, quero {story.action} para {story.benefit}\n"
        md += "\n"
        
        md += "## Critérios de Aceitação\n"
        for ac in self.acceptance_criteria:
            md += f"- {ac}\n"
        md += "\n"
        
        md += "## Métricas de Sucesso\n"
        for metric in self.success_metrics:
            md += f"- {metric}\n"
        md += "\n"
        
        if self.tags:
            md += "## Tags\n"
            md += ", ".join(self.tags)
            md += "\n\n"
        
        return md

    def to_embedding_text(self) -> str:
        """Convert epic to text format for embedding generation."""
        text = f"{self.title}. {self.description}"
        
        text += " Objetivos: "
        text += "; ".join(self.objectives)
        
        text += " Histórias: "
        stories = [f"{s.role} quer {s.action} para {s.benefit}" for s in self.user_stories]
        text += "; ".join(stories)
        
        text += " Critérios: "
        text += "; ".join(self.acceptance_criteria)
        
        text += " Métricas: "
        text += "; ".join(self.success_metrics)
        
        if self.tags:
            text += " Tags: "
            text += ", ".join(self.tags)
        
        return text
