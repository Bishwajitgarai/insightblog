import pytest
from typing import AsyncGenerator, Generator
from httpx import AsyncClient, ASGITransport
import sys
import os
sys.path.append(os.getcwd())

from app.main import app
from app.db.session import get_session
from app.core.config import get_settings

settings = get_settings()

# ... (comments) ...

from app.models.user import User, Role

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c

@pytest.fixture
def mock_user():
    return User(
        id=1,
        email="test@example.com",
        hashed_password="hashed",
        full_name="Test User",
        role=Role.USER,
        is_active=True
    )

@pytest.fixture
def mock_admin():
    return User(
        id=2,
        email="admin@example.com",
        hashed_password="hashed",
        full_name="Admin User",
        role=Role.ADMIN,
        is_active=True
    )
