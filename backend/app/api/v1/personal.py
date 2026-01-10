"""
Personal Panel API Routes
روت‌های پنل شخصی کاربر - با عملیات واقعی دیتابیس
"""
from typing import Optional, List
from datetime import datetime, date, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, and_

from app.core.security import get_current_user, TokenData
from app.core.database import get_db
from app.models.note import PersonalNote, Reminder, NoteCategory, NotePriority, ReminderStatus
from app.models.user import User
from app.models.checklist import ChecklistTask, TaskStatus

router = APIRouter()


# ========== Schemas ==========
class PersonalNoteCreate(BaseModel):
    title: Optional[str] = None
    content: str
    category: str = "General"
    priority: str = "Medium"
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
    repeat_type: Optional[str] = None
    notification_type: str = "both"


class PersonalEmailSettings(BaseModel):
    personal_email: EmailStr
    auto_send_notes: bool = False
    send_reminders: bool = True
    send_daily_summary: bool = False


# ========== Helper Functions ==========
def note_to_dict(note: PersonalNote) -> dict:
    """Convert PersonalNote to dict"""
    return {
        "id": note.id,
        "title": note.title,
        "content": note.content,
        "category": note.category.value if hasattr(note.category, 'value') else str(note.category),
        "priority": note.priority.value if hasattr(note.priority, 'value') else str(note.priority),
        "is_todo": note.is_todo,
        "is_done": note.is_done,
        "has_reminder": note.has_reminder,
        "reminder_date": note.reminder_date.isoformat() if note.reminder_date else None,
        "tags": note.tags or [],
        "color": note.color or "#ffffff",
        "pinned": note.pinned,
        "archived": note.archived,
        "created_at": note.created_at.isoformat() if note.created_at else datetime.utcnow().isoformat(),
        "updated_at": note.updated_at.isoformat() if note.updated_at else None
    }


def reminder_to_dict(reminder: Reminder) -> dict:
    """Convert Reminder to dict"""
    return {
        "id": reminder.id,
        "title": reminder.title,
        "description": reminder.description,
        "reminder_time": reminder.reminder_time.isoformat() if reminder.reminder_time else None,
        "status": reminder.status.value if hasattr(reminder.status, 'value') else str(reminder.status),
        "repeat_type": reminder.repeat_type,
        "notification_type": reminder.notification_type,
        "snooze_until": reminder.snooze_until.isoformat() if reminder.snooze_until else None,
        "created_at": reminder.created_at.isoformat() if reminder.created_at else datetime.utcnow().isoformat()
    }


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
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت یادداشت‌های شخصی کاربر
    """
    query = select(PersonalNote).where(
        and_(
            PersonalNote.user_id == current_user.user_id,
            PersonalNote.is_deleted == False
        )
    )

    # Apply filters
    if category:
        try:
            cat = NoteCategory(category)
            query = query.where(PersonalNote.category == cat)
        except ValueError:
            pass

    if is_todo is not None:
        query = query.where(PersonalNote.is_todo == is_todo)

    if is_done is not None:
        query = query.where(PersonalNote.is_done == is_done)

    if pinned is not None:
        query = query.where(PersonalNote.pinned == pinned)

    query = query.where(PersonalNote.archived == archived)

    if search:
        search_filter = or_(
            PersonalNote.title.ilike(f"%{search}%"),
            PersonalNote.content.ilike(f"%{search}%")
        )
        query = query.where(search_filter)

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Apply ordering (pinned first, then by created_at)
    query = query.order_by(PersonalNote.pinned.desc(), PersonalNote.created_at.desc())
    query = query.offset((page - 1) * page_size).limit(page_size)

    result = await db.execute(query)
    notes = result.scalars().all()

    items = [note_to_dict(n) for n in notes]

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": (total + page_size - 1) // page_size if total > 0 else 1
    }


@router.post("/notes")
async def create_personal_note(
    note: PersonalNoteCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ایجاد یادداشت شخصی
    """
    # Parse category and priority
    try:
        category = NoteCategory(note.category)
    except ValueError:
        category = NoteCategory.GENERAL

    try:
        priority = NotePriority(note.priority)
    except ValueError:
        priority = NotePriority.MEDIUM

    new_note = PersonalNote(
        user_id=current_user.user_id,
        title=note.title,
        content=note.content,
        category=category,
        priority=priority,
        is_todo=note.is_todo,
        is_done=False,
        has_reminder=note.has_reminder,
        reminder_date=note.reminder_date,
        tags=note.tags or [],
        color=note.color or "#ffffff",
        pinned=False,
        archived=False,
        created_by=current_user.user_id
    )

    db.add(new_note)
    await db.commit()
    await db.refresh(new_note)

    return note_to_dict(new_note)


