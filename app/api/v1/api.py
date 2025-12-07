from fastapi import APIRouter
from app.api.v1.endpoints import users, content, feed, admin

api_router = APIRouter()
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(admin.router, prefix="/admin", tags=["admin"])
api_router.include_router(content.router, prefix="/content", tags=["content"])
api_router.include_router(feed.router, prefix="/feed", tags=["feed"])
