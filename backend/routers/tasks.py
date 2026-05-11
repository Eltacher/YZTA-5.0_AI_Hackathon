"""Görev yönetimi API endpoint'leri."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from database import get_db
from models import Task, TaskStatus, TaskPriority
from services.workflow_service import workflow_service

router = APIRouter(prefix="/api/tasks", tags=["tasks"])


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    priority: str = "medium"
    due_date: Optional[str] = None
    category: Optional[str] = None
    related_order_id: Optional[int] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None


@router.get("/")
def list_tasks(
    status: Optional[str] = None,
    assigned_to: Optional[str] = None,
    category: Optional[str] = None,
    skip: int = 0, limit: int = 50,
    db: Session = Depends(get_db)
):
    query = db.query(Task)
    if status:
        try:
            query = query.filter(Task.status == TaskStatus(status))
        except ValueError:
            pass
    if assigned_to:
        query = query.filter(Task.assigned_to == assigned_to)
    if category:
        query = query.filter(Task.category == category)
    total = query.count()
    tasks = query.order_by(Task.priority.desc(), Task.due_date.asc()).offset(skip).limit(limit).all()
    return {"total": total, "tasks": [t.to_dict() for t in tasks]}


@router.get("/today")
def today_tasks(db: Session = Depends(get_db)):
    return workflow_service.get_today_tasks(db)


@router.get("/by-assignee")
def tasks_by_assignee(assignee: Optional[str] = None, db: Session = Depends(get_db)):
    return workflow_service.get_tasks_by_assignee(db, assignee)


@router.post("/generate-daily")
def generate_daily(db: Session = Depends(get_db)):
    """Günlük otomatik görev oluştur."""
    tasks = workflow_service.generate_daily_tasks(db)
    return {"generated": len(tasks), "tasks": tasks}


@router.get("/stats")
def task_stats(db: Session = Depends(get_db)):
    total = db.query(Task).count()
    todo = db.query(Task).filter(Task.status == TaskStatus.TODO).count()
    in_progress = db.query(Task).filter(Task.status == TaskStatus.IN_PROGRESS).count()
    done = db.query(Task).filter(Task.status == TaskStatus.DONE).count()
    return {"total": total, "todo": todo, "in_progress": in_progress, "done": done}


@router.post("/")
def create_task(data: TaskCreate, db: Session = Depends(get_db)):
    task = Task(
        title=data.title,
        description=data.description,
        assigned_to=data.assigned_to,
        category=data.category,
        related_order_id=data.related_order_id,
    )
    try:
        task.priority = TaskPriority(data.priority)
    except ValueError:
        task.priority = TaskPriority.MEDIUM
    if data.due_date:
        try:
            task.due_date = datetime.fromisoformat(data.due_date)
        except ValueError:
            pass
    db.add(task)
    db.commit()
    db.refresh(task)
    return task.to_dict()


@router.patch("/{task_id}")
def update_task(task_id: int, data: TaskUpdate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    if data.title:
        task.title = data.title
    if data.description:
        task.description = data.description
    if data.assigned_to:
        task.assigned_to = data.assigned_to
    if data.status:
        try:
            task.status = TaskStatus(data.status)
            if data.status == "done":
                task.completed_at = datetime.utcnow()
        except ValueError:
            pass
    if data.priority:
        try:
            task.priority = TaskPriority(data.priority)
        except ValueError:
            pass
    db.commit()
    db.refresh(task)
    return task.to_dict()


@router.delete("/{task_id}")
def delete_task(task_id: int, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Görev bulunamadı")
    db.delete(task)
    db.commit()
    return {"message": "Görev silindi"}
