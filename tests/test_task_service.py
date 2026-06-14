from taskflow.api.deps import build_services
from taskflow.models.task import Status


def test_create_task_notifies_assignee():
    services = build_services()
    task = services.tasks.create_task("Write report", project_id=1, assignee_id=7)
    assert task.id is not None
    assert any("Assigned task" in m for m in services.notifications.sent)


def test_complete_task_sets_done():
    services = build_services()
    task = services.tasks.create_task("Ship", project_id=1, assignee_id=2)
    done = services.tasks.complete_task(task.id)
    assert done.status == Status.DONE


def test_open_tasks_excludes_done():
    services = build_services()
    services.tasks.create_task("a", project_id=1)
    second = services.tasks.create_task("b", project_id=1)
    services.tasks.complete_task(second.id)
    open_titles = [t.title for t in services.tasks.open_tasks(1)]
    assert open_titles == ["a"]
