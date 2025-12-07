from typing import Generic, TypeVar, List, Optional
from pydantic import BaseModel

T = TypeVar("T")

class PaginationSchema(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int

class ResponseSchema(BaseModel, Generic[T]):
    data: T
    message: str = "Success"
    pagination: Optional[PaginationSchema] = None
