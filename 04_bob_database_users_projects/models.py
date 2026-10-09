"""
models.py
Data models for the TaskFlow application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional


class Status(Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"
    ARCHIVED = "archived"


class Priority(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    URGENT = 4


@dataclass
class User:
    user_id: int
    username: str
    email: str
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __str__(self) -> str:
        return f"User({self.username})"


@dataclass
class Task:
    task_id: int
    title: str
    owner: User
    description: str = ""
    status: Status = Status.TODO
    priority: Priority = Priority.MEDIUM
    due_date: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def mark_done(self) -> None:
        self.status = Status.DONE

    def is_overdue(self) -> bool:
        if self.due_date is None:
            return False
        return datetime.utcnow() > self.due_date and self.status != Status.DONE

    def __str__(self) -> str:
        return f"[{self.status.value.upper()}] {self.title} (owner: {self.owner.username})"


@dataclass
class Project:
    project_id: int
    name: str
    tasks: list = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def completion_rate(self) -> float:
        if not self.tasks:
            return 0.0
        done = sum(1 for t in self.tasks if t.status == Status.DONE)
        return done / len(self.tasks)
