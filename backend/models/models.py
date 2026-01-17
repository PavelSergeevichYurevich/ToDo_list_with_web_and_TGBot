from typing import List, Optional
from datetime import datetime
from sqlalchemy import ForeignKey, BigInteger, String, DateTime
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..database.database import Base

class User(Base):
    __tablename__ = "user"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    hashed_password: Mapped[str]
    
    tasks: Mapped[List["Task"]] = relationship(
        back_populates='user', 
        cascade='all, delete-orphan', 
        passive_deletes=True
    )

class Task(Base):
    __tablename__ = "task"
    
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(100)) # переименовали 'task' в 'title'
    description: Mapped[Optional[str]] = mapped_column(String(500)) # 'describe' -> 'description'
    
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    deadline: Mapped[Optional[datetime]] = mapped_column(DateTime) # 'ex_date' -> 'deadline'
    
    is_completed: Mapped[bool] = mapped_column(default=False)
    
    user_id: Mapped[int] = mapped_column(ForeignKey('user.id', ondelete='CASCADE'), index=True)
    user: Mapped["User"] = relationship(back_populates="tasks")
