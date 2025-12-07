from fastapi import APIRouter, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.session import get_session
from app.models.user import User
from app.models.blog import Notification
from app.web.routes import get_current_user_from_cookie

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Notification routes

@router.get("/notifications", response_class=HTMLResponse)
async def notifications_page(
    request: Request,
    user: Optional[User] = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        return RedirectResponse(url="/login")
    
    # Get notifications for user (admin gets all)
    if user.role == "admin":
        query = select(Notification).order_by(Notification.created_at.desc()).limit(50)
    else:
        query = select(Notification).where(Notification.user_id == user.id).order_by(Notification.created_at.desc()).limit(50)
    
    result = await session.execute(query)
    notifications = result.scalars().all()
    
    return templates.TemplateResponse("notifications.html", {
        "request": request,
        "user": user,
        "notifications": notifications
    })

@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    user: Optional[User] = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    notification = await session.get(Notification, notification_id)
    if not notification or notification.user_id != user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.read = True
    session.add(notification)
    await session.commit()
    
    return {"message": "Notification marked as read"}
