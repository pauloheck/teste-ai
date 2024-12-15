from dataclasses import dataclass
from typing import List

@dataclass
class UserStory:
    role: str
    action: str
    benefit: str
    
    def __str__(self) -> str:
        # Removendo possíveis duplicações de "eu quero"
        action = self.action.replace("eu quero ", "")
        return f"Como {self.role}, eu quero {action} para que {self.benefit}"

@dataclass
class Epic:
    title: str
    description: str
    objectives: List[str]
    user_stories: List[UserStory]
    acceptance_criteria: List[str]
    success_metrics: List[str]
    
    def to_markdown(self) -> str:
        """Convert the epic to markdown format."""
        markdown = f"## {self.title}\n\n"
        
        markdown += "### Descrição\n"
        markdown += f"{self.description}\n\n"
        
        markdown += "### Objetivos\n"
        for objective in self.objectives:
            markdown += f"- {objective}\n"
        markdown += "\n"
        
        markdown += "### User Stories\n"
        for story in self.user_stories:
            markdown += f"- {str(story)}\n"
        markdown += "\n"
        
        markdown += "### Critérios de Aceitação\n"
        for criterion in self.acceptance_criteria:
            markdown += f"- {criterion}\n"
        markdown += "\n"
        
        markdown += "### Métricas de Sucesso\n"
        for metric in self.success_metrics:
            markdown += f"- {metric}\n"
        
        return markdown
