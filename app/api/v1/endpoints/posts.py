from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional, Annotated
from datetime import datetime

from app.db.session import get_session
from app.models.blog import Post, Category, Tag, PostComment, PostCategory, PostTag
from app.models.user import User
from app.api.v1.endpoints.users import get_current_user

# We need separate schemas for API request/response usually, 
# but for now I will use SQLModel classes directly or create lightweight ones here to save time/files if complexity is low,
# however for proper separation, let's define Pydantic models here or reuse if possible.
# Ideally these go to app/schemas/blog.py but I will inline simple ones or use SQLModel.

from pydantic import BaseModel

class PostCreate(BaseModel):
    title: str
    summary: str
    image_url: Optional[str] = None
    published: bool = False
    categories: List[str] = []  # Titles of categories
    tags: List[str] = []  # Titles of tags

class PostUpdate(BaseModel):
    title: Optional[str] = None
    summary: Optional[str] = None
    image_url: Optional[str] = None
    published: Optional[bool] = None
    categories: Optional[List[str]] = None
    tags: Optional[List[str]] = None

class CommentCreate(BaseModel):
    content: str
    title: Optional[str] = None
    parent_id: Optional[int] = None

class PostOut(BaseModel):
    id: int
    title: str
    summary: Optional[str]
    image_url: Optional[str]
    published: bool
    created_at: datetime
    published_at: Optional[datetime]
    author_id: int
    
    # Simple list of strings for display
    categories: List[str] = []
    tags: List[str] = []
    
    class Config:
        orm_mode = True

class CommentOut(BaseModel):
    id: int
    content: str
    created_at: datetime
    author_name: str = "Anonymous" # Needs join or separate fetch

router = APIRouter()

@router.post("/", response_model=PostOut)
async def create_post(
    post_in: PostCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_session)
):
    # simple logic: if category/tag doesn't exist, create it
    
    # 1. Create Post
    new_post = Post(
        author_id=current_user.id,
        title=post_in.title,
        summary=post_in.summary,
        image_url=post_in.image_url,
        published=post_in.published,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        published_at=datetime.utcnow() if post_in.published else None
    )
    
    # 2. Handle Categories
    for cat_title in post_in.categories:
        cat_slug = cat_title.lower().replace(" ", "-") # simplistic slug
        cat_res = await session.execute(select(Category).where(Category.slug == cat_slug))
        category = cat_res.scalars().first()
        if not category:
            category = Category(title=cat_title, slug=cat_slug)
            session.add(category)
            await session.commit()
            await session.refresh(category)
        
        # Link
        # Since new_post.id is None, we add object
        # But we need new_post to be added first or use relationship append
        pass
        # We will add usage below
    
    session.add(new_post)
    await session.commit()
    await session.refresh(new_post)

    # Now link m2m (simplified approach)
    for cat_title in post_in.categories:
        cat_slug = cat_title.lower().replace(" ", "-")
        cat_res = await session.execute(select(Category).where(Category.slug == cat_slug))
        category = cat_res.scalars().first() # Should exist now
        if category:
            link = PostCategory(post_id=new_post.id, category_id=category.id)
            session.add(link)

    for tag_title in post_in.tags:
        tag_slug = tag_title.lower().replace(" ", "-")
        tag_res = await session.execute(select(Tag).where(Tag.slug == tag_slug))
        tag = tag_res.scalars().first()
        if not tag:
            tag = Tag(title=tag_title, slug=tag_slug)
            session.add(tag)
            await session.commit()
            await session.refresh(tag)
        
        link = PostTag(post_id=new_post.id, tag_id=tag.id)
        session.add(link)


    await session.commit()
    await session.refresh(new_post)
    
    # TODO: Ingest to Vespa here or via separate task
    
    # Construct response manually or re-fetch with relations
    return PostOut(
        id=new_post.id,
        title=new_post.title,
        summary=new_post.summary,
        image_url=new_post.image_url,
        published=new_post.published,
        created_at=new_post.created_at,
        published_at=new_post.published_at,
        author_id=new_post.author_id,
        categories=post_in.categories,
        tags=post_in.tags
    )

@router.get("/", response_model=List[PostOut])
async def read_posts(
    skip: int = 0,
    limit: int = 20,
    session: AsyncSession = Depends(get_session)
):
    # This acts as the Feed
    query = select(Post).where(Post.published == True).order_by(Post.published_at.desc()).offset(skip).limit(limit)
    result = await session.execute(query)
    posts = result.scalars().all()
    
    # Ideally should eager load categories/tags
    # returning basic info for now
    out_posts = []
    for p in posts:
        # fetch cats/tags lazily (Not efficient but works for simple prototype)
        # Or better, just ignore for list view unless asked
        out_posts.append(PostOut(
            id=p.id,
            title=p.title,
            summary=p.summary,
            image_url=p.image_url,
            published=p.published,
            created_at=p.created_at,
            published_at=p.published_at,
            author_id=p.author_id,
            categories=[],  # populated if we join
            tags=[]
        ))
    return out_posts

@router.get("/{post_id}", response_model=PostOut)
async def read_post(post_id: int, session: AsyncSession = Depends(get_session)):
    user = await session.get(Post, post_id)
    if not user:
         raise HTTPException(status_code=404, detail="Post not found")
    # Again, populating relations manually or via query options is strictly needed for full detail
    return PostOut(
            id=user.id,
            title=user.title,
            summary=user.summary,
            image_url=user.image_url,
            published=user.published,
            created_at=user.created_at,
            published_at=user.published_at,
            author_id=user.author_id
    )

@router.post("/{post_id}/comments")
async def create_comment(
    post_id: int,
    comment_in: CommentCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    session: AsyncSession = Depends(get_session)
):
    post = await session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
        
    comment = PostComment(
        post_id=post_id,
        parent_id=comment_in.parent_id,
        title=comment_in.title,
        content=comment_in.content,
        published=True, # Auto publish for now
        created_at=datetime.utcnow(),
        published_at=datetime.utcnow()
    )
    session.add(comment)
    await session.commit()
    return {"message": "Comment added"}

@router.get("/{post_id}/comments")
async def read_comments(post_id: int, session: AsyncSession = Depends(get_session)):
    query = select(PostComment).where(PostComment.post_id == post_id).where(PostComment.published == True).order_by(PostComment.created_at)
    result = await session.execute(query)
    # Return simple list
    return result.scalars().all()
