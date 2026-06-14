from taskflow.db import Database
from taskflow.models.task import Status, Task
from taskflow.models.user import User
from taskflow.repositories.task_repo import TaskRepository
from taskflow.repositories.user_repo import UserRepository


def test_add_and_get_user():
    repo = UserRepository(Database())
    user = repo.add(User(email="a@b.com", name="A"))
    assert user.id is not None
    assert repo.get(user.id).email == "a@b.com"


def test_get_by_email():
    repo = UserRepository(Database())
    repo.add(User(email="found@b.com", name="A"))
    assert repo.get_by_email("found@b.com") is not None
    assert repo.get_by_email("missing@b.com") is None


def test_list_by_project():
    repo = TaskRepository(Database())
    repo.add(Task(title="t1", project_id=1))
    repo.add(Task(title="t2", project_id=2))
    assert len(repo.list_by_project(1)) == 1


def test_update_status():
    repo = TaskRepository(Database())
    task = repo.add(Task(title="t"))
    repo.update(task.id, {"status": Status.DONE})
    assert repo.get(task.id).status == Status.DONE
