from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# All routes ONLY serve templates - NO data handling
# All data is fetched client-side via JSON API calls

@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return RedirectResponse(url="/dashboard")

@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request):
    return templates.TemplateResponse("profile.html", {"request": request})

@router.get("/posts/create", response_class=HTMLResponse)
async def create_post_page(request: Request):
    return templates.TemplateResponse("create_post.html", {"request": request})

@router.get("/posts/{post_id}", response_class=HTMLResponse)
async def view_post_page(request: Request, post_id: int):
    return templates.TemplateResponse("post_view.html", {"request": request, "post_id": post_id})

@router.get("/notifications", response_class=HTMLResponse)
async def notifications_page(request: Request):
    return templates.TemplateResponse("notifications.html", {"request": request})

@router.get("/forgot-password", response_class=HTMLResponse)
async def forgot_password_page(request: Request):
    return templates.TemplateResponse("forgot_password.html", {"request": request})
