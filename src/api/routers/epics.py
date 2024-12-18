from fastapi import APIRouter, HTTPException, Query, Path
from typing import List, Optional
import logging
import os
from datetime import datetime

from src.models.epic import Epic, EpicSource, ExternalReference
from src.services.epic_service import EpicService
from src.agents.epic_generator import EpicGenerator

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter()
epic_service = EpicService()
epic_generator = EpicGenerator()

@router.post("/", response_model=str)
async def create_epic(epic: Epic):
    """Create a new epic"""
    try:
        # Validate required fields
        if not epic.title or not epic.description:
            raise HTTPException(
                status_code=400,
                detail="Title and description are required fields"
            )
        
        # Validate user stories
        if epic.user_stories:
            for story in epic.user_stories:
                if not all([story.role, story.action, story.benefit]):
                    raise HTTPException(
                        status_code=400,
                        detail="All user stories must have role, action, and benefit"
                    )

        logger.info(f"[API] Recebida requisição para criar épico: {epic.title}")
        epic_id = await epic_service.create_epic(epic)
        logger.info(f"[API] Épico criado com sucesso. ID: {epic_id}")
        return epic_id
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao criar épico: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/", response_model=List[Epic])
async def list_epics(
    skip: int = Query(0, ge=0, description="Number of epics to skip"),
    limit: int = Query(10, ge=1, le=100, description="Number of epics to return"),
    status: Optional[str] = Query(
        None,
        regex="^(draft|in_progress|completed|archived)$",
        description="Filter by status"
    ),
    tags: Optional[List[str]] = Query(
        None,
        max_items=10,
        description="Filter by tags"
    )
):
    """List epics with optional filters"""
    try:
        # Validate tags length if provided
        if tags:
            if any(len(tag) > 50 for tag in tags):
                raise HTTPException(
                    status_code=400,
                    detail="Tags must not exceed 50 characters"
                )

        logger.info(f"[API] Listando épicos. Skip: {skip}, Limit: {limit}, Status: {status}, Tags: {tags}")
        epics = await epic_service.list_epics(skip, limit, status, tags)
        logger.info(f"[API] {len(epics)} épicos retornados")
        return epics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao listar épicos: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{epic_id}", response_model=Epic)
