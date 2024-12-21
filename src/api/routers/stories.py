from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorCollection
import logging

from src.models.epic import UserStory
from src.api.services.stories import StoryService
from src.config.database import get_collection
from src.config import OPENAI_API_KEY
from src.api.services.epics import EpicService

logger = logging.getLogger(__name__)
router = APIRouter()  

async def get_story_service() -> StoryService:
    collection: AsyncIOMotorCollection = await get_collection("stories")
    return StoryService(collection)

async def get_epic_service() -> EpicService:
    collection: AsyncIOMotorCollection = await get_collection("epics")
    return EpicService(collection)

@router.post("/", response_model=UserStory)
async def create_story(
    story: UserStory,
    service: StoryService = Depends(get_story_service)
) -> UserStory:
    """Create a new user story"""
    if not story.role or not story.action or not story.benefit:
        raise HTTPException(
            status_code=400,
            detail="Story must include role, action, and benefit"
        )
    return await service.create_story(story)

@router.get("/{story_id}", response_model=UserStory)
async def get_story(
    story_id: str,
    service: StoryService = Depends(get_story_service)
) -> UserStory:
    """Get a specific user story by ID"""
    story = await service.get_story(story_id)
    if not story:
        raise HTTPException(status_code=404, detail="Story not found")
    return story

@router.put("/{story_id}", response_model=UserStory)
async def update_story(
    story_id: str,
    story_update: UserStory,
    service: StoryService = Depends(get_story_service)
) -> UserStory:
    """Update an existing user story"""
    if not story_update.role or not story_update.action or not story_update.benefit:
        raise HTTPException(
            status_code=400,
            detail="Story must include role, action, and benefit"
        )
    
    updated_story = await service.update_story(story_id, story_update)
    if not updated_story:
        raise HTTPException(status_code=404, detail="Story not found")
    return updated_story

@router.get("/", response_model=List[UserStory])
async def list_stories(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    epic_id: Optional[str] = None,
    status: Optional[str] = None,
    priority: Optional[str] = None,
    tags: Optional[List[str]] = Query(None),
    service: StoryService = Depends(get_story_service)
) -> List[UserStory]:
    """List user stories with optional filtering"""
    return await service.list_stories(
        skip=skip,
        limit=limit,
        epic_id=epic_id,
        status=status,
        priority=priority,
        tags=tags
    )

@router.delete("/{story_id}")
async def delete_story(
    story_id: str,
    service: StoryService = Depends(get_story_service)
) -> dict:
    """Delete a user story"""
    deleted = await service.delete_story(story_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Story not found")
    return {"message": "Story deleted successfully"}

@router.get("/search/similar", response_model=List[UserStory])
async def search_similar_stories(
    query: str = Query(..., min_length=3),
    limit: int = Query(5, ge=1, le=20),
    epic_id: Optional[str] = None,
    service: StoryService = Depends(get_story_service)
) -> List[UserStory]:
    """Search for similar user stories using semantic search"""
    return await service.search_similar_stories(
        query=query,
        limit=limit,
        epic_id=epic_id
    )

@router.post("/generate", response_model=List[UserStory])
async def generate_stories(
    epic_id: str,
    service: StoryService = Depends(get_story_service),
    epic_service: EpicService = Depends(get_epic_service)
) -> List[UserStory]:
    """Generate user stories from an epic"""
    logger.info(f"Attempting to generate stories for epic {epic_id}")
    
    epic = await epic_service.get_epic(epic_id)
    logger.info(f"Epic found: {epic is not None}")
    
    if not epic:
        raise HTTPException(status_code=404, detail="Epic not found")
        
    # Create stories from epic's user_stories
    stories = []
    for story_data in epic.user_stories:
        logger.info(f"Creating story for role: {story_data.role}")
        story = UserStory(
            role=story_data.role,
            action=story_data.action,
            benefit=story_data.benefit,
            epic_id=epic_id,
            acceptance_criteria=epic.acceptance_criteria,
            status="draft",
            priority="medium"
        )
        created_story = await service.create_story(story)
        stories.append(created_story)
    
    logger.info(f"Generated {len(stories)} stories")
    return stories
