from fastapi import FastAPI, HTTPException, Path, Request, Depends
from sqlalchemy.orm import Session
from typing import List
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from slugify import slugify
from pydantic import BaseModel
from app.backend.db import SessionLocal, engine, User as DBUser, Task as DBTask

app = FastAPI()
templates = Jinja2Templates(directory="templates")


# Зависимость для получения сессии базы данных
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Модели Pydantic
class User(BaseModel):
    id: int
    name: str
    email: str


class Task(BaseModel):
    id: int
    title: str
    content: str
    priority: int
    user_id: int
    completed: bool
    slug: str


# Маршруты для работы с пользователями
@app.post("/user/", response_model=User)
async def create_user(name: str, email: str, db: Session = Depends(get_db)):
    new_user = DBUser(name=name, email=email)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


@app.get("/users", response_model=List[User])
async def get_users(db: Session = Depends(get_db)):
    users = db.query(DBUser).all()
    return users


@app.put("/user/{user_id}", response_model=User)
async def update_user(user_id: int, name: str, email: str, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if user:
        user.name = name
        user.email = email
        db.commit()
        db.refresh(user)
        return user
    raise HTTPException(status_code=404, detail="Пользователь не найден")


@app.delete("/user/{user_id}", response_model=User)
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if user:
        # Найти все задачи, связанные с этим пользователем
        tasks = db.query(DBTask).filter(DBTask.user_id == user_id).all()
        for task in tasks:
            db.delete(task)  # Удалить каждую задачу
        db.commit()  # Зафиксировать изменения в базе данных
        db.delete(user)  # Удалить пользователя
        db.commit()  # Зафиксировать изменения в базе данных
        return user
    raise HTTPException(status_code=404, detail="Пользователь не найден")


# Маршруты для работы с задачами
@app.post("/task/", response_model=Task)
async def create_task(title: str, content: str, priority: int, user_id: int, db: Session = Depends(get_db)):
    slug = slugify(title)
    new_task = DBTask(title=title, content=content, priority=priority, user_id=user_id, slug=slug)
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    return new_task


@app.get("/tasks", response_model=List[Task])
async def get_all_tasks(db: Session = Depends(get_db)):
    tasks = db.query(DBTask).all()
    return tasks


@app.put("/task/{task_id}", response_model=Task)
async def update_task(task_id: int, title: str, content: str, priority: int, user_id: int, completed: bool,
                      db: Session = Depends(get_db)):
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if task:
        task.title = title
        task.content = content
        task.priority = priority
        task.user_id = user_id
        task.completed = completed
        db.commit()
        db.refresh(task)
        return task
    raise HTTPException(status_code=404, detail="Задача не найдена")


@app.delete("/task/{task_id}", response_model=Task)
async def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(DBTask).filter(DBTask.id == task_id).first()
    if task:
        db.delete(task)
        db.commit()
        return task
    raise HTTPException(status_code=404, detail="Задача не найдена")
