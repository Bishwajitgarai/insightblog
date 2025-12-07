from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional
from datetime import datetime
import os
import uuid

from app.db.session import get_session
from app.models.blog import Post, Category, Tag, PostCategory, PostTag, PostComment, PostLike, PostShare, Notification
from app.models.user import User
from app.api.v1.endpoints.users import get_current_user

router = APIRouter()

# GET /api/v1/posts/ - List posts with pagination
@router.get("/")
async def list_posts(
    skip: int = 0,
    limit: int = 20,
    published_only: bool = True,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    query = select(Post)
    if published_only:
        query = query.where(Post.published == True)
    
    count_query = select(func.count()).select_from(Post)
    if published_only:
        count_query = count_query.where(Post.published == True)
    total_result = await session.execute(count_query)
    total = total_result.scalar()
    
    query = query.order_by(Post.published_at.desc()).offset(skip).limit(limit)
    result = await session.execute(query)
    posts = result.scalars().all()
    
    posts_data = []
    for post in posts:
        like_query = select(func.count()).select_from(PostLike).where(PostLike.post_id == post.id)
        like_result = await session.execute(like_query)
        like_count = like_result.scalar()
        
        comment_query = select(func.count()).select_from(PostComment).where(PostComment.post_id == post.id)
        comment_result = await session.execute(comment_query)
        comment_count = comment_result.scalar()
        
        cat_query = select(Category).join(PostCategory).where(PostCategory.post_id == post.id)
        cat_result = await session.execute(cat_query)
        categories = [cat.title for cat in cat_result.scalars().all()]
        
        tag_query = select(Tag).join(PostTag).where(PostTag.post_id == post.id)
        tag_result = await session.execute(tag_query)
        tags = [tag.title for tag in tag_result.scalars().all()]
        
        posts_data.append({
            "id": post.id,
            "title": post.title,
            "summary": post.summary,
            "image_url": post.image_url,
            "author_id": post.author_id,
            "published": post.published,
            "created_at": post.created_at.isoformat(),
            "published_at": post.published_at.isoformat() if post.published_at else None,
            "like_count": like_count,
            "comment_count": comment_count,
            "categories": categories,
            "tags": tags
        })
    
    return {
        "total": total,
        "skip": skip,
        "limit": limit,
        "posts": posts_data
    }

# GET /api/v1/posts/{post_id} - Get single post with details
@router.get("/{post_id}")
async def get_post(
    post_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    post = await session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get author
    author = await session.get(User, post.author_id)
    
    # Get categories
    cat_query = select(Category).join(PostCategory).where(PostCategory.post_id == post_id)
    cat_result = await session.execute(cat_query)
    categories = [{"id": cat.id, "title": cat.title} for cat in cat_result.scalars().all()]
    
    # Get tags
    tag_query = select(Tag).join(PostTag).where(PostTag.post_id == post_id)
    tag_result = await session.execute(tag_query)
    tags = [{"id": tag.id, "title": tag.title} for tag in tag_result.scalars().all()]
    
    # Get comments with replies
    comment_query = select(PostComment).where(
        PostComment.post_id == post_id,
        PostComment.parent_id == None
    ).order_by(PostComment.created_at.desc())
    comment_result = await session.execute(comment_query)
    comments_raw = comment_result.scalars().all()
    
    comments = []
    for comment in comments_raw:
        comment_author = await session.get(User, comment.user_id)
        
        # Get replies
        reply_query = select(PostComment).where(PostComment.parent_id == comment.id).order_by(PostComment.created_at)
        reply_result = await session.execute(reply_query)
        replies_raw = reply_result.scalars().all()
        
        replies = []
        for reply in replies_raw:
            reply_author = await session.get(User, reply.user_id)
            replies.append({
                "id": reply.id,
                "content": reply.content,
                "created_at": reply.created_at.isoformat(),
                "user_id": reply.user_id,
                "author_name": reply_author.full_name if reply_author else "Unknown"
            })
        
        comments.append({
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at.isoformat(),
            "user_id": comment.user_id,
            "author_name": comment_author.full_name if comment_author else "Unknown",
            "replies": replies
        })
    
    # Get like count and check if user liked
    like_query = select(PostLike).where(PostLike.post_id == post_id)
    like_result = await session.execute(like_query)
    likes = like_result.scalars().all()
    like_count = len(likes)
    user_liked = any(like.user_id == current_user.id for like in likes)
    
    return {
        "id": post.id,
        "title": post.title,
        "summary": post.summary,
        "image_url": post.image_url,
        "author_id": post.author_id,
        "author_name": author.full_name if author else "Unknown",
        "published": post.published,
        "created_at": post.created_at.isoformat(),
        "published_at": post.published_at.isoformat() if post.published_at else None,
        "categories": categories,
        "tags": tags,
        "comments": comments,
        "like_count": like_count,
        "user_liked": user_liked,
        "comment_count": len(comments_raw)
    }

# POST /api/v1/posts/ - Create post
@router.post("/")
async def create_post(
    title: str = Form(...),
    summary: str = Form(...),
    category: str = Form(...),
    tags: Optional[str] = Form(None),
    image: Optional[UploadFile] = File(None),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    image_url = None
    if image and image.filename:
        file_extension = os.path.splitext(image.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = os.path.join("static", "uploads", unique_filename)
        
        with open(file_path, "wb") as f:
            content = await image.read()
            f.write(content)
        
        image_url = f"/static/uploads/{unique_filename}"
    
    new_post = Post(
        author_id=current_user.id,
        title=title,
        summary=summary,
        image_url=image_url,
        published=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        published_at=datetime.utcnow()
    )
    
    session.add(new_post)
    await session.commit()
    await session.refresh(new_post)
    
    # Handle category
    cat_slug = category.lower().replace(" ", "-")
    cat_result = await session.execute(select(Category).where(Category.slug == cat_slug))
    cat_obj = cat_result.scalars().first()
    
    if not cat_obj:
        cat_obj = Category(title=category, slug=cat_slug)
        session.add(cat_obj)
        await session.commit()
        await session.refresh(cat_obj)
    
    link = PostCategory(post_id=new_post.id, category_id=cat_obj.id)
    session.add(link)
    
    # Handle tags
    if tags:
        tag_list = [t.strip() for t in tags.split(",") if t.strip()]
        for tag_title in tag_list:
            tag_slug = tag_title.lower().replace(" ", "-")
            tag_result = await session.execute(select(Tag).where(Tag.slug == tag_slug))
            tag_obj = tag_result.scalars().first()
            
            if not tag_obj:
                tag_obj = Tag(title=tag_title, slug=tag_slug)
                session.add(tag_obj)
                await session.commit()
                await session.refresh(tag_obj)
            
            link = PostTag(post_id=new_post.id, tag_id=tag_obj.id)
            session.add(link)
    
    await session.commit()
    
    return {
        "id": new_post.id,
        "title": new_post.title,
        "summary": new_post.summary,
        "image_url": new_post.image_url,
        "published": new_post.published,
        "created_at": new_post.created_at.isoformat(),
        "message": "Post created successfully"
    }

# POST /api/v1/posts/{post_id}/like - Like/unlike post
@router.post("/{post_id}/like")
async def toggle_like(
    post_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    like_query = select(PostLike).where(
        PostLike.post_id == post_id,
        PostLike.user_id == current_user.id
    )
    result = await session.execute(like_query)
    existing_like = result.scalars().first()
    
    if existing_like:
        await session.delete(existing_like)
        await session.commit()
        liked = False
    else:
        new_like = PostLike(post_id=post_id, user_id=current_user.id)
        session.add(new_like)
        await session.commit()
        liked = True
        
        # Create notification
        post = await session.get(Post, post_id)
        if post and post.author_id != current_user.id:
            notification = Notification(
                user_id=post.author_id,
                actor_id=current_user.id,
                type="like",
                content=f"{current_user.full_name} liked your post",
                post_id=post_id
            )
            session.add(notification)
            await session.commit()
    
    count_query = select(func.count()).select_from(PostLike).where(PostLike.post_id == post_id)
    count_result = await session.execute(count_query)
    like_count = count_result.scalar()
    
    return {"liked": liked, "like_count": like_count}

# POST /api/v1/posts/{post_id}/share - Share post
@router.post("/{post_id}/share")
async def share_post(
    post_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    new_share = PostShare(post_id=post_id, user_id=current_user.id)
    session.add(new_share)
    
    post = await session.get(Post, post_id)
    if post and post.author_id != current_user.id:
        notification = Notification(
            user_id=post.author_id,
            actor_id=current_user.id,
            type="share",
            content=f"{current_user.full_name} shared your post",
            post_id=post_id
        )
        session.add(notification)
    
    await session.commit()
    return {"message": "Post shared successfully"}

# POST /api/v1/posts/{post_id}/comments - Add comment
@router.post("/{post_id}/comments")
async def add_comment(
    post_id: int,
    data: dict = Body(...),
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    content = data.get("content")
    parent_id = data.get("parent_id")
    
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    new_comment = PostComment(
        post_id=post_id,
        user_id=current_user.id,
        content=content,
        parent_id=parent_id
    )
    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)
    
    post = await session.get(Post, post_id)
    if post and post.author_id != current_user.id:
        notification = Notification(
            user_id=post.author_id,
            actor_id=current_user.id,
            type="comment",
            content=f"{current_user.full_name} commented on your post",
            post_id=post_id,
            comment_id=new_comment.id
        )
        session.add(notification)
        await session.commit()
    
    return {
        "message": "Comment added successfully",
        "comment_id": new_comment.id,
        "content": new_comment.content,
        "created_at": new_comment.created_at.isoformat()
    }

# DELETE /api/v1/posts/{post_id}/comments/{comment_id} - Delete comment
@router.delete("/{post_id}/comments/{comment_id}")
async def delete_comment(
    post_id: int,
    comment_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    comment = await session.get(PostComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    if current_user.role != "admin" and comment.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await session.delete(comment)
    await session.commit()
    
    return {"message": "Comment deleted successfully"}

# DELETE /api/v1/posts/{post_id} - Delete post
@router.delete("/{post_id}")
async def delete_post(
    post_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    post = await session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    if current_user.role != "admin" and post.author_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await session.delete(post)
    await session.commit()
    
    return {"message": "Post deleted successfully"}

# GET /api/v1/notifications - Get user notifications
@router.get("/notifications/")
async def get_notifications(
    skip: int = 0,
    limit: int = 50,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    if current_user.role == "admin":
        query = select(Notification).order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    else:
        query = select(Notification).where(Notification.user_id == current_user.id).order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    
    result = await session.execute(query)
    notifications = result.scalars().all()
    
    notifications_data = []
    for notif in notifications:
        notifications_data.append({
            "id": notif.id,
            "type": notif.type,
            "content": notif.content,
            "post_id": notif.post_id,
            "comment_id": notif.comment_id,
            "read": notif.read,
            "created_at": notif.created_at.isoformat()
        })
    
    return {"notifications": notifications_data}

# PUT /api/v1/notifications/{notification_id}/read - Mark as read
@router.put("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    notification = await session.get(Notification, notification_id)
    if not notification or notification.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    notification.read = True
    session.add(notification)
    await session.commit()
    
    return {"message": "Notification marked as read"}
