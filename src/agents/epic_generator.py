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
           - Liste 4-6 objetivos específicos e mensuráveis
           - Comece cada objetivo com um verbo no infinitivo

        4. User Stories:
           - Crie 4-6 user stories no formato:
           {{"role": "papel do usuário", "action": "ação desejada", "benefit": "benefício esperado"}}
           - Não inclua "Como", "eu quero" ou "para que" nas propriedades individuais
           - Exemplo correto:
             {{"role": "desenvolvedor", "action": "configurar integrações", "benefit": "facilitar a conexão com outros sistemas"}}

        5. Critérios de Aceitação:
           - Liste 4-6 critérios específicos e verificáveis
           - Comece cada critério com "O sistema deve" ou similar

        6. Métricas de Sucesso:
           - Liste 3-5 métricas quantificáveis
           - Inclua números ou percentuais específicos

        {format_instructions}
        """
        
        self.prompt = ChatPromptTemplate.from_template(
            template,
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
            
            # Convert user stories dict to UserStory objects with proper error handling
            user_stories = []
            for story in data.user_stories:
                try:
                    user_stories.append(
                        UserStory(
                            role=story.get("role", "usuário"),  # default to "usuário" if role is missing
                            action=story.get("action", "realizar uma ação"),  # default action if missing
                            benefit=story.get("benefit", "obter um benefício")  # default benefit if missing
                        )
                    )
                except Exception as story_error:
                    print(f"Erro ao processar user story: {story_error}. Story: {story}")
                    continue
            
            # Create and return Epic object
            return Epic(
                title=data.title,
                description=data.description,
                objectives=data.objectives,
                user_stories=user_stories,
                acceptance_criteria=data.acceptance_criteria,
                success_metrics=data.success_metrics,
                tags=[]  # Initialize with empty tags
            )
            
        except Exception as e:
            raise Exception(f"Erro ao gerar épico: {str(e)}")
