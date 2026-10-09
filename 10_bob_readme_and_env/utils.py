"""
utils.py
Miscellaneous helper functions used across TaskFlow.
"""

from datetime import datetime, timedelta
from typing import Iterable

from models import Priority, Status, Task


def format_task_summary(task: Task) -> str:
    due = task.due_date.strftime("%Y-%m-%d") if task.due_date else "no due date"
    return f"#{task.task_id} {task.title} — {task.status.value} ({due})"


def sort_by_priority(tasks: Iterable[Task]) -> list:
    return sorted(tasks, key=lambda t: t.priority.value, reverse=True)


def filter_by_status(tasks: Iterable[Task], status: Status) -> list:
    return [t for t in tasks if t.status == status]


def upcoming_deadlines(tasks: Iterable[Task], within_days: int = 7) -> list:
    cutoff = datetime.utcnow() + timedelta(days=within_days)
    return [
        t for t in tasks
        if t.due_date and t.due_date <= cutoff and t.status != Status.DONE
    ]


def priority_from_string(value: str) -> Priority:
    mapping = {
        "low": Priority.LOW,
        "medium": Priority.MEDIUM,
        "high": Priority.HIGH,
        "urgent": Priority.URGENT,
    }
    try:
        return mapping[value.lower()]
    except KeyError:
        raise ValueError(f"Unknown priority string: {value!r}")
