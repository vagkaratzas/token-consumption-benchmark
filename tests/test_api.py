from taskflow.api.app import create_app


def test_create_user_route():
    app = create_app()
    resp = app.dispatch(
        "POST", "/users", {"email": "x@y.com", "name": "X", "password": "pw123456"}
    )
    assert resp["status"] == 201
    assert resp["user"]["email"] == "x@y.com"


def test_unknown_route_returns_404():
    app = create_app()
    assert app.dispatch("GET", "/nope")["status"] == 404


def test_task_flow_end_to_end():
    app = create_app()
    proj = app.dispatch("POST", "/projects", {"name": "P", "owner_id": 1})
    assert proj["status"] == 201
    pid = proj["project"]["id"]
    created = app.dispatch(
        "POST", "/tasks", {"title": "T", "project_id": pid, "assignee_id": 1}
    )
    assert created["status"] == 201
    done = app.dispatch(
        "POST", "/tasks/complete", {"task_id": created["task"]["id"]}
    )
    assert done["status"] == 200
    assert done["task"]["status"] == "done"
