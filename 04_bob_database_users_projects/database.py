"""
database.py
A fake, in-memory "database" layer for TaskFlow.
Simulates the kind of interface a real DB client would expose.
"""

from typing import Dict, Optional

from models import Project, User


class DatabaseError(Exception):
    """Raised when a database operation fails."""


class InMemoryDatabase:
    """A toy stand-in for a real database connection."""

    def __init__(self):
        self._users: Dict[int, User] = {}
        self._projects: Dict[int, Project] = {}
        self._next_user_id = 1
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
