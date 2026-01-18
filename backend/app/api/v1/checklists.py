"""
Checklists API Routes
روت‌های مدیریت چک‌لیست و تسک‌ها - با عملیات واقعی دیتابیس
"""
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_
from sqlalchemy.orm import selectinload

from app.core.security import get_current_user, TokenData, require_permission
from app.core.database import get_db
from app.models.checklist import Checklist, ChecklistItem, ChecklistTask, ChecklistStatus, TaskStatus, TaskPriority
from app.models.customer import Customer

router = APIRouter()


# ========== Schemas ==========
class ChecklistItemBase(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_required: bool = True


class ChecklistCreate(BaseModel):
    customer_id: str
    facility_id: Optional[str] = None
    checklist_type: str
    title: str
    description: Optional[str] = None
    due_date: Optional[date] = None
    items: Optional[List[ChecklistItemBase]] = None


class ChecklistItemUpdate(BaseModel):
    is_completed: Optional[bool] = None
    is_applicable: Optional[bool] = None
    notes: Optional[str] = None


class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    customer_id: Optional[str] = None
    checklist_id: Optional[str] = None
    priority: str = "Medium"
    due_date: Optional[date] = None
    follow_up_date: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None


# ========== Helper Functions ==========
def checklist_to_dict(checklist: Checklist) -> dict:
    """Convert Checklist model to dict"""
    return {
        "id": checklist.id,
        "customer_id": checklist.customer_id,
        "facility_id": checklist.facility_id,
        "checklist_type": checklist.checklist_type,
        "title": checklist.title,
        "description": checklist.description,
        "status": checklist.status.value if hasattr(checklist.status, 'value') else str(checklist.status),
        "total_items": checklist.total_items or 0,
        "completed_items": checklist.completed_items or 0,
        "progress_percentage": checklist.progress_percentage or 0,
        "due_date": checklist.due_date.isoformat() if checklist.due_date else None,
        "assigned_to": checklist.assigned_to,
        "notes": checklist.notes,
        "created_at": checklist.created_at.isoformat() if checklist.created_at else datetime.utcnow().isoformat(),
        "updated_at": checklist.updated_at.isoformat() if checklist.updated_at else datetime.utcnow().isoformat()
    }


def task_to_dict(task: ChecklistTask, customer_name: str = None) -> dict:
    """Convert ChecklistTask model to dict"""
    return {
        "id": task.id,
        "title": task.title,
        "description": task.description,
        "customer_id": task.customer_id,
        "customer_name": customer_name,
        "checklist_id": task.checklist_id,
        "priority": task.priority.value if hasattr(task.priority, 'value') else str(task.priority),
        "status": task.status.value if hasattr(task.status, 'value') else str(task.status),
        "due_date": task.due_date.isoformat() if task.due_date else None,
        "follow_up_date": task.follow_up_date.isoformat() if task.follow_up_date else None,
        "notes": task.notes,
        "days_overdue": task.days_overdue if hasattr(task, 'days_overdue') else 0,
        "created_at": task.created_at.isoformat() if task.created_at else datetime.utcnow().isoformat()
    }


# ========== Routes ==========
@router.get("/")
async def list_checklists(
    customer_id: Optional[str] = None,
    checklist_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    لیست چک‌لیست‌ها
    """
    # Build query
    query = select(Checklist).where(Checklist.is_deleted == False)

    # Apply filters
    if customer_id:
        query = query.where(Checklist.customer_id == customer_id)

    if checklist_type:
        query = query.where(Checklist.checklist_type == checklist_type)

    if status:
        try:
            ckl_status = ChecklistStatus(status)
            query = query.where(Checklist.status == ckl_status)
        except ValueError:
            pass

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(Checklist.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    # Execute query
    result = await db.execute(query)
    checklists = result.scalars().all()

    items = [checklist_to_dict(c) for c in checklists]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 1
    }


@router.post("/")
async def create_checklist(
    checklist: ChecklistCreate,
    current_user: TokenData = Depends(require_permission("write:checklists")),
    db: AsyncSession = Depends(get_db)
):
    """
    ایجاد چک‌لیست جدید
    """
    # Check customer exists
    customer_result = await db.execute(
        select(Customer).where(
            and_(Customer.id == checklist.customer_id, Customer.is_deleted == False)
        )
    )
    if not customer_result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Customer not found")

    # Create checklist
    new_checklist = Checklist(
        customer_id=checklist.customer_id,
        facility_id=checklist.facility_id,
        checklist_type=checklist.checklist_type,
        title=checklist.title,
        description=checklist.description,
        status=ChecklistStatus.DRAFT,
        due_date=checklist.due_date,
        total_items=len(checklist.items) if checklist.items else 0,
        completed_items=0,
        progress_percentage=0,
        created_by=current_user.user_id
    )

    db.add(new_checklist)
    await db.flush()  # Get the ID

    # Add items if provided
    if checklist.items:
        for idx, item_data in enumerate(checklist.items):
            item = ChecklistItem(
                checklist_id=new_checklist.id,
                title=item_data.title,
                description=item_data.description,
                category=item_data.category,
                is_required=item_data.is_required,
                order=idx,
                created_by=current_user.user_id
            )
            db.add(item)

    await db.commit()
    await db.refresh(new_checklist)

    return checklist_to_dict(new_checklist)


@router.get("/{checklist_id}")
async def get_checklist(
    checklist_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت جزئیات چک‌لیست
    """
    result = await db.execute(
        select(Checklist).options(selectinload(Checklist.items)).where(
            and_(Checklist.id == checklist_id, Checklist.is_deleted == False)
        )
    )
    checklist = result.scalar_one_or_none()

    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    response = checklist_to_dict(checklist)
    response["items"] = [{
        "id": item.id,
        "title": item.title,
        "description": item.description,
        "category": item.category,
        "is_completed": item.is_completed,
        "is_required": item.is_required,
        "is_applicable": item.is_applicable,
        "completed_date": item.completed_date.isoformat() if item.completed_date else None,
        "notes": item.notes,
        "order": item.order
    } for item in sorted(checklist.items, key=lambda x: x.order or 0)]

    return response


@router.delete("/{checklist_id}")
async def delete_checklist(
    checklist_id: str,
    current_user: TokenData = Depends(require_permission("delete:checklists")),
    db: AsyncSession = Depends(get_db)
):
    """
    حذف چک‌لیست
    """
    result = await db.execute(
        select(Checklist).where(
            and_(Checklist.id == checklist_id, Checklist.is_deleted == False)
        )
    )
    checklist = result.scalar_one_or_none()

    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    # Soft delete
    checklist.is_deleted = True
    checklist.deleted_at = datetime.utcnow()
    checklist.deleted_by = current_user.user_id
    await db.commit()

    return {"message": f"Checklist {checklist_id} deleted successfully", "success": True}


class ChecklistItemCreate(BaseModel):
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    is_required: bool = True
    due_date: Optional[date] = None


@router.post("/{checklist_id}/items")
async def add_checklist_item(
    checklist_id: str,
    item: ChecklistItemCreate,
    current_user: TokenData = Depends(require_permission("write:checklists")),
    db: AsyncSession = Depends(get_db)
):
    """
    افزودن آیتم جدید به چک‌لیست
    Add a new item to an existing checklist
    """
    # Verify checklist exists
    result = await db.execute(
        select(Checklist).options(selectinload(Checklist.items)).where(
            and_(Checklist.id == checklist_id, Checklist.is_deleted == False)
        )
    )
    checklist = result.scalar_one_or_none()

    if not checklist:
        raise HTTPException(status_code=404, detail="Checklist not found")

    # Determine order (add at end)
    max_order = max([i.order or 0 for i in checklist.items], default=0) if checklist.items else 0

    # Create new item
    new_item = ChecklistItem(
        checklist_id=checklist_id,
        title=item.title,
        description=item.description,
        category=item.category,
        is_required=item.is_required,
        due_date=item.due_date,
        order=max_order + 1,
        is_completed=False,
        is_applicable=True,
        created_by=current_user.user_id
    )

    db.add(new_item)

    # Update checklist total items
    checklist.total_items = (checklist.total_items or 0) + 1
    checklist.calculate_progress()

    await db.commit()
    await db.refresh(new_item)

    return {
        "id": new_item.id,
        "checklist_id": checklist_id,
        "title": new_item.title,
        "description": new_item.description,
        "category": new_item.category,
        "is_required": new_item.is_required,
        "is_completed": new_item.is_completed,
        "is_applicable": new_item.is_applicable,
        "due_date": new_item.due_date.isoformat() if new_item.due_date else None,
        "order": new_item.order,
        "created_at": datetime.utcnow().isoformat()
    }


@router.put("/{checklist_id}/items/{item_id}")
async def update_checklist_item(
    checklist_id: str,
    item_id: str,
    item_update: ChecklistItemUpdate,
    current_user: TokenData = Depends(require_permission("write:checklists")),
    db: AsyncSession = Depends(get_db)
):
    """
    بروزرسانی آیتم چک‌لیست
    """
    result = await db.execute(
        select(ChecklistItem).where(
            and_(ChecklistItem.id == item_id, ChecklistItem.checklist_id == checklist_id)
        )
    )
    item = result.scalar_one_or_none()

    if not item:
        raise HTTPException(status_code=404, detail="Checklist item not found")

    # Update fields
    if item_update.is_completed is not None:
        item.is_completed = item_update.is_completed
        if item_update.is_completed:
            item.completed_date = date.today()
            item.completed_by = current_user.user_id
        else:
            item.completed_date = None
            item.completed_by = None

    if item_update.is_applicable is not None:
        item.is_applicable = item_update.is_applicable

    if item_update.notes is not None:
        item.notes = item_update.notes

    item.updated_by = current_user.user_id
    await db.commit()

    # Update checklist progress
    checklist_result = await db.execute(
        select(Checklist).options(selectinload(Checklist.items)).where(Checklist.id == checklist_id)
    )
    checklist = checklist_result.scalar_one_or_none()
    if checklist:
        total = len([i for i in checklist.items if i.is_applicable])
        completed = len([i for i in checklist.items if i.is_completed and i.is_applicable])
        checklist.total_items = total
        checklist.completed_items = completed
        checklist.calculate_progress()

        # Update status
        if completed == total and total > 0:
            checklist.status = ChecklistStatus.COMPLETED
            checklist.completed_date = date.today()
        elif completed > 0:
            checklist.status = ChecklistStatus.IN_PROGRESS

        await db.commit()

    return {
        "id": item.id,
        "checklist_id": checklist_id,
        "is_completed": item.is_completed,
        "is_applicable": item.is_applicable,
        "notes": item.notes,
        "updated_at": datetime.utcnow().isoformat(),
        "updated_by": current_user.user_id
    }


# ========== Tasks ==========
@router.get("/tasks/pending")
async def get_pending_tasks(
    customer_id: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت تسک‌های معلق
    """
    query = select(ChecklistTask).where(
        and_(
            ChecklistTask.is_deleted == False,
            ChecklistTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS])
        )
    )

    if customer_id:
        query = query.where(ChecklistTask.customer_id == customer_id)

    if priority:
        try:
            task_priority = TaskPriority(priority)
            query = query.where(ChecklistTask.priority == task_priority)
        except ValueError:
            pass

    query = query.order_by(ChecklistTask.due_date.asc().nullslast())
    result = await db.execute(query)
    tasks = result.scalars().all()

    # Get customer names
    customer_names = {}
    if tasks:
        customer_ids = list(set(t.customer_id for t in tasks if t.customer_id))
        if customer_ids:
            customers_result = await db.execute(
                select(Customer).where(Customer.id.in_(customer_ids))
            )
            for c in customers_result.scalars():
                customer_names[c.id] = c.customer_name

    items = [task_to_dict(t, customer_names.get(t.customer_id)) for t in tasks]

    return {"items": items, "total": len(items)}


@router.get("/tasks/all")
async def list_all_tasks(
    customer_id: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    لیست همه تسک‌ها
    """
    query = select(ChecklistTask).where(ChecklistTask.is_deleted == False)

    if customer_id:
        query = query.where(ChecklistTask.customer_id == customer_id)

    if status:
        try:
            task_status = TaskStatus(status)
            query = query.where(ChecklistTask.status == task_status)
        except ValueError:
            pass

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply pagination
    query = query.order_by(ChecklistTask.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    tasks = result.scalars().all()

    # Get customer names
    customer_names = {}
    if tasks:
        customer_ids = list(set(t.customer_id for t in tasks if t.customer_id))
        if customer_ids:
            customers_result = await db.execute(
                select(Customer).where(Customer.id.in_(customer_ids))
            )
            for c in customers_result.scalars():
                customer_names[c.id] = c.customer_name

    items = [task_to_dict(t, customer_names.get(t.customer_id)) for t in tasks]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 1
    }


@router.post("/tasks")
async def create_task(
    task: TaskCreate,
    current_user: TokenData = Depends(require_permission("write:tasks")),
    db: AsyncSession = Depends(get_db)
):
    """
    ایجاد تسک جدید
    """
    # Parse priority
    try:
        priority = TaskPriority(task.priority)
    except ValueError:
        priority = TaskPriority.MEDIUM

    new_task = ChecklistTask(
        title=task.title,
        description=task.description,
        customer_id=task.customer_id,
        checklist_id=task.checklist_id,
        priority=priority,
        status=TaskStatus.PENDING,
        due_date=task.due_date,
        follow_up_date=task.follow_up_date,
        assigned_to=current_user.user_id,
        assigned_by=current_user.user_id,
        created_by=current_user.user_id
    )

    db.add(new_task)
    await db.commit()
    await db.refresh(new_task)

    return task_to_dict(new_task)


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: str,
    task_update: TaskUpdate,
    current_user: TokenData = Depends(require_permission("write:tasks")),
    db: AsyncSession = Depends(get_db)
):
    """
    بروزرسانی تسک
    """
    result = await db.execute(
        select(ChecklistTask).where(
            and_(ChecklistTask.id == task_id, ChecklistTask.is_deleted == False)
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Update fields
    update_data = task_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "status":
                try:
                    value = TaskStatus(value)
                except ValueError:
                    continue
            elif field == "priority":
                try:
                    value = TaskPriority(value)
                except ValueError:
                    continue
            setattr(task, field, value)

    task.updated_by = current_user.user_id
    await db.commit()
    await db.refresh(task)

    return task_to_dict(task)


@router.delete("/tasks/{task_id}")
async def delete_task(
    task_id: str,
    current_user: TokenData = Depends(require_permission("delete:tasks")),
    db: AsyncSession = Depends(get_db)
):
    """
    حذف تسک
    """
    result = await db.execute(
        select(ChecklistTask).where(
            and_(ChecklistTask.id == task_id, ChecklistTask.is_deleted == False)
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Soft delete
    task.is_deleted = True
    task.deleted_at = datetime.utcnow()
    task.deleted_by = current_user.user_id
    await db.commit()

    return {"message": f"Task {task_id} deleted successfully", "success": True}


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    notes: Optional[str] = None,
    current_user: TokenData = Depends(require_permission("write:tasks")),
    db: AsyncSession = Depends(get_db)
):
    """
    تکمیل تسک
    """
    result = await db.execute(
        select(ChecklistTask).where(
            and_(ChecklistTask.id == task_id, ChecklistTask.is_deleted == False)
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    task.status = TaskStatus.COMPLETED
    task.completed_date = date.today()
    if notes:
        task.action_taken = notes
    task.updated_by = current_user.user_id

    await db.commit()

    return {
        "id": task_id,
        "status": "Completed",
        "completed_by": current_user.user_id,
        "completed_at": datetime.utcnow().isoformat(),
        "notes": notes,
        "success": True
    }


@router.get("/templates")
async def get_checklist_templates(
    checklist_type: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت قالب‌های چک‌لیست
    """
    # Static templates - these could be stored in database in future
    templates = [
        {
            "id": "TPL-001",
            "name": "Regulatory Checklist - Corporate",
            "type": "Regulatory",
            "items_count": 25,
            "categories": ["Documentation", "KYC", "Financial", "Legal"]
        },
        {
            "id": "TPL-002",
            "name": "Regulatory Checklist - Retail",
            "type": "Regulatory",
            "items_count": 15,
            "categories": ["Documentation", "KYC", "Employment"]
        },
        {
            "id": "TPL-003",
            "name": "Facility Review Checklist",
            "type": "Facility",
            "items_count": 20,
            "categories": ["Security", "Financial", "Compliance"]
        },
        {
            "id": "TPL-004",
            "name": "KYC Checklist",
            "type": "KYC",
            "items_count": 18,
            "categories": ["Identity", "Source of Funds", "PEP Screening"]
        }
    ]

    if checklist_type:
        templates = [t for t in templates if t["type"] == checklist_type]

    return {"items": templates}