@router.get("/notes/{note_id}")
async def get_personal_note(
    note_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت یادداشت شخصی
    """
    result = await db.execute(
        select(PersonalNote).where(
            and_(
                PersonalNote.id == note_id,
                PersonalNote.user_id == current_user.user_id,
                PersonalNote.is_deleted == False
            )
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    return note_to_dict(note)


@router.put("/notes/{note_id}")
async def update_personal_note(
    note_id: str,
    note_update: PersonalNoteUpdate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    بروزرسانی یادداشت شخصی
    """
    result = await db.execute(
        select(PersonalNote).where(
            and_(
                PersonalNote.id == note_id,
                PersonalNote.user_id == current_user.user_id,
                PersonalNote.is_deleted == False
            )
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Update fields
    update_data = note_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if field == "category":
                try:
                    value = NoteCategory(value)
                except ValueError:
                    continue
            elif field == "priority":
                try:
                    value = NotePriority(value)
                except ValueError:
                    continue
            elif field == "is_done" and value:
                note.done_date = datetime.utcnow()
            setattr(note, field, value)

    note.updated_by = current_user.user_id
    await db.commit()
    await db.refresh(note)

    return note_to_dict(note)


@router.delete("/notes/{note_id}")
async def delete_personal_note(
    note_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    حذف یادداشت شخصی
    """
    result = await db.execute(
        select(PersonalNote).where(
            and_(
                PersonalNote.id == note_id,
                PersonalNote.user_id == current_user.user_id,
                PersonalNote.is_deleted == False
            )
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Soft delete
    note.is_deleted = True
    note.deleted_at = datetime.utcnow()
    note.deleted_by = current_user.user_id
    await db.commit()

    return {"message": f"Note {note_id} deleted successfully", "success": True}


@router.post("/notes/{note_id}/toggle-done")
async def toggle_note_done(
    note_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    تغییر وضعیت تکمیل یادداشت (برای todo)
    """
    result = await db.execute(
        select(PersonalNote).where(
            and_(
                PersonalNote.id == note_id,
                PersonalNote.user_id == current_user.user_id,
                PersonalNote.is_deleted == False
            )
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.is_done = not note.is_done
    note.done_date = datetime.utcnow() if note.is_done else None
    note.updated_by = current_user.user_id
    await db.commit()

    return {
        "id": note_id,
        "is_done": note.is_done,
        "done_date": note.done_date.isoformat() if note.done_date else None,
        "success": True
    }


@router.post("/notes/{note_id}/toggle-pin")
async def toggle_note_pin(
    note_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    تغییر وضعیت پین یادداشت
    """
    result = await db.execute(
        select(PersonalNote).where(
            and_(
                PersonalNote.id == note_id,
                PersonalNote.user_id == current_user.user_id,
                PersonalNote.is_deleted == False
            )
        )
    )
    note = result.scalar_one_or_none()

    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    note.pinned = not note.pinned
    note.updated_by = current_user.user_id
    await db.commit()

    return {
        "id": note_id,
        "pinned": note.pinned,
        "success": True
    }


# ========== Reminders ==========
@router.get("/reminders")
async def get_reminders(
    status: Optional[str] = None,
    upcoming_days: int = 7,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت یادآوری‌های کاربر
    """
    query = select(Reminder).where(Reminder.user_id == current_user.user_id)

    if status:
        try:
            rem_status = ReminderStatus(status)
            query = query.where(Reminder.status == rem_status)
        except ValueError:
            pass
    else:
        # Default: show pending reminders within upcoming_days
        threshold = datetime.utcnow() + timedelta(days=upcoming_days)
        query = query.where(
            and_(
                Reminder.status == ReminderStatus.PENDING,
                Reminder.reminder_time <= threshold
            )
        )

    query = query.order_by(Reminder.reminder_time.asc())
    result = await db.execute(query)
    reminders = result.scalars().all()

    items = [reminder_to_dict(r) for r in reminders]

    return {"items": items, "total": len(items)}


@router.post("/reminders")
async def create_reminder(
    reminder: ReminderCreate,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ایجاد یادآوری جدید
    """
    new_reminder = Reminder(
        user_id=current_user.user_id,
        title=reminder.title,
        description=reminder.description,
        reminder_time=reminder.reminder_time,
        repeat_type=reminder.repeat_type,
        notification_type=reminder.notification_type,
        status=ReminderStatus.PENDING,
        created_by=current_user.user_id
    )

    db.add(new_reminder)
    await db.commit()
    await db.refresh(new_reminder)

    return reminder_to_dict(new_reminder)


@router.delete("/reminders/{reminder_id}")
async def delete_reminder(
    reminder_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    حذف یادآوری
    """
    result = await db.execute(
        select(Reminder).where(
            and_(Reminder.id == reminder_id, Reminder.user_id == current_user.user_id)
        )
    )
    reminder = result.scalar_one_or_none()

    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    await db.delete(reminder)
    await db.commit()

    return {"message": f"Reminder {reminder_id} deleted successfully", "success": True}


@router.post("/reminders/{reminder_id}/dismiss")
async def dismiss_reminder(
    reminder_id: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    رد کردن یادآوری
    """
    result = await db.execute(
        select(Reminder).where(
            and_(Reminder.id == reminder_id, Reminder.user_id == current_user.user_id)
        )
    )
    reminder = result.scalar_one_or_none()

    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    reminder.status = ReminderStatus.DISMISSED
    reminder.dismissed_at = datetime.utcnow()
    await db.commit()

    return {
        "id": reminder_id,
        "status": "Dismissed",
        "dismissed_at": datetime.utcnow().isoformat(),
        "success": True
    }


@router.post("/reminders/{reminder_id}/snooze")
async def snooze_reminder(
    reminder_id: str,
    snooze_minutes: int = 15,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    به تعویق انداختن یادآوری
    """
    result = await db.execute(
        select(Reminder).where(
            and_(Reminder.id == reminder_id, Reminder.user_id == current_user.user_id)
        )
    )
    reminder = result.scalar_one_or_none()

    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")

    snooze_until = datetime.utcnow() + timedelta(minutes=snooze_minutes)
    reminder.status = ReminderStatus.SNOOZED
    reminder.snooze_until = snooze_until
    await db.commit()

    return {
        "id": reminder_id,
        "status": "Snoozed",
        "snooze_until": snooze_until.isoformat(),
        "success": True
    }


# ========== Email Settings ==========
@router.get("/email-settings")
async def get_personal_email_settings(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت تنظیمات ایمیل شخصی
    """
    result = await db.execute(
        select(User).where(User.id == current_user.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    notification_settings = user.notification_settings or {}

    return {
        "personal_email": user.personal_email or user.email,
        "auto_send_notes": notification_settings.get("auto_send_notes", False),
        "send_reminders": notification_settings.get("send_reminders", True),
        "send_daily_summary": notification_settings.get("send_daily_summary", False)
    }


@router.put("/email-settings")
async def update_personal_email_settings(
    settings: PersonalEmailSettings,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    بروزرسانی تنظیمات ایمیل شخصی
    """
    result = await db.execute(
        select(User).where(User.id == current_user.user_id)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.personal_email = settings.personal_email
    user.notification_settings = {
        **(user.notification_settings or {}),
        "auto_send_notes": settings.auto_send_notes,
        "send_reminders": settings.send_reminders,
        "send_daily_summary": settings.send_daily_summary
    }

    await db.commit()

    return {
        "message": "Email settings updated",
        "settings": settings.model_dump(),
        "success": True
    }


@router.post("/send-notes-to-email")
async def send_notes_to_personal_email(
    note_ids: Optional[List[str]] = None,
    send_all_unsent: bool = False,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    ارسال یادداشت‌ها به ایمیل شخصی
    """
    # Get user email
    user_result = await db.execute(
        select(User).where(User.id == current_user.user_id)
    )
    user = user_result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    email_to = user.personal_email or user.email

    # Get notes to send
    query = select(PersonalNote).where(
        and_(
            PersonalNote.user_id == current_user.user_id,
            PersonalNote.is_deleted == False
        )
    )

    if note_ids:
        query = query.where(PersonalNote.id.in_(note_ids))
    elif send_all_unsent:
        query = query.where(PersonalNote.email_sent == False)
    else:
        raise HTTPException(status_code=400, detail="Specify note_ids or set send_all_unsent=true")

    result = await db.execute(query)
    notes = result.scalars().all()

    if not notes:
        return {"message": "No notes to send", "notes_count": 0}

    # Mark as sent (actual email sending would be done via email service)
    for note in notes:
        note.email_sent = True
        note.email_sent_date = datetime.utcnow()

    await db.commit()

    return {
        "message": f"Notes queued for sending to {email_to}",
        "notes_count": len(notes),
        "success": True
    }


# ========== Dashboard ==========
@router.get("/dashboard")
async def get_personal_dashboard(
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    دریافت داشبورد شخصی کاربر
    """
    # Get pending todos count
    todos_result = await db.execute(
        select(func.count()).select_from(
            select(PersonalNote).where(
                and_(
                    PersonalNote.user_id == current_user.user_id,
                    PersonalNote.is_todo == True,
                    PersonalNote.is_done == False,
                    PersonalNote.is_deleted == False
                )
            ).subquery()
        )
    )
    pending_todos = todos_result.scalar() or 0

    # Get upcoming reminders count
    reminder_threshold = datetime.utcnow() + timedelta(days=7)
    reminders_result = await db.execute(
        select(func.count()).select_from(
            select(Reminder).where(
                and_(
                    Reminder.user_id == current_user.user_id,
                    Reminder.status == ReminderStatus.PENDING,
                    Reminder.reminder_time <= reminder_threshold
                )
            ).subquery()
        )
    )
    upcoming_reminders = reminders_result.scalar() or 0

    # Get total notes count
    notes_result = await db.execute(
        select(func.count()).select_from(
            select(PersonalNote).where(
                and_(
                    PersonalNote.user_id == current_user.user_id,
                    PersonalNote.is_deleted == False,
                    PersonalNote.archived == False
                )
            ).subquery()
        )
    )
    notes_count = notes_result.scalar() or 0

    # Get today's tasks (assigned to user)
    tasks_result = await db.execute(
        select(ChecklistTask).where(
            and_(
                ChecklistTask.assigned_to == current_user.user_id,
                ChecklistTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
                ChecklistTask.is_deleted == False
            )
        ).order_by(ChecklistTask.due_date.asc().nullslast()).limit(5)
    )
    today_tasks = [{
        "id": t.id,
        "title": t.title,
        "priority": t.priority.value if hasattr(t.priority, 'value') else str(t.priority),
        "due_date": t.due_date.isoformat() if t.due_date else None
    } for t in tasks_result.scalars()]

    # Get recent notes
    recent_notes_result = await db.execute(
        select(PersonalNote).where(
            and_(
                PersonalNote.user_id == current_user.user_id,
                PersonalNote.is_deleted == False,
                PersonalNote.archived == False
            )
        ).order_by(PersonalNote.created_at.desc()).limit(5)
    )
    recent_notes = [{
        "id": n.id,
        "title": n.title or n.content[:50],
        "created_at": n.created_at.isoformat() if n.created_at else None
    } for n in recent_notes_result.scalars()]

    return {
        "pending_todos": pending_todos,
        "upcoming_reminders": upcoming_reminders,
        "notes_count": notes_count,
        "today_tasks": today_tasks,
        "recent_notes": recent_notes,
        "expiring_documents_assigned": []  # Would be populated from customer profiles
    }


# ========== Quick Actions ==========
@router.post("/quick-note")
async def add_quick_note(
    content: str,
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    افزودن یادداشت سریع
    """
    note = PersonalNote(
        user_id=current_user.user_id,
        content=content,
        category=NoteCategory.GENERAL,
        priority=NotePriority.MEDIUM,
        is_todo=False,
        created_by=current_user.user_id
    )

    db.add(note)
    await db.commit()
    await db.refresh(note)

    return note_to_dict(note)


@router.post("/quick-todo")
async def add_quick_todo(
    title: str,
    due_date: Optional[date] = None,
    priority: str = "Medium",
    current_user: TokenData = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    افزودن todo سریع
    """
    try:
        prio = NotePriority(priority)
    except ValueError:
        prio = NotePriority.MEDIUM

    todo = PersonalNote(
        user_id=current_user.user_id,
        title=title,
        content=title,
        category=NoteCategory.GENERAL,
        priority=prio,
        is_todo=True,
        is_done=False,
        created_by=current_user.user_id
    )

    db.add(todo)
    await db.commit()
    await db.refresh(todo)

    return note_to_dict(todo)
