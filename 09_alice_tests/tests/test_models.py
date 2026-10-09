"""
test_models.py
Basic unit tests for TaskFlow's models.
"""

import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from models import Project, Status, Task, User


def make_user():
    return User(user_id=1, username="testuser", email="test@example.com")


def test_task_marks_done():
    user = make_user()
    task = Task(task_id=1, title="Test task", owner=user)
    assert task.status == Status.TODO
    task.mark_done()
    assert task.status == Status.DONE


def test_task_overdue_detection():
    user = make_user()
    past_due = Task(
        task_id=2,
        title="Overdue task",
        owner=user,
        due_date=datetime.utcnow() - timedelta(days=1),
    )
    assert past_due.is_overdue() is True

    future_due = Task(
        task_id=3,
        title="Future task",
        owner=user,
        due_date=datetime.utcnow() + timedelta(days=1),
    )
    assert future_due.is_overdue() is False


def test_project_completion_rate():
    user = make_user()
    project = Project(project_id=1, name="Test Project")
    assert project.completion_rate() == 0.0

    t1 = Task(task_id=4, title="A", owner=user, status=Status.DONE)
    t2 = Task(task_id=5, title="B", owner=user, status=Status.TODO)
    project.add_task(t1)
    project.add_task(t2)

    assert project.completion_rate() == 0.5


if __name__ == "__main__":
    test_task_marks_done()
    test_task_overdue_detection()
    test_project_completion_rate()
    print("All tests passed.")
