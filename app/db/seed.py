"""
Database seeding utilities
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.user import User
from app.services.auth import get_password_hash
from app.core.logging import logger

async def seed_admin_user(session: AsyncSession):
    """
    Check if admin user exists, if not create one.
    Default credentials: admin@insightblog.com / admin123
    """
    # Check if admin exists
    result = await session.execute(
        select(User).where(User.email == "admin@insightblog.com")
    )
    admin = result.scalars().first()
    
    if not admin:
        logger.info("Admin user not found. Creating default admin user...")
        admin = User(
            email="admin@insightblog.com",
            full_name="Admin User",
            hashed_password=get_password_hash("admin123"),
            role="admin"
        )
        session.add(admin)
        await session.commit()
        logger.info("[SUCCESS] Admin user created successfully!")
        logger.info("[EMAIL] admin@insightblog.com")
        logger.info("[PASSWORD] admin123")
        logger.info("[WARNING] Please change the password after first login!")
    else:
        logger.info("[SUCCESS] Admin user already exists")
