from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

# --- Схемы для Пользователей ---

class UserCreateSchema(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    telegram_id: Optional[int] = None

class UserCreateTlgSchema(BaseModel):
    telegram_id: int
    username: str
    password: str

class UserChangeSchema(BaseModel):
    telegram_id: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None

class UserReadSchema(BaseModel):
    id: int
    username: str
    telegram_id: Optional[int] = None
    model_config = ConfigDict(from_attributes=True) 

# --- Схемы для Задач 

class TaskCreateSchema(BaseModel):
    title: str = Field(..., min_length=1, max_length=100) 
    description: Optional[str] = Field(None, max_length=500) 
    deadline: Optional[datetime] = None 
    username: str 

class TaskUpdateSchema(BaseModel):
    id: int
    field: str 
    new_value: str
    username: str

class TaskDeleteSchema(BaseModel):
    id: int

# Схема для возврата данных 
class TaskReadSchema(BaseModel):
    id: int
    title: str
    description: Optional[str]
    deadline: Optional[datetime]
    is_completed: bool
    
    model_config = ConfigDict(from_attributes=True) # Позволяет Pydantic работать с моделями SQLAlchemy
