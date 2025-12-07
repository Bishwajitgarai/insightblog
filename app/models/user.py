from typing import Optional
from sqlmodel import Field, SQLModel
from enum import Enum

class Role(str, Enum):
    USER = "user"
    ADMIN = "admin"

class UserBase(SQLModel):
    email: str = Field(unique=True, index=True)
    full_name: Optional[str] = None
    role: Role = Role.USER
    is_active: bool = True
    profile_image_url: Optional[str] = None
    bio: Optional[str] = None

class User(UserBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    hashed_password: str


