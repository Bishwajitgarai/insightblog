from pydantic import BaseModel
from typing import List, Optional

class UserProfile(BaseModel):
    user_id: str
    interests: List[str]
    embedding: Optional[List[float]] = None

class ContentItem(BaseModel):
    content_id: str
    title: str
    body: str
    tags: List[str]
    embedding: Optional[List[float]] = None
