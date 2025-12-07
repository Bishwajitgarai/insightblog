from fastapi import APIRouter, Request, Depends, Form, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select
from typing import Optional

from app.db.session import get_session
from app.models.user import User, UserCreate
from app.services.auth import get_password_hash, verify_password, create_access_token
from app.core.config import get_settings
from jose import jwt, JWTError

router = APIRouter()
templates = Jinja2Templates(directory="templates")
settings = get_settings()

async def get_current_user_from_cookie(request: Request, session: AsyncSession):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        scheme, _, param = token.partition(" ")
        payload = jwt.decode(param, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None
    
    result = await session.exec(select(User).where(User.email == email))
    return result.first()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, session: AsyncSession = Depends(get_session)):
    user = await get_current_user_from_cookie(request, session)
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(User).where(User.email == username))
    user = result.first()
    if not user or not verify_password(password, user.hashed_password):
        return templates.TemplateResponse("login.html", {"request": request, "error": "Invalid credentials"})
    
    access_token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.post("/register")
async def register(request: Request, email: str = Form(...), password: str = Form(...), full_name: str = Form(...), session: AsyncSession = Depends(get_session)):
    result = await session.exec(select(User).where(User.email == email))
    if result.first():
        return templates.TemplateResponse("register.html", {"request": request, "error": "Email already registered"})
    
    user = User(email=email, full_name=full_name, hashed_password=get_password_hash(password))
    session.add(user)
    await session.commit()
    
    # Auto login
    access_token = create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, session: AsyncSession = Depends(get_session)):
    user = await get_current_user_from_cookie(request, session)
    if not user:
        return RedirectResponse(url="/login")
    
    # Mock feed data for now
    feed = [
        {"title": "Welcome to InsightBlog", "body": "This is your personalized feed."},
        {"title": "Getting Started", "body": "Explore content tailored to your interests."}
    ]
    return templates.TemplateResponse("dashboard.html", {"request": request, "user": user, "feed": feed})

@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie("access_token")
    return response

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})

@router.get("/reset-password", response_class=HTMLResponse)
async def reset_password_page(request: Request):
    return templates.TemplateResponse("reset_password.html", {"request": request})

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request, session: AsyncSession = Depends(get_session)):
    user = await get_current_user_from_cookie(request, session)
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})
