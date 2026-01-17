import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from dotenv import load_dotenv
import uvicorn
from contextlib import asynccontextmanager
from backend.routes import auth, user, task, web

env_path = Path(__file__).resolve().parent / '.env'
load_dotenv(dotenv_path=env_path)
HOST = os.getenv("APP_HOST", "127.0.0.1")
PORT = int(os.getenv("APP_PORT", 8000))

@asynccontextmanager
async def lifespan(app: FastAPI):
    print('Starting server...')
    yield
    print('Server stopped')

app = FastAPI(
    title='Exam ToDo Project',
    lifespan=lifespan
)

# Подключаем роутеры
app.include_router(auth.auth_router)
app.include_router(user.user_router)
app.include_router(task.task_router)
app.include_router(web.web_router)

static_path = Path(__file__).parent.absolute() / "static"
app.mount("/static", StaticFiles(directory=static_path), name="static")

if __name__ == '__main__':
    
    uvicorn.run(
        'main:app', 
        port=PORT, 
        host=HOST, 
        reload=True
    )
