from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Annotated
import shutil
import os
from pathlib import Path

from app.db.session import get_session
from app.models.user import User
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services.auth import get_password_hash, verify_password, create_access_token, create_refresh_token
from app.services.otp import create_otp, verify_otp
from app.core.config import get_settings
from jose import JWTError, jwt
from pydantic import BaseModel
from app.utils.upload_helper import get_user_profile_upload_path

router = APIRouter()
settings = get_settings()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/users/login")

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    email: str
    otp: str
    new_password: str

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], session: AsyncSession = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    return user

@router.post("/register", response_model=UserRead)
async def register(user: UserCreate, session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(User).where(User.email == user.email))
    if result.first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create User object directly with hashed password
    db_user = User(
        email=user.email,
        full_name=user.full_name,
        hashed_password=get_password_hash(user.password),
        role=user.role if hasattr(user, 'role') else "user"
    )
    session.add(db_user)
    await session.commit()
    await session.refresh(db_user)
    return db_user

@router.post("/login")
async def login(response: Response, form_data: Annotated[OAuth2PasswordRequestForm, Depends()], session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    # Also set refresh token in cookie for enhanced security if you want, but for now returning in body is typical
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    
    return {
        "access_token": access_token, 
        "refresh_token": refresh_token,
        "token_type": "bearer"
    }

class RefreshTokenRequest(BaseModel):
    refresh_token: str

@router.post("/refresh")
async def refresh_token(request: RefreshTokenRequest, response: Response, session: AsyncSession = Depends(get_session)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(request.refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        token_type: str = payload.get("type")
        if email is None or token_type != "refresh":
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    result = await session.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None:
        raise credentials_exception
    
    access_token = create_access_token(data={"sub": user.email})
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    
    return {"access_token": access_token, "token_type": "bearer"}

class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str

@router.post("/me/change-password")
async def change_password(
    request: ChangePasswordRequest, 
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_session)
):
    if not verify_password(request.old_password, current_user.hashed_password):
        raise HTTPException(status_code=400, detail="Incorrect old password")
    
    current_user.hashed_password = get_password_hash(request.new_password)
    session.add(current_user)
    await session.commit()
    
    return {"message": "Password changed successfully"}

@router.get("/me", response_model=UserRead)
async def read_users_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user

@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == request.email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    await create_otp(request.email)
    return {"message": "OTP sent"}

@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, session: AsyncSession = Depends(get_session)):
    if not await verify_otp(request.email, request.otp):
        raise HTTPException(status_code=400, detail="Invalid OTP")
    
    result = await session.execute(select(User).where(User.email == request.email))
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.hashed_password = get_password_hash(request.new_password)
    session.add(user)
    await session.commit()
    return {"message": "Password reset successfully"}

@router.put("/me", response_model=UserRead)
async def update_profile(
    user_update: UserUpdate, 
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_session)
):
    user_data = user_update.dict(exclude_unset=True)
    for key, value in user_data.items():
        setattr(current_user, key, value)
    
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user

@router.post("/me/avatar", response_model=UserRead)
async def upload_avatar(
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_session),
    file: UploadFile = File(...)
):
    # Use structured upload path
    file_extension = os.path.splitext(file.filename)[1]
    unique_filename = f"avatar{file_extension}"
    
    file_path, url_path = get_user_profile_upload_path(current_user.id, unique_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    current_user.profile_image_url = url_path
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user

@router.get("/profile/{user_id}")
async def get_user_profile_by_id(
    user_id: int,
    session: AsyncSession = Depends(get_session)
):
    """Get user profile by user ID"""
    # Find user by ID
    result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Count user's posts
    from app.models.blog import Post
    count_result = await session.execute(
        select(func.count()).select_from(Post).where(
            Post.author_id == user.id,
            Post.published == True
        )
    )
    post_count = count_result.scalar()
    
    return {
        "id": user.id,
        "username": user.email.split("@")[0],
        "email": user.email,
        "full_name": user.full_name,
        "bio": user.bio,
        "profile_image_url": user.profile_image_url,
        "role": user.role,

        "post_count": post_count
    }

@router.get("/profile/{user_id}/posts")
async def get_user_posts_by_id(
    user_id: int,
    skip: int = 0,
    limit: int = 12,
    session: AsyncSession = Depends(get_session)
):
    """Get user's posts by user ID with pagination (for profile feed)"""
    # Find user by ID
    user_result = await session.execute(
        select(User).where(User.id == user_id)
    )
    user = user_result.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    from app.models.blog import Post
    
    # Get total count
    count_result = await session.execute(
        select(func.count()).select_from(Post).where(
            Post.author_id == user.id,
            Post.published == True
        )
    )
    total = count_result.scalar()
    
    # Get posts with pagination
    query = select(Post).where(
        Post.author_id == user.id,
        Post.published == True
    ).order_by(Post.published_at.desc()).offset(skip).limit(limit)
    
    result = await session.execute(query)
    posts = result.scalars().all()
    
    posts_data = []
    for post in posts:
        # Get like count
        from app.models.blog import PostLike, PostComment
        like_query = select(func.count()).select_from(PostLike).where(PostLike.post_id == post.id)
        like_result = await session.execute(like_query)
        like_count = like_result.scalar()
        
        # Get comment count
        comment_query = select(func.count()).select_from(PostComment).where(PostComment.post_id == post.id)
        comment_result = await session.execute(comment_query)
        comment_count = comment_result.scalar()
        
        posts_data.append({
            "id": post.id,
            "title": post.title,
            "summary": post.summary,
            "image_url": post.image_url,
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "like_count": like_count,
            "comment_count": comment_count
        })
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "has_more": (skip + limit) < total,
        "posts": posts_data
    }

