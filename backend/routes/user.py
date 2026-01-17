from typing import Annotated, List
from fastapi import APIRouter, Depends, Request, status, Form, HTTPException
from fastapi.responses import RedirectResponse
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from backend.routes.auth import get_password_hash
from backend.dependencies.dependency import get_db
from backend.models.models import User
from backend.schemas.schemas import UserChangeSchema, UserCreateTlgSchema, UserReadSchema

user_router = APIRouter(prefix='/user', tags=['Users'])

# 1. Вывести пользователей
@user_router.get("/show/", response_model=List[UserReadSchema])
async def get_customers(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User))
    return result.scalars().all()

# 2. Создать пользователя через WEB-форму
@user_router.post("/add/")
async def add_user(
    username: Annotated[str, Form()], 
    password: Annotated[str, Form()], 
    telegram_id: Annotated[str, Form()] = "",
    db: AsyncSession = Depends(get_db)
):
    t_id = int(telegram_id) if telegram_id.strip() else None
    existing_user = await db.execute(select(User).where(User.username == username))
    if existing_user.scalars().first():
        raise HTTPException(status_code=400, detail="Username already exists")

    new_user = User(
        telegram_id=t_id,
        username=username,
        hashed_password=get_password_hash(password),
    )
    db.add(new_user)
    await db.commit() # Асинхронный коммит
    return RedirectResponse(url="/login/", status_code=status.HTTP_303_SEE_OTHER)

# 3. Создать пользователя через Telegram
@user_router.post("/add_tlg/")
async def add_user_tlg(user_data: UserCreateTlgSchema, db: AsyncSession = Depends(get_db)):
    new_user = User(
        telegram_id=user_data.telegram_id,
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password),
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user

# 4. Изменить пользователя
@user_router.put('/update/{user_id}')
async def change_user(user_id: int, user_upd: UserChangeSchema, db: AsyncSession = Depends(get_db)):
    update_data = {}
    if user_upd.telegram_id is not None:
        update_data["telegram_id"] = user_upd.telegram_id
    if user_upd.username is not None:
        update_data["username"] = user_upd.username
    if user_upd.password is not None:
        update_data["hashed_password"] = get_password_hash(user_upd.password)

    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    query = update(User).where(User.id == user_id).values(**update_data)
    await db.execute(query)
    await db.commit()
    
    return {"status": "updated", "fields": list(update_data.keys())}

# 5. Удалить пользователя
@user_router.delete('/delete/{id}')
async def del_user(id: int, db: AsyncSession = Depends(get_db)):
    await db.execute(delete(User).where(User.id == id))
    await db.commit()
    return {"status": "deleted", "id": id}
