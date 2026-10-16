from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, field_validator, ConfigDict
from app.models.task import TaskPriority, TaskStatus


class TaskBase(BaseModel):
    """
    Base attributes shared by task models.
    """
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Title of the task",
        examples=["Complete Project Report"]
    )
    description: Optional[str] = Field(
        None,
        description="Detailed description or notes for the task"
    )
    priority: TaskPriority = Field(
        default=TaskPriority.MEDIUM,
        description="Priority level: low, medium, or high"
    )
    status: TaskStatus = Field(
        default=TaskStatus.PENDING,
        description="Current workflow status: pending, in_progress, or completed"
    )
    due_date: Optional[datetime] = Field(
        None,
        description="Optional due date in ISO 8601 format (e.g. 2026-10-31T18:00:00Z)"
    )

    @field_validator("title")
    @classmethod
    def validate_title(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Task title cannot be empty or blank spaces.")
        return trimmed


class TaskCreate(TaskBase):
    """
    Payload for creating a new task.
    """
    pass


class TaskUpdate(BaseModel):
    """
    Payload for updating an existing task. All fields are optional.
    """
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    due_date: Optional[datetime] = None

    @field_validator("title")
    @classmethod
    def validate_title_optional(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            trimmed = v.strip()
            if not trimmed:
                raise ValueError("Task title cannot be empty or blank spaces.")
            return trimmed
        return v


class TaskResponse(BaseModel):
    """
    Safe output representation of a task returned by the API.
    """
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    priority: TaskPriority
    status: TaskStatus
    due_date: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    is_overdue: bool = False

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def from_orm_with_overdue(cls, task) -> "TaskResponse":
        """
        Calculates whether a task is overdue relative to the current UTC time.
        A task is overdue if it has a due_date in the past and is NOT completed.
        """
        now = datetime.now(timezone.utc)
        is_od = False
        if task.due_date and task.status != TaskStatus.COMPLETED:
            # Handle naive vs aware datetimes safely
            task_due = task.due_date
            if task_due.tzinfo is None:
                task_due = task_due.replace(tzinfo=timezone.utc)
            is_od = task_due < now

        return cls(
            id=task.id,
            user_id=task.user_id,
            title=task.title,
            description=task.description,
            priority=task.priority,
            status=task.status,
            due_date=task.due_date,
            created_at=task.created_at,
            updated_at=task.updated_at,
            is_overdue=is_od
        )


class TaskMetricsResponse(BaseModel):
    """
    Dashboard metrics summary schema.
    """
    total: int
    pending: int
    in_progress: int
    completed: int
    overdue: int
