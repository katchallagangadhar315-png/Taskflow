from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models.task import Task, TaskPriority, TaskStatus
from app.models.user import User
from app.schemas.task import (
    TaskCreate,
    TaskUpdate,
    TaskResponse,
    TaskMetricsResponse
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.get(
    "/metrics",
    response_model=TaskMetricsResponse,
    summary="Get task metrics and analytics for current user",
    description="Returns aggregate counts of total, pending, in-progress, completed, and overdue tasks."
)
def get_task_metrics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Computes dashboard metrics strictly isolated to the authenticated user.
    """
    user_tasks = db.query(Task).filter(Task.user_id == current_user.id).all()
    now_utc = datetime.now(timezone.utc)

    total = len(user_tasks)
    pending = 0
    in_progress = 0
    completed = 0
    overdue = 0

    for task in user_tasks:
        if task.status == TaskStatus.PENDING:
            pending += 1
        elif task.status == TaskStatus.IN_PROGRESS:
            in_progress += 1
        elif task.status == TaskStatus.COMPLETED:
            completed += 1

        # Calculate overdue: must have a due date in the past and NOT be completed
        if task.due_date and task.status != TaskStatus.COMPLETED:
            due = task.due_date
            if due.tzinfo is None:
                due = due.replace(tzinfo=timezone.utc)
            if due < now_utc:
                overdue += 1

    return TaskMetricsResponse(
        total=total,
        pending=pending,
        in_progress=in_progress,
        completed=completed,
        overdue=overdue
    )


@router.post(
    "/",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new task",
    description="Creates a task associated exclusively with the authenticated user."
)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    1. Ingests task creation payload.
    2. Explicitly binds the task's user_id to current_user.id to guarantee ownership.
    3. Persists the record to MySQL and returns the created task.
    """
    new_task = Task(
        user_id=current_user.id,
        title=task_in.title,
        description=task_in.description,
        priority=task_in.priority,
        status=task_in.status,
        due_date=task_in.due_date
    )

    db.add(new_task)
    db.commit()
    db.refresh(new_task)

    return TaskResponse.from_orm_with_overdue(new_task)


@router.get(
    "/",
    response_model=List[TaskResponse],
    summary="List all tasks for current user with search and filtering",
    description="Fetches tasks belonging to the current user with optional search keywords, status filter, and priority filter."
)
def list_tasks(
    search: Optional[str] = Query(None, description="Keyword search in title and description"),
    status_filter: Optional[TaskStatus] = Query(None, alias="status", description="Filter by status: pending, in_progress, completed"),
    priority_filter: Optional[TaskPriority] = Query(None, alias="priority", description="Filter by priority: low, medium, high"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Enforces user data isolation: ONLY tasks matching Task.user_id == current_user.id are returned.
    """
    query = db.query(Task).filter(Task.user_id == current_user.id)

    # 1. Keyword search (case-insensitive across title and description)
    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(
                Task.title.ilike(search_pattern),
                Task.description.ilike(search_pattern)
            )
        )

    # 2. Status filter
    if status_filter:
        query = query.filter(Task.status == status_filter)

    # 3. Priority filter
    if priority_filter:
        query = query.filter(Task.priority == priority_filter)

    # Order newest tasks first
    tasks = query.order_by(Task.created_at.desc()).all()

    return [TaskResponse.from_orm_with_overdue(t) for t in tasks]


@router.get(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Get single task by ID",
    description="Retrieves a specific task. Enforces strict ownership checks."
)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ownership Security Check:
    Verifies that the requested task exists AND belongs to the requesting user.
    If the task belongs to another user, returns 403 Forbidden.
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found."
        )

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to view this task."
        )

    return TaskResponse.from_orm_with_overdue(task)


@router.put(
    "/{task_id}",
    response_model=TaskResponse,
    summary="Update a task",
    description="Updates task fields. Rejects unauthorized update attempts on tasks owned by other users."
)
def update_task(
    task_id: int,
    task_in: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ownership Security Check:
    Only the owner (current_user.id == task.user_id) can modify the task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found."
        )

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to modify this task."
        )

    # Apply only provided fields (partial update)
    update_data = task_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(task, field, value)

    db.commit()
    db.refresh(task)

    return TaskResponse.from_orm_with_overdue(task)


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete a task",
    description="Deletes a task. Rejects unauthorized deletion attempts on tasks owned by other users."
)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Ownership Security Check:
    Only the owner (current_user.id == task.user_id) can delete the task.
    """
    task = db.query(Task).filter(Task.id == task_id).first()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Task with ID {task_id} not found."
        )

    if task.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to delete this task."
        )

    db.delete(task)
    db.commit()

    return {
        "success": True,
        "message": f"Task #{task_id} '{task.title}' was successfully deleted."
    }
