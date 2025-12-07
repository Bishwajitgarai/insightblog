import asyncio
from sqlmodel import select
from app.db.session import init_db, get_session, engine
from app.models.user import User, Role
from app.services.auth import get_password_hash
from sqlalchemy.orm import sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

from app.core.config import get_settings

settings = get_settings()

async def create_initial_data():
    await init_db()
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        result = await session.exec(select(User).where(User.email == settings.ADMIN_EMAIL))
        user = result.first()
        
        if not user:
            admin_user = User(
                email=settings.ADMIN_EMAIL,
                full_name="Admin User",
                hashed_password=get_password_hash(settings.ADMIN_PASSWORD),
                role=Role.ADMIN,
                is_active=True
            )
            session.add(admin_user)
            await session.commit()
            print("Admin user created")
        else:
            print("Admin user already exists")

if __name__ == "__main__":
    asyncio.run(create_initial_data())
