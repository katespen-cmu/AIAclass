"""
models.py
Data models for the TaskFlow application.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


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
