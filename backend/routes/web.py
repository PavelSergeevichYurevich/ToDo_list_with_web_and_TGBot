from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from backend.models.models import User
from backend.dependencies.dependency import get_db

web_router = APIRouter(tags=['Web Pages'])
templates = Jinja2Templates(directory="backend/templates")

@web_router.get('/', response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse(request=request, name='index.html')

@web_router.get("/login/", response_class=HTMLResponse)
async def login_page(request: Request):
    return templates.TemplateResponse(request=request, name="login.html")

@web_router.get("/register/", response_class=HTMLResponse)
async def register_page(request: Request):
    return templates.TemplateResponse(request=request, name="register.html")

@web_router.get("/users/", response_class=HTMLResponse)
async def get_users_page(request: Request, db: AsyncSession = Depends(get_db)):
    # Асинхронное получение списка
    result = await db.execute(select(User))
    users = result.scalars().all()
    
    # Передаем список объектов напрямую. Jinja2 сама возьмет нужные поля.
    return templates.TemplateResponse(
        "users.html", 
        {"request": request, "users": users}
    )

@web_router.get("/tasks/{username}", response_class=HTMLResponse)
async def get_tasks_page(request: Request, username: str, db: AsyncSession = Depends(get_db)):
    # Ищем пользователя со всеми его задачами
    result = await db.execute(select(User).where(User.username == username).options(selectinload(User.tasks)))
    print(result)
    user = result.scalars().first()
    
    if not user:
        # Можно вернуть 404 страницу
        return templates.TemplateResponse("404.html", {"request": request}, status_code=404)
        
    return templates.TemplateResponse(
        "tasks.html", 
        {"request": request, "user": user}
    )
