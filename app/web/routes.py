from fastapi import APIRouter, Request, Depends, Form, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.session import get_session
from app.models.user import User
from app.models.blog import Post, Category, Tag, PostCategory, PostTag
from app.services.auth import get_password_hash, verify_password, create_access_token
from app.core.config import get_settings
from jose import jwt, JWTError
import os
import uuid
from datetime import datetime

router = APIRouter()
templates = Jinja2Templates(directory="templates")
settings = get_settings()

async def get_current_user_from_cookie(request: Request, session: AsyncSession = Depends(get_session)):
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
    
    result = await session.execute(select(User).where(User.email == email))
    return result.scalars().first()

@router.get("/", response_class=HTMLResponse)
async def index(request: Request, user: Optional[User] = Depends(get_current_user_from_cookie)):
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(User).where(User.email == username))
    user = result.scalars().first()
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
    result = await session.execute(select(User).where(User.email == email))
    if result.scalars().first():
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
async def dashboard(request: Request, user: Optional[User] = Depends(get_current_user_from_cookie), session: AsyncSession = Depends(get_session)):
    if not user:
        return RedirectResponse(url="/login")
    
    # Fetch published posts from database
    query = select(Post).where(Post.published == True).order_by(Post.published_at.desc()).limit(20)
    result = await session.execute(query)
    posts = result.scalars().all()
    
    # Format posts for template
    feed = []
    for post in posts:
        feed.append({
            "id": post.id,
            "title": post.title,
            "body": post.summary or "No summary available",
            "image_url": post.image_url,
            "created_at": post.created_at,
            "author_id": post.author_id
        })
    
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
async def profile_page(request: Request, user: Optional[User] = Depends(get_current_user_from_cookie)):
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("profile.html", {"request": request, "user": user})

@router.get("/posts/create", response_class=HTMLResponse)
async def create_post_page(request: Request, user: Optional[User] = Depends(get_current_user_from_cookie)):
    if not user:
        return RedirectResponse(url="/login")
    return templates.TemplateResponse("create_post.html", {"request": request, "user": user})

@router.post("/posts/create")
async def create_post(
    request: Request,
    title: str = Form(...),
    summary: str = Form(...),
    category: str = Form(...),
    tags: Optional[str] = Form(None),
    published: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    user: Optional[User] = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        return RedirectResponse(url="/login")
    
    # Handle image upload
    image_url = None
    if image and image.filename:
        # Generate unique filename
        file_extension = os.path.splitext(image.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join("static", "uploads", unique_filename)
        
        # Save file
        with open(file_path, "wb") as f:
            content = await image.read()
            f.write(content)
        
        image_url = f"/static/uploads/{unique_filename}"
    
    # Create the post
    is_published = published == "true"
    
    new_post = Post(
        author_id=user.id,
        title=title,
        summary=summary,
        image_url=image_url,
        published=is_published,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        published_at=datetime.utcnow() if is_published else None
    )
    
    session.add(new_post)
    await session.commit()
    await session.refresh(new_post)
    
    # Handle category (single category, auto-create if doesn't exist)
    if category:
        cat_slug = category.lower().replace(" ", "-")
        cat_res = await session.execute(select(Category).where(Category.slug == cat_slug))
        category_obj = cat_res.scalars().first()
        if not category_obj:
            category_obj = Category(title=category, slug=cat_slug)
            session.add(category_obj)
            await session.commit()
            await session.refresh(category_obj)
        
        link = PostCategory(post_id=new_post.id, category_id=category_obj.id)
        session.add(link)
    
    # Handle tags (comma-separated, auto-create if doesn't exist)
    if tags:
        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        for tag_title in tag_list:
            tag_slug = tag_title.lower().replace(" ", "-")
            tag_res = await session.execute(select(Tag).where(Tag.slug == tag_slug))
            tag_obj = tag_res.scalars().first()
            if not tag_obj:
                tag_obj = Tag(title=tag_title, slug=tag_slug)
                session.add(tag_obj)
                await session.commit()
                await session.refresh(tag_obj)
            
            link = PostTag(post_id=new_post.id, tag_id=tag_obj.id)
            session.add(link)
    
    await session.commit()
    
    # Redirect to dashboard with success message
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)
