from fastapi import APIRouter, Depends, HTTPException
from typing import List, Annotated
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel import select

from app.db.session import get_session
from app.models.user import User, Role
from app.schemas.user import UserRead
from app.api.v1.endpoints.users import get_current_user

router = APIRouter()

async def get_current_admin(current_user: Annotated[User, Depends(get_current_user)]):
    if current_user.role != Role.ADMIN:
        raise HTTPException(status_code=403, detail="Not enough privileges")
    return current_user

@router.get("/users", response_model=List[UserRead])
async def read_users(
    session: AsyncSession = Depends(get_session),
    current_user: User = Depends(get_current_admin)
):
    users = await session.exec(select(User))
    return users.all()
