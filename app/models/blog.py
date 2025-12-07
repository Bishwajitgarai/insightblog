from typing import List, Optional
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship
from app.models.user import User

# Association Tables
class PostCategory(SQLModel, table=True):
    post_id: Optional[int] = Field(default=None, foreign_key="post.id", primary_key=True)
    category_id: Optional[int] = Field(default=None, foreign_key="category.id", primary_key=True)

class PostTag(SQLModel, table=True):
    post_id: Optional[int] = Field(default=None, foreign_key="post.id", primary_key=True)
    tag_id: Optional[int] = Field(default=None, foreign_key="tag.id", primary_key=True)

# Models
class Category(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=75)
    slug: str = Field(unique=True, index=True, max_length=100)
    
    posts: List["Post"] = Relationship(back_populates="categories", link_model=PostCategory)

class Tag(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=75)
    slug: str = Field(unique=True, index=True, max_length=100)
    
    posts: List["Post"] = Relationship(back_populates="tags", link_model=PostTag)

class Post(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    author_id: int = Field(foreign_key="user.id")
    title: str = Field(max_length=200)
    summary: Optional[str] = None
    image_url: Optional[str] = None
    published: bool = Field(default=False)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None
    
    categories: List[Category] = Relationship(back_populates="posts", link_model=PostCategory)
    tags: List[Tag] = Relationship(back_populates="posts", link_model=PostTag)
    comments: List["PostComment"] = Relationship(back_populates="post", sa_relationship_kwargs={"cascade": "all, delete"})

class PostComment(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    post_id: int = Field(foreign_key="post.id")
    parent_id: Optional[int] = Field(default=None, foreign_key="postcomment.id")
    title: Optional[str] = Field(default=None, max_length=100)
    published: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    published_at: Optional[datetime] = None # Defaults to created_at if published
    content: Optional[str] = None
    
    post: Post = Relationship(back_populates="comments")
    children: List["PostComment"] = Relationship(
        sa_relationship_kwargs={
            "cascade": "all, delete",
            "remote_side": "PostComment.id"
        }
    )
