"""
main.py
Entry point that wires together the TaskFlow demo app.
"""

from datetime import datetime, timedelta

from database import InMemoryDatabase
from models import Priority, Status
from utils import format_task_summary, sort_by_priority, upcoming_deadlines


def seed_data(db: InMemoryDatabase):
    alice = db.create_user("alice", "alice@example.com")
    bob = db.create_user("bob", "bob@example.com")

    project = db.create_project("Website Relaunch")

    db.create_task(
        "Design new homepage",
        owner=alice,
        project=project,
        priority=Priority.HIGH,
        due_date=datetime.utcnow() + timedelta(days=2),
    )
    db.create_task(
        "Set up CI pipeline",
        owner=bob,
        project=project,
        priority=Priority.MEDIUM,
        due_date=datetime.utcnow() + timedelta(days=10),
    )
    db.create_task(
        "Write launch announcement",
        owner=alice,
        project=project,
        priority=Priority.LOW,
        status=Status.IN_PROGRESS,
    )

    return alice, bob, project


def main():
    db = InMemoryDatabase()
    alice, bob, project = seed_data(db)

    print(f"Project: {project.name}")
    print(f"Completion rate: {project.completion_rate():.0%}\n")

    print("All tasks by priority:")
    for task in sort_by_priority(project.tasks):
        print(" -", format_task_summary(task))

    print("\nUpcoming deadlines (next 7 days):")
    for task in upcoming_deadlines(project.tasks):
        print(" -", format_task_summary(task))

    print(f"\nTasks owned by {alice.username}:")
    for task in db.list_tasks_for_user(alice.user_id):
        print(" -", format_task_summary(task))


if __name__ == "__main__":
    main()
