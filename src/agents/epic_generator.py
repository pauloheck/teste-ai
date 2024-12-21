from typing import Dict, List
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
from src.models.epic import Epic, UserStory
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
           - Liste 3-6 objetivos específicos e mensuráveis
           - Comece cada objetivo com um verbo no infinitivo
           - Foque em resultados, não em tarefas

        4. User Stories:
           - Crie 3-5 histórias de usuário essenciais
           - Use o formato "Como [role], quero [action] para [benefit]"
           - Certifique-se que cubram diferentes aspectos do épico

        5. Critérios de Aceitação:
           - Liste 3-5 critérios claros e verificáveis
           - Inclua critérios funcionais e não-funcionais
           - Use linguagem precisa e mensurável

        6. Métricas de Sucesso:
           - Defina 2-4 métricas quantificáveis
           - Inclua métricas de negócio e técnicas
           - Especifique valores ou percentuais alvo

        {format_instructions}
        """
        
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", template)
        ]).partial(format_instructions=self.parser.get_format_instructions())

    def generate(self, idea: str) -> Epic:
        """Generate an epic from an idea."""
        try:
            # Gera o conteúdo usando o LLM
            messages = self.prompt.format_messages(idea=idea)
            logger.info(f"Prompt formatado: {messages}")
            
            response = self.llm.invoke(messages)
            logger.info(f"Resposta do LLM: {response.content}")
            
            epic_data = self.parser.parse(response.content)
            logger.info(f"Dados parseados: {epic_data}")
            
            # Converte as user stories para o formato correto
            user_stories = [
                UserStory(
                    role=story["role"],
                    action=story["action"],
                    benefit=story["benefit"]
                )
                for story in epic_data.user_stories
            ]
            logger.info(f"User stories convertidas: {user_stories}")
            
            # Cria e retorna o Epic
            epic = Epic(
                title=epic_data.title,
                description=epic_data.description,
                objectives=epic_data.objectives,
                user_stories=user_stories,
                acceptance_criteria=epic_data.acceptance_criteria,
                success_metrics=epic_data.success_metrics,
                tags=[],  # Tags podem ser adicionadas posteriormente
                status="draft",
                priority="medium"
            )
            logger.info(f"Epic criado: {epic}")
            return epic
            
        except Exception as e:
            logger.error(f"Erro ao gerar épico: {str(e)}", exc_info=True)
            raise
