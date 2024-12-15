from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from src.models.epic import Epic, UserStory
import os

class EpicData(BaseModel):
    title: str = Field(description="Título do épico")
    description: str = Field(description="Descrição detalhada do épico")
    objectives: List[str] = Field(description="Lista de objetivos do épico")
    user_stories: List[Dict[str, str]] = Field(
        description="Lista de user stories com role, action e benefit"
    )
    acceptance_criteria: List[str] = Field(description="Lista de critérios de aceitação")
    success_metrics: List[str] = Field(description="Lista de métricas de sucesso")

class EpicGenerator:
    def __init__(self):
        # Obtém a chave API do ambiente
        openai_api_key = os.environ.get('OPENAI_API_KEY')
        if not openai_api_key:
            raise ValueError("OPENAI_API_KEY não encontrada nas variáveis de ambiente")
            
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.7,
            openai_api_key=openai_api_key
        )
        self.parser = PydanticOutputParser(pydantic_object=EpicData)
        self._setup_prompt()

    def _setup_prompt(self):
        template = """
        Você é um especialista em análise de requisitos e metodologias ágeis.
        Sua tarefa é criar um épico profissional e detalhado baseado na seguinte ideia:

        {idea}

        Siga estas diretrizes específicas:

        1. Título:
           - Deve ser claro, conciso e representar o objetivo principal
           - Comece com um verbo no infinitivo (ex: "Implementar", "Desenvolver", "Criar")

        2. Descrição:
           - Forneça uma visão geral clara do que precisa ser alcançado
           - Explique o valor para o negócio e os usuários
           - Mantenha entre 3-5 frases

        3. Objetivos:
           - Liste 3-5 objetivos específicos e mensuráveis
           - Cada objetivo deve começar com um verbo no infinitivo
           - Foque em resultados, não em tarefas

        4. User Stories:
           - Crie 3-5 user stories essenciais
           - Use EXATAMENTE o formato: "Como [papel], eu quero [ação] para que [benefício]"
           - NÃO repita "eu quero" na parte da ação
           - Exemplo correto: "Como desenvolvedor, eu quero implementar testes automatizados para que bugs sejam detectados rapidamente"
           - Exemplo incorreto: "Como desenvolvedor, eu quero eu quero implementar testes para que bugs sejam detectados"
           - Certifique-se que cada história agregue valor ao usuário

        5. Critérios de Aceitação:
           - Liste 3-5 critérios específicos e verificáveis
           - Cada critério deve ser claro e testável
           - Use linguagem objetiva

        6. Métricas de Sucesso:
           - Defina 2-4 métricas quantificáveis
           - Inclua números ou percentuais específicos
           - Foque em resultados mensuráveis

        {format_instructions}
        """
        
        self.prompt = ChatPromptTemplate.from_template(
            template=template,
            partial_variables={
                "format_instructions": self.parser.get_format_instructions()
            }
        )

    def generate(self, idea: str) -> Epic:
        """Generate an epic from an idea."""
        try:
            # Generate content using LangChain
            messages = self.prompt.format_messages(idea=idea)
            response = self.llm.invoke(messages)
            
            # Parse the response
            data = self.parser.parse(response.content)
            
            # Convert user stories dict to UserStory objects
            user_stories = [
                UserStory(
                    role=story["role"],
                    action=story["action"],
                    benefit=story["benefit"]
                )
                for story in data.user_stories
            ]
            
            # Create and return Epic object
            return Epic(
                title=data.title,
                description=data.description,
                objectives=data.objectives,
                user_stories=user_stories,
                acceptance_criteria=data.acceptance_criteria,
                success_metrics=data.success_metrics
            )
            
        except Exception as e:
            raise Exception(f"Erro ao gerar épico: {str(e)}")
