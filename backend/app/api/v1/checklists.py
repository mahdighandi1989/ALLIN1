"""
Checklists API Routes
روت‌های مدیریت چک‌لیست و تسک‌ها
"""
from typing import Optional, List
from datetime import date, datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel

from app.core.security import get_current_user, TokenData, require_permission

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
    checklist_type: str  # Regulatory, Facility, KYC, etc.
    title: str
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
    priority: str = "medium"  # low, medium, high, urgent
    due_date: Optional[date] = None
    follow_up_date: Optional[date] = None


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[date] = None
    notes: Optional[str] = None


# ========== Routes ==========
@router.get("/")
async def list_checklists(
    customer_id: Optional[str] = None,
    checklist_type: Optional[str] = None,
    status: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user)
):
    """
    لیست چک‌لیست‌ها
    """
    checklists = [
        {
            "id": "CKL-001",
            "customer_id": "cust-001",
            "facility_id": "FAC-001",
            "checklist_type": "Regulatory",
            "title": "Annual Review Checklist",
            "status": "in_progress",
            "total_items": 15,
            "completed_items": 10,
            "progress_percentage": 67,
            "due_date": "2025-02-28",
            "created_at": "2025-01-01T09:00:00"
        }
    ]

    return {"items": checklists, "total": len(checklists), "page": page}


@router.post("/")
async def create_checklist(
    checklist: ChecklistCreate,
    current_user: TokenData = Depends(require_permission("write:checklists"))
):
    """
    ایجاد چک‌لیست جدید
    """
    new_checklist = {
        "id": f"CKL-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        **checklist.model_dump(),
        "status": "draft",
        "total_items": len(checklist.items) if checklist.items else 0,
        "completed_items": 0,
        "progress_percentage": 0,
        "created_at": datetime.utcnow().isoformat()
    }

    return new_checklist


@router.get("/{checklist_id}")
async def get_checklist(
    checklist_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت جزئیات چک‌لیست
    """
    checklist = {
        "id": checklist_id,
        "customer_id": "cust-001",
        "facility_id": "FAC-001",
        "checklist_type": "Regulatory",
        "title": "Annual Review Checklist",
        "status": "in_progress",
        "total_items": 15,
        "completed_items": 10,
        "progress_percentage": 67,
        "due_date": "2025-02-28",
        "items": [
            {"id": "CLI-001", "title": "Trade License", "is_completed": True, "is_required": True},
            {"id": "CLI-002", "title": "Passport Copy", "is_completed": True, "is_required": True},
            {"id": "CLI-003", "title": "Emirates ID", "is_completed": False, "is_required": True},
            {"id": "CLI-004", "title": "Financial Statements", "is_completed": False, "is_required": True},
        ],
        "created_at": "2025-01-01T09:00:00"
    }

    return checklist


@router.put("/{checklist_id}/items/{item_id}")
async def update_checklist_item(
    checklist_id: str,
    item_id: str,
    item: ChecklistItemUpdate,
    current_user: TokenData = Depends(require_permission("write:checklists"))
):
    """
    بروزرسانی آیتم چک‌لیست
    """
    updated_item = {
        "id": item_id,
        "checklist_id": checklist_id,
        "is_completed": item.is_completed,
        "is_applicable": item.is_applicable,
        "notes": item.notes,
        "updated_at": datetime.utcnow().isoformat(),
        "updated_by": current_user.user_id
    }

    return updated_item


# ========== Tasks ==========
@router.get("/tasks/pending")
async def get_pending_tasks(
    customer_id: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت تسک‌های معلق
    """
    tasks = [
        {
            "id": "TSK-001",
            "title": "Follow up on Trade License renewal",
            "customer_id": "cust-001",
            "customer_name": "ABC Trading LLC",
            "priority": "high",
            "status": "pending",
            "due_date": "2025-01-15",
            "days_overdue": 0
        },
        {
            "id": "TSK-002",
            "title": "Collect updated financial statements",
            "customer_id": "cust-002",
            "customer_name": "XYZ Corp",
            "priority": "medium",
            "status": "pending",
            "due_date": "2025-01-20",
            "days_overdue": 0
        }
    ]

    if customer_id:
        tasks = [t for t in tasks if t["customer_id"] == customer_id]

    if priority:
        tasks = [t for t in tasks if t["priority"] == priority]

    return {"items": tasks, "total": len(tasks)}


@router.post("/tasks")
async def create_task(
    task: TaskCreate,
    current_user: TokenData = Depends(require_permission("write:tasks"))
):
    """
    ایجاد تسک جدید
    """
    new_task = {
        "id": f"TSK-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        **task.model_dump(),
        "status": "pending",
        "created_by": current_user.user_id,
        "created_at": datetime.utcnow().isoformat()
    }

    return new_task


@router.put("/tasks/{task_id}")
async def update_task(
    task_id: str,
    task: TaskUpdate,
    current_user: TokenData = Depends(require_permission("write:tasks"))
):
    """
    بروزرسانی تسک
    """
    updated_task = {
        "id": task_id,
        **{k: v for k, v in task.model_dump().items() if v is not None},
        "updated_by": current_user.user_id,
        "updated_at": datetime.utcnow().isoformat()
    }

    return updated_task


@router.post("/tasks/{task_id}/complete")
async def complete_task(
    task_id: str,
    notes: Optional[str] = None,
    current_user: TokenData = Depends(require_permission("write:tasks"))
):
    """
    تکمیل تسک
    """
    return {
        "id": task_id,
        "status": "completed",
        "completed_by": current_user.user_id,
        "completed_at": datetime.utcnow().isoformat(),
        "notes": notes
    }


@router.get("/templates")
async def get_checklist_templates(
    checklist_type: Optional[str] = None,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت قالب‌های چک‌لیست
    """
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
        }
    ]

    if checklist_type:
        templates = [t for t in templates if t["type"] == checklist_type]

    return {"items": templates}
