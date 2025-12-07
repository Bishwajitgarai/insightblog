import pytest
from httpx import AsyncClient
from app.main import app
from app.web.routes import get_current_user_from_cookie
from app.models.user import User

@pytest.mark.asyncio
async def test_dashboard_redirect_if_not_logged_in(client: AsyncClient):
    response = await client.get("/dashboard")
    # Should redirect to /login (307 Temporary Redirect or 303 See Other)
    # RedirectResponse defaults to 307 unless status_code is set.
    assert response.status_code == 307
    assert "login" in response.headers["location"]

@pytest.mark.asyncio
async def test_dashboard_access_with_cookie(client: AsyncClient, mock_user: User):
    # Mock get_current_user_from_cookie dependency
    app.dependency_overrides[get_current_user_from_cookie] = lambda: mock_user
    
    response = await client.get("/dashboard")
    assert response.status_code == 200
    assert "Your Feed" in response.text
    
    app.dependency_overrides = {}
