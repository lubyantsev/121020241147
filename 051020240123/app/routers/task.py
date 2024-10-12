from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.models.task import Task as DBTask
from app.models.user import User
from app.schemas import CreateTask, UpdateTask
from app.backend.db_depends import get_db
from slugify import slugify
from typing import List

from .user import users

router = APIRouter(prefix="/task", tags=["task"])

# Обработчик для использования базы данных
@router.get("/", response_model=List[DBTask])
async def all_tasks(db: Session = Depends(get_db)):
    tasks = db.query(DBTask).all()
    return tasks

@router.get("/{task_id}", response_model=DBTask)
async def task_by_id(task_id: int, db: Session = Depends(get_db)):
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_task(create_task: CreateTask, user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User was not found")

    # Создание новой задачи
    new_task = DBTask(**create_task.dict(), user_id=user_id, slug=slugify(create_task.title), completed=False)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return {"status_code": status.HTTP_201_CREATED, "transaction": "Successful"}

@router.put("/update/{task_id}", response_model=DBTask)
async def update_task(task_id: int, update_task: UpdateTask, db: Session = Depends(get_db)):
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Обновление полей задачи
    for key, value in update_task.dict().items():
        setattr(task, key, value)

    db.commit()
    db.refresh(task)
    return task

@router.delete("/delete/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    db.delete(task)
    db.commit()

# Пример кода для работы с задачами в памяти (для тестирования)
tasks = []

@router.get("/memory/", response_model=List[DBTask])
async def all_memory_tasks():
    return tasks

@router.get("/memory/{task_id}", response_model=DBTask)
async def memory_task_by_id(task_id: int):
    task = next((task for task in tasks if task.id == task_id), None)
    if task:
        return task
    raise HTTPException(status_code=404, detail="Task not found")

@router.post("/memory/create", status_code=status.HTTP_201_CREATED)
async def memory_create_task(task: CreateTask, user_id: int):
    if not any(user.id == user_id for user in users):  # Проверка на существование пользователя
        raise HTTPException(status_code=404, detail="User was not found")

    task_id = tasks[-1].id + 1 if tasks else 1
    slug = slugify(task.title)
    new_task = DBTask(
        id=task_id,
        title=task.title,
        content=task.content,
        priority=task.priority,
        user_id=user_id,
        completed=False,
        slug=slug
    )
    tasks.append(new_task)
    return {'status_code': status.HTTP_201_CREATED, 'transaction': 'Successful'}

@router.put("/memory/update/{task_id}", response_model=DBTask)
async def memory_update_task(task_id: int, task: CreateTask):
    for t in tasks:
        if t.id == task_id:
            t.title = task.title
            t.content = task.content
            t.priority = task.priority
            return t
    raise HTTPException(status_code=404, detail="Task not found")