from fastapi import APIRouter, Query
from typing import List
from app.models.domain import ContentItem
from app.services.feed import feed_service

router = APIRouter()

@router.get("/", response_model=List[ContentItem])
async def get_feed(user_id: str, interests: str = Query(..., description="User interests for personalization")):
    return await feed_service.get_feed_for_user(user_id, interests)
