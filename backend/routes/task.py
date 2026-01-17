from datetime import datetime
import os
from typing import List
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import delete, select, update
from sqlalchemy.orm import joinedload, selectinload


from backend.models.models import Task, User
from backend.dependencies.dependency import get_db
from backend.schemas.schemas import TaskCreateSchema, TaskUpdateSchema, TaskDeleteSchema

from bot.bot import bot 

task_router = APIRouter(
    prefix='/task',
    tags=['Tasks']
)

# 1. Показать ВСЕ задачи пользователя
@task_router.get("/show/{user_tg_id}")
async def get_all_tasks(user_tg_id: int, db: AsyncSession = Depends(get_db)):
    user_result = await db.execute(select(User).where(User.telegram_id == user_tg_id))
    user_id = user_result.scalar_one_or_none()
    result = await db.execute(select(Task).where(Task.user_id == user_id.id))
    return result.scalars().all()

# 2. Показать только АКТИВНЫЕ задачи
@task_router.get("/showactive/{user_id}")
async def get_active_tasks(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).where(Task.user_id == user_id, Task.is_completed == False)
    )
    return result.scalars().all()

# 3. Показать только ЗАВЕРШЕННЫЕ задачи
@task_router.get("/showclosed/{user_id}")
async def get_closed_tasks(user_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Task).where(Task.user_id == user_id, Task.is_completed == True)
    )
    return result.scalars().all()

# 4. Добавление новой задачи
@task_router.post("/add/")
async def add_task(task_data: TaskCreateSchema, db: AsyncSession = Depends(get_db)):
    user_query = await db.execute(select(User).where(User.username == task_data.username))
    user = user_query.scalars().first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    new_task = Task(
        title=task_data.title,
        description=task_data.description,
        deadline=task_data.deadline,
        is_completed=False,
        user_id=user.id
    )
    
    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)
    await db.refresh(user)

    if user.telegram_id:
        try:
            deadline_str = new_task.deadline.strftime('%d.%m.%Y') if new_task.deadline else "не указан"
            text = f"✅ **Новая задача создана!**\n\n📌 {new_task.title}\n📝 {new_task.description}\n📅 Срок: {deadline_str}"
            await bot.send_message(user.telegram_id, text, parse_mode="Markdown")
        except Exception as e:
            print(f"Ошибка отправки уведомления: {e}")

    return RedirectResponse(url=f"/tasks/{user.username}", status_code=status.HTTP_303_SEE_OTHER)

# 5. Удаление задачи
@task_router.delete('/delete/')
async def del_task(task_data: TaskDeleteSchema, db: AsyncSession = Depends(get_db)):
    query = await db.execute(select(Task).where(Task.id == task_data.id))
    task_obj = query.scalars().first()
    
    if not task_obj:
        raise HTTPException(status_code=404, detail="Task not found")

    user_query = await db.execute(select(User).where(User.id == task_obj.user_id))
    user = user_query.scalars().first()

    await db.execute(delete(Task).where(Task.id == task_data.id))
    await db.commit()

    if user and user.telegram_id:
        await bot.send_message(user.telegram_id, f"🗑 Задача удалена: {task_obj.title}")

    return {"status": "deleted"}

# 6. Обновление задачи
@task_router.put('/update/')
async def update_task(updating_task: TaskUpdateSchema, db: AsyncSession = Depends(get_db)):
    field = updating_task.field
    new_value = updating_task.new_value

    if field == "is_completed":
        new_value = True if str(new_value).lower() in ['true', '1', 'yes'] else False
    elif field == "deadline":
        try:
            # Превращаем строку "2026-01-17" в объект Python datetime
            new_value = datetime.strptime(new_value, '%Y-%m-%d')
        except (ValueError, TypeError):
            # Если пришла пустая строка или плохой формат — записываем None или выдаем ошибку
            new_value = None

    await db.execute(
        update(Task).where(Task.id == updating_task.id).values({field: new_value})
    )
    await db.commit()

    task_query = await db.execute(
        select(Task)
        .options(joinedload(Task.user)) # Загружаем пользователя через JOIN
        .where(Task.id == updating_task.id)
    )
    task_obj = task_query.scalars().first()

    if task_obj and task_obj.user.telegram_id:
        msg = f"🔄 Задача обновлена!\nПоле *{field}* изменено на: `{new_value}`"
        await bot.send_message(task_obj.user.telegram_id, msg, parse_mode="Markdown")

    return {"status": "updated", "field": field, "value": new_value}
