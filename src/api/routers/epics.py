from fastapi import APIRouter, HTTPException, Query, Depends
from typing import List, Optional
from src.models.epic import Epic
from src.api.services.epics import EpicService
from src.config.database import get_epic_collection
from motor.motor_asyncio import AsyncIOMotorCollection
from src.agents.epic_generator import EpicGenerator

epic_generator = EpicGenerator()

router = APIRouter()

async def get_epic_service(
    collection: AsyncIOMotorCollection = Depends(get_epic_collection)
) -> EpicService:
    return EpicService(collection)

@router.post("/", response_model=Epic)
async def create_epic(
    idea: str = Query(..., min_length=10, description="Ideia para gerar o épico"),
    service: EpicService = Depends(get_epic_service)
) -> Epic:
    """
    Cria um novo épico a partir de uma ideia usando IA
    - idea: descrição da ideia para gerar o épico (mínimo 10 caracteres)
    """
    try:
        # Gera o épico usando IA
        epic = epic_generator.generate(idea)
        
        # Persiste o épico no banco
        epic_id = await service.create_epic(epic)
        epic.id = epic_id
        return epic
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao gerar épico: {str(e)}"
        )

@router.get("/{epic_id}", response_model=Epic)
async def get_epic(
    epic_id: str,
    service: EpicService = Depends(get_epic_service)
) -> Epic:
    """
    Retorna um épico específico por ID
    - epic_id: ID do épico a ser retornado
    """
    epic = await service.get_epic(epic_id)
    if not epic:
        raise HTTPException(
            status_code=404,
            detail="Épico não encontrado"
        )
    return epic

@router.put("/{epic_id}", response_model=Epic)
async def update_epic(
    epic_id: str,
    epic_update: Epic,
    service: EpicService = Depends(get_epic_service)
) -> Epic:
    """
    Atualiza um épico existente
    - epic_id: ID do épico a ser atualizado
    - epic_update: Dados atualizados do épico
    """
    success = await service.update_epic(epic_id, epic_update)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Épico não encontrado"
        )
    return await service.get_epic(epic_id)

@router.delete("/{epic_id}")
async def delete_epic(
    epic_id: str,
    service: EpicService = Depends(get_epic_service)
) -> dict:
    """
    Remove um épico
    - epic_id: ID do épico a ser removido
    """
    success = await service.delete_epic(epic_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail="Épico não encontrado"
        )
    return {"message": "Épico removido com sucesso"}

@router.get("/", response_model=List[Epic])
async def list_epics(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    status: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|updated_at|title|priority)$"),
    sort_order: int = Query(-1, ge=-1, le=1),
    service: EpicService = Depends(get_epic_service)
) -> List[Epic]:
    """
    Lista épicos com paginação e filtros
    - skip: número de registros para pular
    - limit: número máximo de registros para retornar
    - status: filtrar por status
    - tags: filtrar por tags
    - sort_by: campo para ordenação
    - sort_order: direção da ordenação (-1 para descendente, 1 para ascendente)
    """
    return await service.list_epics(
        skip=skip,
        limit=limit,
        status=status,
        tags=tags,
        sort_by=sort_by,
        sort_order=sort_order
    )

@router.get("/search/similar", response_model=List[Epic])
async def search_similar_epics(
    text: str = Query(..., min_length=3),
    limit: int = Query(5, ge=1, le=20),
    threshold: float = Query(0.5, ge=0, le=1),
    service: EpicService = Depends(get_epic_service)
) -> List[Epic]:
    """
    Busca épicos similares baseado em texto
    - text: texto para busca
    - limit: número máximo de resultados
    - threshold: limiar de similaridade (0-1)
    """
    return await service.search_similar_epics(
        text=text,
        limit=limit,
        threshold=threshold
    )
