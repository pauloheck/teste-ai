from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from typing import List, Optional
from pydantic import BaseModel
from src.agents.epic_generator import EpicGenerator

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class EpicRequest(BaseModel):
    title: str
    description: str
    domain: Optional[str] = None
    methodology: Optional[str] = None

class EpicResponse(BaseModel):
    id: str
    title: str
    description: str
    stories: List[dict]
    status: str

@router.post("/", response_model=EpicResponse)
async def create_epic(
    epic_request: EpicRequest,
    token: str = Depends(oauth2_scheme)
):
    try:
        generator = EpicGenerator()
        epic = await generator.generate_epic(
            title=epic_request.title,
            description=epic_request.description,
            domain=epic_request.domain,
            methodology=epic_request.methodology
        )
        return epic
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/", response_model=List[EpicResponse])
async def list_epics(
    token: str = Depends(oauth2_scheme),
    skip: int = 0,
    limit: int = 10
):
    try:
        # TODO: Implementar listagem de épicos
        return []
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{epic_id}", response_model=EpicResponse)
async def get_epic(
    epic_id: str,
    token: str = Depends(oauth2_scheme)
):
    try:
        # TODO: Implementar busca de épico por ID
        raise HTTPException(status_code=404, detail="Epic not found")
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/{epic_id}/export")
async def export_epic(
    epic_id: str,
    format: str = "json",
    token: str = Depends(oauth2_scheme)
):
    try:
        # TODO: Implementar exportação de épico
        return {
            "epic_id": epic_id,
            "format": format,
            "status": "exported",
            "download_url": None
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
