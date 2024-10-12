from fastapi import APIRouter, HTTPException, Depends, status
from sqlalchemy.orm import Session
from app.models.user import User as DBUser
from app.schemas import CreateUser, UpdateUser  # Предполагается, что такие схемы у вас есть
from app.backend.db_depends import get_db
from pydantic import BaseModel
from typing import List

from main1 import Task

router = APIRouter(prefix="/user", tags=["user"])

# Модель для пользователей в памяти
class User(BaseModel):
    id: int
    name: str
    email: str

# Список пользователей в памяти (для тестирования)
users = []

# Маршруты для работы с базой данных
@router.get("/db/", response_model=list[DBUser])
async def all_db_users(db: Session = Depends(get_db)):
    users = db.query(DBUser).all()
    return users

@router.get("/db/{user_id}", response_model=DBUser)
async def db_user_by_id(user_id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.post("/db/create", response_model=DBUser, status_code=status.HTTP_201_CREATED)
async def create_db_user(create_user: CreateUser, db: Session = Depends(get_db)):
    new_user = DBUser(**create_user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@router.put("/db/update/{user_id}", response_model=DBUser)
async def update_db_user(user_id: int, update_user: UpdateUser, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    for key, value in update_user.dict().items():
        setattr(user, key, value)

    db.commit()
    db.refresh(user)
    return user

@router.delete("/db/delete/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_db_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(DBUser).filter(DBUser.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

# Маршруты для работы с пользователями в памяти
@router.get("/", response_model=List[User])
async def all_users():
    return users

@router.get("/{user_id}", response_model=User)
async def user_by_id(user_id: int):
    user = next((user for user in users if user.id == user_id), None)
    if user:
        return user
    raise HTTPException(status_code=404, detail="User not found")

@router.post("/", response_model=User, status_code=status.HTTP_201_CREATED)
async def create_user(name: str, email: str):
    user_id = users[-1].id + 1 if users else 1
    new_user = User(id=user_id, name=name, email=email)
    users.append(new_user)
    return new_user

@router.put("/{user_id}", response_model=User)
async def update_user(user_id: int, name: str, email: str):
    for user in users:
        if user.id == user_id:
            user.name = name
            user.email = email
            return user
    raise HTTPException(status_code=404, detail="User not found")

@router.delete("/{user_id}", response_model=User)
async def delete_user(user_id: int):
    user_to_delete = next((user for user in users if user.id == user_id), None)
    if user_to_delete:
        # Удаляем все задачи, связанные с пользователем
        global tasks
        tasks = [task for task in tasks if task.user_id != user_id]
        users.remove(user_to_delete)
        return user_to_delete
    raise HTTPException(status_code=404, detail="User not found")

@router.get("/{user_id}/tasks", response_model=List[Task])
async def tasks_by_user_id(user_id: int):
    user_tasks = [task for task in tasks if task.user_id == user_id]
    return user_tasks