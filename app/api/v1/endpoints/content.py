from fastapi import APIRouter, HTTPException
from app.models.domain import ContentItem
from app.services.feed import feed_service

router = APIRouter()

@router.post("/")
async def ingest_content(content: ContentItem):
    try:
        result = await feed_service.ingest_content(content)
        return {"message": "Content ingested", "content_id": result.content_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
