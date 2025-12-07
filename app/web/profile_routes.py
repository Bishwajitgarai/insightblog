from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, UploadFile, File
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import os

from app.db.session import get_session
from app.models.user import User
from app.web.routes import get_current_user_from_cookie
from app.services.auth import get_password_hash, verify_password
from app.utils.upload_helper import get_user_profile_upload_path

router = APIRouter()

# Profile update routes for web (cookie-based auth)

@router.post("/profile/update")
async def update_profile_web(
    request: Request,
    full_name: str = Form(...),
    bio: Optional[str] = Form(None),
    user: Optional[User] = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        return RedirectResponse(url="/login")
    
    user.full_name = full_name
    if bio:
        user.bio = bio
    
    session.add(user)
    await session.commit()
    
    return RedirectResponse(url="/profile", status_code=status.HTTP_303_SEE_OTHER)

@router.post("/profile/avatar")
async def upload_avatar_web(
    request: Request,
    file: UploadFile = File(...),
    user: Optional[User] = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Save file with structured path
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"avatar{file_extension}"
    
    # Use structured upload path
    file_path, url_path = get_user_profile_upload_path(user.id, unique_filename)
    
    with open(file_path, "wb") as f:
        content = await file.read()
        f.write(content)
    
    user.profile_image_url = url_path
    session.add(user)
    await session.commit()
    
    return {"profile_image_url": user.profile_image_url}

@router.post("/profile/change-password")
async def change_password_web(
    request: Request,
    old_password: str = Form(...),
    new_password: str = Form(...),
    user: Optional[User] = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Verify old password
    if not verify_password(old_password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    session.add(user)
    await session.commit()
    
    return {"message": "Password changed successfully"}
