"""
Database Schema Reset Script

This script drops all existing tables and recreates them based on the current model definitions.
Use this when you need to reset the database schema after model changes.

WARNING: This will delete ALL data in the database!
"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text

from app.core.config import get_settings
# Import all models to ensure they're registered with SQLAlchemy
from app.models.user import User
from app.models.blog import Post, Category, Tag, PostCategory, PostTag, PostComment

async def reset_database():
    """Drop all tables and recreate them."""
    settings = get_settings()
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL, echo=True, future=True)
    
    # Get metadata from SQLModel (which uses SQLAlchemy under the hood)
    from sqlmodel import SQLModel
    metadata = SQLModel.metadata
    
    print("=" * 60)
    print("WARNING: This will delete ALL data in the database!")
    print("=" * 60)
    
    async with engine.begin() as conn:
        print("\n🗑️  Dropping all tables with CASCADE...")
        # Drop all tables in the public schema with CASCADE
        await conn.execute(text("DROP SCHEMA public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        # Grant permissions (PostgreSQL default)
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
        print("✅ All tables dropped successfully!")
        
        print("\n🔨 Creating all tables...")
        await conn.run_sync(metadata.create_all)
        print("✅ All tables created successfully!")
    
    await engine.dispose()
    
    print("\n" + "=" * 60)
    print("✨ Database schema reset complete!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(reset_database())
