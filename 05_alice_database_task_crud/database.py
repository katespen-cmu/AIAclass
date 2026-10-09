"""
database.py
A fake, in-memory "database" layer for TaskFlow.
Simulates the kind of interface a real DB client would expose.
"""

from typing import Dict, List, Optional

from models import Project, Task, User


class DatabaseError(Exception):
    """Raised when a database operation fails."""


class InMemoryDatabase:
    """A toy stand-in for a real database connection."""

    def __init__(self):
        self._users: Dict[int, User] = {}
        self._tasks: Dict[int, Task] = {}
        self._projects: Dict[int, Project] = {}
        self._next_user_id = 1
        self._next_task_id = 1
        self._next_project_id = 1

    # --- Users -----------------------------------------------------
    def create_user(self, username: str, email: str) -> User:
        user = User(user_id=self._next_user_id, username=username, email=email)
        self._users[user.user_id] = user
        self._next_user_id += 1
        return user

    def get_user(self, user_id: int) -> Optional[User]:
        return self._users.get(user_id)

    # --- Projects ----------------------------------------------------
    def create_project(self, name: str) -> Project:
        project = Project(project_id=self._next_project_id, name=name)
        self._projects[project.project_id] = project
        self._next_project_id += 1
        return project

    def get_project(self, project_id: int) -> Optional[Project]:
        return self._projects.get(project_id)

    # --- Tasks -------------------------------------------------------
    def create_task(self, title: str, owner: User, project: Project, **kwargs) -> Task:
        if owner.user_id not in self._users:
            raise DatabaseError(f"Unknown user_id: {owner.user_id}")

        task = Task(task_id=self._next_task_id, title=title, owner=owner, **kwargs)
        self._tasks[task.task_id] = task
        project.add_task(task)
        self._next_task_id += 1
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        return self._tasks.get(task_id)

    def list_tasks_for_user(self, user_id: int) -> List[Task]:
        return [t for t in self._tasks.values() if t.owner.user_id == user_id]

    def delete_task(self, task_id: int) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False
