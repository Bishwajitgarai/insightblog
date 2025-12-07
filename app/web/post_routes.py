from fastapi import APIRouter, Request, Depends, HTTPException, status, Body
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional

from app.db.session import get_session
from app.models.user import User
from app.models.blog import Post, Category, Tag, PostCategory, PostTag, PostComment, PostLike, PostShare, Notification
from app.web.routes import get_current_user_from_cookie

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# Post view and social interaction routes

@router.get("/posts/{post_id}", response_class=HTMLResponse)
async def view_post(
    post_id: int,
    request: Request,
    user: Optional[User] = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    # Get post
    post = await session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Get author
    author = await session.get(User, post.author_id)
    
    # Get categories
    cat_query = select(Category).join(PostCategory).where(PostCategory.post_id == post_id)
    cat_result = await session.execute(cat_query)
    categories = cat_result.scalars().all()
    
    # Get tags
    tag_query = select(Tag).join(PostTag).where(PostTag.post_id == post_id)
    tag_result = await session.execute(tag_query)
    tags = tag_result.scalars().all()
    
    # Get comments with authors
    comment_query = select(PostComment).where(
        PostComment.post_id == post_id,
        PostComment.parent_id == None
    ).order_by(PostComment.created_at.desc())
    comment_result = await session.execute(comment_query)
    comments_raw = comment_result.scalars().all()
    
    # Format comments with author names and replies
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
                "created_at": reply.created_at,
                "user_id": reply.user_id,
                "author_name": reply_author.full_name if reply_author else "Unknown"
            })
        
        comments.append({
            "id": comment.id,
            "content": comment.content,
            "created_at": comment.created_at,
            "user_id": comment.user_id,
            "author_name": comment_author.full_name if comment_author else "Unknown",
            "replies": replies
        })
    
    # Get like count and check if user liked
    like_query = select(PostLike).where(PostLike.post_id == post_id)
    like_result = await session.execute(like_query)
    likes = like_result.scalars().all()
    like_count = len(likes)
    user_liked = False
    if user:
        user_liked = any(like.user_id == user.id for like in likes)
    
    comment_count = len(comments_raw)
    
    return templates.TemplateResponse("post_view.html", {
        "request": request,
        "user": user,
        "post": post,
        "author": author,
        "categories": categories,
        "tags": tags,
        "comments": comments,
        "comment_count": comment_count,
        "like_count": like_count,
        "user_liked": user_liked
    })

@router.post("/posts/{post_id}/like")
async def toggle_like(
    post_id: int,
    user: Optional[User] = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Check if already liked
    like_query = select(PostLike).where(
        PostLike.post_id == post_id,
        PostLike.user_id == user.id
    )
    result = await session.execute(like_query)
    existing_like = result.scalars().first()
    
    if existing_like:
        # Unlike
        await session.delete(existing_like)
        await session.commit()
        liked = False
    else:
        # Like
        new_like = PostLike(post_id=post_id, user_id=user.id)
        session.add(new_like)
        await session.commit()
        liked = True
        
        # Create notification for post author
        post = await session.get(Post, post_id)
        if post and post.author_id != user.id:
            notification = Notification(
                user_id=post.author_id,
                actor_id=user.id,
                type="like",
                content=f"{user.full_name} liked your post",
                post_id=post_id
            )
            session.add(notification)
            await session.commit()
    
    # Get updated like count
    count_query = select(PostLike).where(PostLike.post_id == post_id)
    count_result = await session.execute(count_query)
    like_count = len(count_result.scalars().all())
    
    return {"liked": liked, "like_count": like_count}

@router.post("/posts/{post_id}/share")
async def share_post(
    post_id: int,
    user: Optional[User] = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    # Create share record
    new_share = PostShare(post_id=post_id, user_id=user.id)
    session.add(new_share)
    
    # Create notification for post author
    post = await session.get(Post, post_id)
    if post and post.author_id != user.id:
        notification = Notification(
            user_id=post.author_id,
            actor_id=user.id,
            type="share",
            content=f"{user.full_name} shared your post",
            post_id=post_id
        )
        session.add(notification)
    
    await session.commit()
    return {"message": "Post shared successfully"}

@router.post("/posts/{post_id}/comment")
async def add_comment(
    post_id: int,
    data: dict = Body(...),
    user: Optional[User] = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    content = data.get("content")
    parent_id = data.get("parent_id")
    
    if not content:
        raise HTTPException(status_code=400, detail="Content is required")
    
    # Create comment
    new_comment = PostComment(
        post_id=post_id,
        user_id=user.id,
        content=content,
        parent_id=parent_id
    )
    session.add(new_comment)
    await session.commit()
    await session.refresh(new_comment)
    
    # Create notification for post author
    post = await session.get(Post, post_id)
    if post and post.author_id != user.id:
        notification = Notification(
            user_id=post.author_id,
            actor_id=user.id,
            type="comment",
            content=f"{user.full_name} commented on your post",
            post_id=post_id,
            comment_id=new_comment.id
        )
        session.add(notification)
        await session.commit()
    
    return {"message": "Comment added successfully", "comment_id": new_comment.id}

@router.delete("/posts/{post_id}/comments/{comment_id}")
async def delete_comment(
    post_id: int,
    comment_id: int,
    user: Optional[User] = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    comment = await session.get(PostComment, comment_id)
    if not comment:
        raise HTTPException(status_code=404, detail="Comment not found")
    
    # Check permissions (admin or comment author)
    if user.role != "admin" and comment.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await session.delete(comment)
    await session.commit()
    
    return {"message": "Comment deleted successfully"}

@router.delete("/posts/{post_id}")
async def delete_post(
    post_id: int,
    user: Optional[User] = Depends(get_current_user_from_cookie),
    session: AsyncSession = Depends(get_session)
):
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    post = await session.get(Post, post_id)
    if not post:
        raise HTTPException(status_code=404, detail="Post not found")
    
    # Check permissions (admin or post author)
    if user.role != "admin" and post.author_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await session.delete(post)
    await session.commit()
    
    return {"message": "Post deleted successfully"}
