"""
Personal Panel API Routes
روت‌های پنل شخصی کاربر
"""
from typing import Optional, List
from datetime import datetime, date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr

from app.core.security import get_current_user, TokenData

router = APIRouter()


# ========== Schemas ==========
class PersonalNoteCreate(BaseModel):
    title: Optional[str] = None
    content: str
    category: str = "general"
    priority: str = "medium"
    is_todo: bool = False
    has_reminder: bool = False
    reminder_date: Optional[datetime] = None
    tags: Optional[List[str]] = None
    color: Optional[str] = "#ffffff"


class PersonalNoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    priority: Optional[str] = None
    is_done: Optional[bool] = None
    pinned: Optional[bool] = None
    archived: Optional[bool] = None
    tags: Optional[List[str]] = None
    color: Optional[str] = None


class ReminderCreate(BaseModel):
    title: str
    description: Optional[str] = None
    reminder_time: datetime
    repeat_type: Optional[str] = None  # None, Daily, Weekly, Monthly
    notification_type: str = "both"  # email, push, both


class PersonalEmailSettings(BaseModel):
    personal_email: EmailStr
    auto_send_notes: bool = False
    send_reminders: bool = True
    send_daily_summary: bool = False


# ========== Notes ==========
@router.get("/notes")
async def get_personal_notes(
    category: Optional[str] = None,
    is_todo: Optional[bool] = None,
    is_done: Optional[bool] = None,
    pinned: Optional[bool] = None,
    archived: bool = False,
    search: Optional[str] = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت یادداشت‌های شخصی کاربر
    """
    notes = [
        {
            "id": "PNT-001",
            "title": "Follow up with ABC Trading",
            "content": "Need to collect updated financials by end of week",
            "category": "follow_up",
            "priority": "high",
            "is_todo": True,
            "is_done": False,
            "has_reminder": True,
            "reminder_date": "2025-01-15T09:00:00",
            "tags": ["urgent", "customer"],
            "color": "#fef3c7",
            "pinned": True,
            "archived": False,
            "created_at": "2025-01-08T10:30:00"
        },
        {
            "id": "PNT-002",
            "title": "Meeting notes - Jan 7",
            "content": "Discussed new facility request for XYZ Corp...",
            "category": "meeting",
            "priority": "medium",
            "is_todo": False,
            "is_done": False,
            "has_reminder": False,
            "tags": ["meeting"],
            "color": "#dbeafe",
            "pinned": False,
            "archived": False,
            "created_at": "2025-01-07T14:00:00"
        }
    ]

    # Apply filters
    if category:
        notes = [n for n in notes if n["category"] == category]
    if is_todo is not None:
        notes = [n for n in notes if n["is_todo"] == is_todo]
    if is_done is not None:
        notes = [n for n in notes if n["is_done"] == is_done]
    if pinned is not None:
        notes = [n for n in notes if n["pinned"] == pinned]
    if not archived:
        notes = [n for n in notes if not n["archived"]]
    if search:
        search_lower = search.lower()
        notes = [n for n in notes if search_lower in n.get("title", "").lower() or search_lower in n.get("content", "").lower()]

    total = len(notes)
    start = (page - 1) * page_size
    items = notes[start:start + page_size]

    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("/notes")
async def create_personal_note(
    note: PersonalNoteCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """
    ایجاد یادداشت شخصی
    """
    new_note = {
        "id": f"PNT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "user_id": current_user.user_id,
        **note.model_dump(),
        "is_done": False,
        "pinned": False,
        "archived": False,
        "email_sent": False,
        "created_at": datetime.utcnow().isoformat()
    }

    return new_note


@router.get("/notes/{note_id}")
async def get_personal_note(
    note_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت یادداشت شخصی
    """
    note = {
        "id": note_id,
        "user_id": current_user.user_id,
        "title": "Sample Note",
        "content": "This is the content of the note",
        "category": "general",
        "priority": "medium",
        "is_todo": False,
        "is_done": False,
        "has_reminder": False,
        "tags": [],
        "color": "#ffffff",
        "pinned": False,
        "archived": False,
        "created_at": datetime.utcnow().isoformat()
    }

    return note


@router.put("/notes/{note_id}")
async def update_personal_note(
    note_id: str,
    note: PersonalNoteUpdate,
    current_user: TokenData = Depends(get_current_user)
):
    """
    بروزرسانی یادداشت شخصی
    """
    updated = {
        "id": note_id,
        **{k: v for k, v in note.model_dump().items() if v is not None},
        "updated_at": datetime.utcnow().isoformat()
    }

    return updated


@router.delete("/notes/{note_id}")
async def delete_personal_note(
    note_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    حذف یادداشت شخصی
    """
    return {"message": f"Note {note_id} deleted successfully"}


@router.post("/notes/{note_id}/toggle-done")
async def toggle_note_done(
    note_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    تغییر وضعیت تکمیل یادداشت (برای todo)
    """
    return {
        "id": note_id,
        "is_done": True,  # یا False
        "done_date": datetime.utcnow().isoformat()
    }


@router.post("/notes/{note_id}/toggle-pin")
async def toggle_note_pin(
    note_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    تغییر وضعیت پین یادداشت
    """
    return {
        "id": note_id,
        "pinned": True  # یا False
    }


# ========== Reminders ==========
@router.get("/reminders")
async def get_reminders(
    status: Optional[str] = None,  # pending, sent, dismissed
    upcoming_days: int = 7,
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت یادآوری‌های کاربر
    """
    reminders = [
        {
            "id": "RMD-001",
            "title": "Review ABC Trading file",
            "description": "Annual review is due",
            "reminder_time": "2025-01-15T09:00:00",
            "status": "pending",
            "repeat_type": None,
            "notification_type": "both"
        },
        {
            "id": "RMD-002",
            "title": "Weekly report",
            "description": "Prepare weekly activity report",
            "reminder_time": "2025-01-12T17:00:00",
            "status": "pending",
            "repeat_type": "Weekly",
            "notification_type": "email"
        }
    ]

    if status:
        reminders = [r for r in reminders if r["status"] == status]

    return {"items": reminders, "total": len(reminders)}


@router.post("/reminders")
async def create_reminder(
    reminder: ReminderCreate,
    current_user: TokenData = Depends(get_current_user)
):
    """
    ایجاد یادآوری جدید
    """
    new_reminder = {
        "id": f"RMD-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "user_id": current_user.user_id,
        **reminder.model_dump(),
        "status": "pending",
        "created_at": datetime.utcnow().isoformat()
    }

    return new_reminder


@router.post("/reminders/{reminder_id}/dismiss")
async def dismiss_reminder(
    reminder_id: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    رد کردن یادآوری
    """
    return {
        "id": reminder_id,
        "status": "dismissed",
        "dismissed_at": datetime.utcnow().isoformat()
    }


@router.post("/reminders/{reminder_id}/snooze")
async def snooze_reminder(
    reminder_id: str,
    snooze_minutes: int = 15,
    current_user: TokenData = Depends(get_current_user)
):
    """
    به تعویق انداختن یادآوری
    """
    from datetime import timedelta

    snooze_until = datetime.utcnow() + timedelta(minutes=snooze_minutes)

    return {
        "id": reminder_id,
        "status": "snoozed",
        "snooze_until": snooze_until.isoformat()
    }


# ========== Email Settings ==========
@router.get("/email-settings")
async def get_personal_email_settings(
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت تنظیمات ایمیل شخصی
    """
    return {
        "personal_email": "user@example.com",
        "auto_send_notes": False,
        "send_reminders": True,
        "send_daily_summary": False
    }


@router.put("/email-settings")
async def update_personal_email_settings(
    settings: PersonalEmailSettings,
    current_user: TokenData = Depends(get_current_user)
):
    """
    بروزرسانی تنظیمات ایمیل شخصی
    """
    return {
        "message": "Email settings updated",
        "settings": settings.model_dump()
    }


@router.post("/send-notes-to-email")
async def send_notes_to_personal_email(
    note_ids: Optional[List[str]] = None,
    send_all_unsent: bool = False,
    current_user: TokenData = Depends(get_current_user)
):
    """
    ارسال یادداشت‌ها به ایمیل شخصی
    """
    from app.services.email_service import email_service

    # در عمل یادداشت‌ها را از دیتابیس بخوانید
    notes = [
        {"title": "Note 1", "content": "Content 1", "created_at": "2025-01-08"},
        {"title": "Note 2", "content": "Content 2", "created_at": "2025-01-07"}
    ]

    # result = await email_service.send_personal_notes(
    #     to="user@example.com",
    #     notes=notes
    # )

    return {
        "message": "Notes sent to email",
        "notes_count": len(notes)
    }


# ========== Dashboard ==========
@router.get("/dashboard")
async def get_personal_dashboard(
    current_user: TokenData = Depends(get_current_user)
):
    """
    دریافت داشبورد شخصی کاربر
    """
    return {
        "pending_todos": 5,
        "upcoming_reminders": 3,
        "notes_count": 24,
        "today_tasks": [
            {"id": "TSK-001", "title": "Follow up ABC Trading", "priority": "high"},
            {"id": "TSK-002", "title": "Submit weekly report", "priority": "medium"}
        ],
        "recent_notes": [
            {"id": "PNT-001", "title": "Meeting notes", "created_at": "2025-01-08T10:30:00"}
        ],
        "expiring_documents_assigned": [
            {"customer": "ABC Trading", "document": "Trade License", "days_remaining": 15}
        ]
    }


# ========== Quick Actions ==========
@router.post("/quick-note")
async def add_quick_note(
    content: str,
    current_user: TokenData = Depends(get_current_user)
):
    """
    افزودن یادداشت سریع
    """
    note = {
        "id": f"PNT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "user_id": current_user.user_id,
        "content": content,
        "category": "quick",
        "priority": "medium",
        "is_todo": False,
        "created_at": datetime.utcnow().isoformat()
    }

    return note


@router.post("/quick-todo")
async def add_quick_todo(
    title: str,
    due_date: Optional[date] = None,
    priority: str = "medium",
    current_user: TokenData = Depends(get_current_user)
):
    """
    افزودن todo سریع
    """
    todo = {
        "id": f"PNT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        "user_id": current_user.user_id,
        "title": title,
        "content": title,
        "category": "todo",
        "priority": priority,
        "is_todo": True,
        "is_done": False,
        "due_date": str(due_date) if due_date else None,
        "created_at": datetime.utcnow().isoformat()
    }

    return todo
