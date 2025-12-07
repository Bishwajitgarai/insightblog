from typing import Optional
from sqlmodel import SQLModel
from app.models.user import UserBase, Role

class UserCreate(UserBase):
    password: str

class UserRead(UserBase):
    id: int
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None

class UserUpdate(SQLModel):
    full_name: Optional[str] = None
    password: Optional[str] = None
    email: Optional[str] = None
    role: Optional[Role] = None
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None