async def get_epic(epic_id: str = Path(..., description="ID of the epic to get")):
    """Get an epic by ID"""
    try:
        logger.info(f"[API] Buscando épico: {epic_id}")
        epic = await epic_service.get_epic(epic_id)
        if not epic:
            logger.warning(f"[API] Épico não encontrado: {epic_id}")
            raise HTTPException(status_code=404, detail="Epic not found")
        logger.info(f"[API] Épico encontrado: {epic.title}")
        return epic
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao buscar épico {epic_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{epic_id}", response_model=Epic)
async def update_epic(epic: Epic, epic_id: str = Path(..., description="ID of the epic to update")):
    """Update an epic"""
    try:
        # Validate epic_id format
        if not epic_id or len(epic_id) < 3:
            raise HTTPException(
                status_code=400,
                detail="Invalid epic ID format"
            )
            
        # Validate required fields
        if not epic.title or not epic.description:
            raise HTTPException(
                status_code=400,
                detail="Title and description are required fields"
            )
        
        # Validate user stories
        if epic.user_stories:
            for story in epic.user_stories:
                if not all([story.role, story.action, story.benefit]):
                    raise HTTPException(
                        status_code=400,
                        detail="All user stories must have role, action, and benefit"
                    )

        logger.info(f"[API] Atualizando épico: {epic_id}")
        success = await epic_service.update_epic(epic_id, epic)
        if not success:
            logger.warning(f"[API] Épico não encontrado para atualização: {epic_id}")
            raise HTTPException(status_code=404, detail="Epic not found")
        logger.info(f"[API] Épico atualizado com sucesso: {epic_id}")
        return epic
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao atualizar épico {epic_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{epic_id}", response_model=bool)
async def delete_epic(epic_id: str = Path(..., description="ID of the epic to delete")):
    """Delete an epic"""
    try:
        logger.info(f"[API] Removendo épico: {epic_id}")
        success = await epic_service.delete_epic(epic_id)
        if not success:
            logger.warning(f"[API] Épico não encontrado para remoção: {epic_id}")
            raise HTTPException(status_code=404, detail="Epic not found")
        logger.info(f"[API] Épico removido com sucesso: {epic_id}")
        return success
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao remover épico {epic_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/search/similar", response_model=List[Epic])
async def search_similar_epics(
    text: str = Query(..., description="Text to search for similar epics"),
    limit: int = Query(5, description="Number of similar epics to return"),
    min_similarity: float = Query(0.7, description="Minimum similarity score")
):
    """Search for similar epics"""
    try:
        logger.info(f"[API] Buscando épicos similares. Texto: '{text[:50]}...'")
        epics = await epic_service.search_similar_epics(text, limit, min_similarity)
        logger.info(f"[API] {len(epics)} épicos similares encontrados")
        return epics
    except Exception as e:
        logger.error(f"[API] Erro na busca por épicos similares: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{epic_id}/external-reference", response_model=bool)
async def link_external_reference(
    epic_id: str = Path(..., description="ID of the epic to link"),
    source: EpicSource = Query(..., description="Source of the external reference"),
    external_id: str = Query(..., description="ID in the external system"),
    external_url: Optional[str] = Query(None, description="URL to the external system"),
    status: str = Query(..., description="Status of the external reference")
):
    """Link an epic to an external reference"""
    try:
        logger.info(f"[API] Vinculando épico {epic_id} a referência externa: {source.value} {external_id}")
        ref = ExternalReference(
            source=source,
            external_id=external_id,
            external_url=external_url,
            status=status,
            linked_at=datetime.utcnow()
        )
        success = await epic_service.link_external_reference(epic_id, ref)
        if not success:
            logger.warning(f"[API] Épico não encontrado para vinculação: {epic_id}")
            raise HTTPException(status_code=404, detail="Epic not found")
        logger.info(f"[API] Épico vinculado com sucesso: {epic_id}")
        return success
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao vincular épico {epic_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{epic_id}/external-reference/{source}/{external_id}", response_model=bool)
async def update_external_reference_status(
    epic_id: str = Path(..., description="ID of the epic to update"),
    source: EpicSource = Path(..., description="Source of the external reference"),
    external_id: str = Path(..., description="ID in the external system"),
    status: str = Query(..., description="New status for the external reference")
):
    """Update the status of an external reference"""
    try:
        logger.info(f"[API] Atualizando status da referência externa. Épico: {epic_id}, Source: {source.value}, ID: {external_id}")
        success = await epic_service.update_external_reference(
            epic_id,
            source,
            external_id,
            status
        )
        if not success:
            logger.warning(f"[API] Referência externa não encontrada: {epic_id}/{source.value}/{external_id}")
            raise HTTPException(status_code=404, detail="External reference not found")
        logger.info(f"[API] Status da referência externa atualizado com sucesso")
        return success
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro ao atualizar status da referência externa: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/generate", response_model=str)
async def generate_epic(
    idea: str = Query(
        ...,
        min_length=10,
        max_length=1000,
        description="The idea to generate an epic from"
    )
):
    """Generate a new epic from an idea using AI and save it to the database"""
    try:
        # Validate idea content
        if not idea.strip():
            raise HTTPException(
                status_code=400,
                detail="Idea cannot be empty or contain only whitespace"
            )

        # Check for OpenAI API key
        if not os.environ.get('OPENAI_API_KEY'):
            raise HTTPException(
                status_code=500,
                detail="OpenAI API key not configured"
            )

        logger.info(f"[API] Gerando épico a partir da ideia: {idea[:100]}...")
        try:
            epic = epic_generator.generate(idea)
            epic_id = await epic_service.create_epic(epic)
            logger.info(f"[API] Épico gerado e salvo com sucesso. ID: {epic_id}")
            return epic_id
        except ValueError as ve:
            logger.error(f"[API] Erro de validação ao gerar épico: {str(ve)}")
            raise HTTPException(status_code=400, detail=str(ve))
        except Exception as e:
            logger.error(f"[API] Erro ao gerar épico: {str(e)}")
            raise HTTPException(status_code=500, detail="Failed to generate epic")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[API] Erro inesperado ao gerar épico: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
