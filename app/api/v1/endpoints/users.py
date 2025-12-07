from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Response
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
    upload_dir = Path("static/uploads")
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    file_path = upload_dir / f"{current_user.id}_{file.filename}"
    with file_path.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    current_user.profile_image_url = f"/static/uploads/{file_path.name}"
    session.add(current_user)
    await session.commit()
    await session.refresh(current_user)
    return current_user
