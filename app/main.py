from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.api.v1.api import api_router
from app.web.routes import router as web_router
from app.core.config import get_settings
from app.core.logging import setup_logging
from app.db.session import init_db, get_session
from app.db.seed import seed_admin_user

settings = get_settings()

from app.middlwares.logger import RequestMiddleware

# ...

app = FastAPI(title="InsightBlog Gen-AI Feed")

app.add_middleware(RequestMiddleware)

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def on_startup():
    setup_logging()
    await init_db()
    
    # Seed admin user
    async for session in get_session():
        await seed_admin_user(session)
        break

from app.core.logging import logger

# ...

@app.get("/health")
async def health_check():
    logger.info("Health check called")
    return {"status": "ok"}

app.include_router(api_router, prefix="/api/v1")
app.include_router(web_router)
