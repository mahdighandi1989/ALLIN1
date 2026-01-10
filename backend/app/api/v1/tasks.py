"""
Tasks API
API وظایف سفارشی
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_
from pydantic import BaseModel
from datetime import date

from app.core.database import get_db
from app.core.auth import get_current_user, TokenData
from app.models.task import CustomTask, TaskStatus, TaskPriority

router = APIRouter()


# Schemas
class TaskCreate(BaseModel):
    customer_id: Optional[str] = None
    facility_id: Optional[str] = None
    account_no: Optional[str] = None
    task_name: str
    description: Optional[str] = None
    status: str = "Pending"
    priority: str = "Medium"
    due_date: Optional[date] = None
    follow_up_date: Optional[date] = None
    notes: Optional[str] = None


class TaskUpdate(BaseModel):
    task_name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    follow_up_date: Optional[date] = None
    notes: Optional[str] = None


class TaskResponse(BaseModel):
    id: str
    task_id: Optional[str]
    customer_id: Optional[str]
    facility_id: Optional[str]
    account_no: Optional[str]
    task_name: str
    description: Optional[str]
    status: str
    priority: str
    due_date: Optional[date]
    follow_up_date: Optional[date]
    notes: Optional[str]
    is_active: bool

    class Config:
        from_attributes = True


@router.get("")
async def get_tasks(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = None,
    priority: Optional[str] = None,
    customer_id: Optional[str] = None,
    search: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """دریافت لیست وظایف"""
    query = select(CustomTask).where(CustomTask.is_deleted == False)

    if status:
        query = query.where(CustomTask.status == status)
    if priority:
        query = query.where(CustomTask.priority == priority)
    if customer_id:
        query = query.where(CustomTask.customer_id == customer_id)
    if search:
        query = query.where(
            or_(
                CustomTask.task_name.ilike(f"%{search}%"),
                CustomTask.notes.ilike(f"%{search}%"),
                CustomTask.account_no.ilike(f"%{search}%")
            )
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(CustomTask.created_at.desc()).offset(skip).limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()

    return {
        "items": [
            {
                "id": t.id,
                "task_id": t.task_id,
                "customer_id": t.customer_id,
                "facility_id": t.facility_id,
                "account_no": t.account_no,
                "task_name": t.task_name,
                "description": t.description,
                "status": t.status.value if t.status else "Pending",
                "priority": t.priority.value if t.priority else "Medium",
                "due_date": t.due_date.isoformat() if t.due_date else None,
                "follow_up_date": t.follow_up_date.isoformat() if t.follow_up_date else None,
                "notes": t.notes,
                "is_active": t.is_active,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in tasks
        ],
        "total": total,
        "skip": skip,
        "limit": limit
    }


@router.get("/stats")
async def get_task_stats(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """دریافت آمار وظایف"""
    # Total tasks
    total_result = await db.execute(
        select(func.count()).select_from(CustomTask).where(CustomTask.is_deleted == False)
    )
    total = total_result.scalar() or 0

    # By status
    status_counts = {}
    for status in TaskStatus:
        result = await db.execute(
            select(func.count()).select_from(CustomTask).where(
                CustomTask.is_deleted == False,
                CustomTask.status == status
            )
        )
        status_counts[status.value] = result.scalar() or 0

    # Overdue tasks
    from datetime import date as date_type
    overdue_result = await db.execute(
        select(func.count()).select_from(CustomTask).where(
            CustomTask.is_deleted == False,
            CustomTask.status != TaskStatus.COMPLETED,
            CustomTask.due_date < date_type.today()
        )
    )
    overdue = overdue_result.scalar() or 0

    return {
        "total": total,
        "by_status": status_counts,
        "overdue": overdue
    }


@router.get("/{task_id}")
async def get_task(
    task_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """دریافت یک وظیفه"""
    result = await db.execute(
        select(CustomTask).where(
            CustomTask.id == task_id,
            CustomTask.is_deleted == False
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "id": task.id,
        "task_id": task.task_id,
        "customer_id": task.customer_id,
        "facility_id": task.facility_id,
        "account_no": task.account_no,
        "task_name": task.task_name,
        "description": task.description,
        "status": task.status.value if task.status else "Pending",
        "priority": task.priority.value if task.priority else "Medium",
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "follow_up_date": task.follow_up_date.isoformat() if task.follow_up_date else None,
        "notes": task.notes,
        "is_active": task.is_active,
    }


@router.post("")
async def create_task(
    task_data: TaskCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """ایجاد وظیفه جدید"""
    # Parse status
    try:
        status = TaskStatus(task_data.status)
    except:
        status = TaskStatus.PENDING

    # Parse priority
    try:
        priority = TaskPriority(task_data.priority)
    except:
        priority = TaskPriority.MEDIUM

    task = CustomTask(
        customer_id=task_data.customer_id,
        facility_id=task_data.facility_id,
        account_no=task_data.account_no,
        task_name=task_data.task_name,
        description=task_data.description,
        status=status,
        priority=priority,
        due_date=task_data.due_date,
        follow_up_date=task_data.follow_up_date,
        notes=task_data.notes,
        created_by=current_user.user_id,
    )
    db.add(task)
    await db.commit()
    await db.refresh(task)

    return {"id": task.id, "message": "Task created successfully"}


@router.put("/{task_id}")
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """به‌روزرسانی وظیفه"""
    result = await db.execute(
        select(CustomTask).where(
            CustomTask.id == task_id,
            CustomTask.is_deleted == False
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task_data.task_name is not None:
        task.task_name = task_data.task_name
    if task_data.description is not None:
        task.description = task_data.description
    if task_data.status is not None:
        try:
            task.status = TaskStatus(task_data.status)
        except:
            pass
    if task_data.priority is not None:
        try:
            task.priority = TaskPriority(task_data.priority)
        except:
            pass
    if task_data.due_date is not None:
        task.due_date = task_data.due_date
    if task_data.follow_up_date is not None:
        task.follow_up_date = task_data.follow_up_date
    if task_data.notes is not None:
        task.notes = task_data.notes

    task.updated_by = current_user.user_id
    await db.commit()

    return {"message": "Task updated successfully"}


@router.delete("/{task_id}")
async def delete_task(
    task_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """حذف وظیفه"""
    result = await db.execute(
        select(CustomTask).where(
            CustomTask.id == task_id,
            CustomTask.is_deleted == False
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.is_deleted = True
    task.updated_by = current_user.user_id
    await db.commit()

    return {"message": "Task deleted successfully"}
