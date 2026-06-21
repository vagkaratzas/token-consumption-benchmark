"""The benchmark task suite.

Eight tasks across three categories, each modelling a realistic thing an agent
is asked to do against the ``taskflow`` codebase:

* A. comprehension / navigation  (input/code-retrieval heavy -> serena, graphify, codegraph)
* B. command / diagnostic        (command-output heavy        -> rtk)
* C. explanation                 (prose-output heavy          -> caveman)
* D. code generation             (code-output heavy           -> ponytail)

Each task declares, for every scenario, exactly what artifact is produced:

* ``baseline_files``    : repo-relative files a no-tool agent reads in full
* ``baseline_commands`` : raw shell commands a no-tool agent runs
* ``rtk_read_files``    : files read through ``rtk read``
* ``rtk_commands``      : the rtk-proxied equivalents of ``baseline_commands``
* ``serena_calls``      : MCP tool calls (None -> serena gives no benefit; falls back to baseline)
* ``graphify_argv``     : graphify CLI invocations (None -> falls back to baseline)
* ``codegraph_argv``    : codegraph CLI invocations (None -> falls back to baseline)
* ``reference_answer``  : the single canonical answer / artifact (the shared "output" component)
* ``codegen``           : True for code-generation tasks, where the output is generated
                         code that ponytail minimises (and caveman leaves ~unchanged)

serena paths are relative to the ``taskflow`` project root (e.g.
``services/task_service.py``); baseline/rtk file paths are repo-relative
(``taskflow/services/task_service.py``).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Task:
    id: str
    category: str
    title: str
    goal: str
    reference_answer: str
    baseline_files: List[str] = field(default_factory=list)
    baseline_commands: List[str] = field(default_factory=list)
    rtk_read_files: List[str] = field(default_factory=list)
    rtk_commands: List[str] = field(default_factory=list)
    serena_calls: Optional[List[dict]] = None
    graphify_argv: Optional[List[List[str]]] = None
    codegraph_argv: Optional[List[List[str]]] = None
    codegen: bool = False


TASKS: List[Task] = [
    # ---------------------------------------------------------------- A1
    Task(
        id="A1",
        category="A",
        title="Locate a class and list its methods",
        goal="Find the TaskService class and enumerate its public methods.",
        baseline_files=["taskflow/services/task_service.py"],
        rtk_read_files=["taskflow/services/task_service.py"],
        serena_calls=[
            {"tool": "get_symbols_overview",
             "args": {"relative_path": "services/task_service.py", "depth": 1}},
        ],
        graphify_argv=[["explain", "TaskService"]],
        codegraph_argv=[["node", "TaskService"]],
        reference_answer=(
            "TaskService is defined in taskflow/services/task_service.py. It creates and "
            "transitions tasks and notifies assignees of changes. Its methods are:\n"
            "- __init__(self, tasks: TaskRepository, notifications: NotificationService)\n"
            "- create_task(self, title, project_id, assignee_id=None) -> Task\n"
            "- assign_task(self, task_id, assignee_id) -> Optional[Task]\n"
            "- complete_task(self, task_id) -> Optional[Task]\n"
            "- open_tasks(self, project_id) -> List[Task]"
        ),
    ),
    # ---------------------------------------------------------------- A2
    Task(
        id="A2",
        category="A",
        title="Find all callers of a symbol",
        goal="Find every place that calls NotificationService.notify.",
        baseline_files=["taskflow/services/task_service.py"],
        baseline_commands=["grep -rn --include='*.py' \"\\.notify(\" taskflow"],
        rtk_read_files=["taskflow/services/task_service.py"],
        rtk_commands=['rtk grep "\\.notify\\(" taskflow -t py'],
        serena_calls=[
            {"tool": "find_referencing_symbols",
             "args": {"name_path": "notify",
                      "relative_path": "services/notification_service.py"}},
        ],
        graphify_argv=[["query", "Where is notify called and what calls it?",
                        "--budget", "800"]],
        codegraph_argv=[["callers", "notify"]],
        reference_answer=(
            "NotificationService.notify (taskflow/services/notification_service.py) is "
            "called only from TaskService (taskflow/services/task_service.py), in three "
            "methods:\n"
            "- create_task: notifies the assignee of a newly created task\n"
            "- assign_task: notifies the assignee on (re)assignment\n"
            "- complete_task: notifies the assignee when a task is completed\n"
            "No other module calls notify directly."
        ),
    ),
    # ---------------------------------------------------------------- A3
    Task(
        id="A3",
        category="A",
        title="Trace a call path API -> DB",
        goal="Trace how creating a task via the API reaches the database write.",
        baseline_files=[
            "taskflow/api/routes_tasks.py",
            "taskflow/services/task_service.py",
            "taskflow/repositories/task_repo.py",
            "taskflow/repositories/base_repo.py",
            "taskflow/db.py",
        ],
        rtk_read_files=[
            "taskflow/api/routes_tasks.py",
            "taskflow/services/task_service.py",
            "taskflow/repositories/task_repo.py",
            "taskflow/repositories/base_repo.py",
            "taskflow/db.py",
        ],
        serena_calls=[
            {"tool": "get_symbols_overview",
             "args": {"relative_path": "api/routes_tasks.py"}},
            {"tool": "find_symbol",
             "args": {"name_path_pattern": "TaskService/create_task",
                      "relative_path": "services/task_service.py", "include_body": True}},
            {"tool": "find_symbol",
             "args": {"name_path_pattern": "BaseRepository/add",
                      "relative_path": "repositories/base_repo.py", "include_body": True}},
            {"tool": "find_symbol",
             "args": {"name_path_pattern": "Database/insert",
                      "relative_path": "db.py", "include_body": True}},
        ],
        graphify_argv=[["path", "create_task", "Database"]],
        codegraph_argv=[["node", "create_task"]],
        reference_answer=(
            "Creating a task flows through four layers:\n"
            "1. API: POST /tasks -> create_task handler in taskflow/api/routes_tasks.py "
            "calls app.services.tasks.create_task(...).\n"
            "2. Service: TaskService.create_task (taskflow/services/task_service.py) builds "
            "a Task and calls self.tasks.add(task), then notifies the assignee.\n"
            "3. Repository: BaseRepository.add (taskflow/repositories/base_repo.py) turns "
            "the entity into a row and calls self.db.insert(self.table, row).\n"
            "4. DB: Database.insert (taskflow/db.py) assigns an id and stores the row. "
            "The new id is returned back up the chain."
        ),
    ),
    # ---------------------------------------------------------------- B1
    Task(
        id="B1",
        category="B",
        title="Run the test suite and summarize",
        goal="Run the pytest suite and report pass/fail.",
        baseline_commands=[".venv/bin/python -m pytest"],
        rtk_commands=["rtk test .venv/bin/python -m pytest"],
        reference_answer=(
            "All 13 tests pass. Breakdown: tests/test_api.py (3), "
            "tests/test_auth_service.py (3), tests/test_repositories.py (4), "
            "tests/test_task_service.py (3). No failures or errors."
        ),
    ),
    # ---------------------------------------------------------------- B2
    Task(
        id="B2",
        category="B",
        title="List the project structure",
        goal="List all Python source files in the project.",
        baseline_commands=["find taskflow tests -type f -name '*.py'"],
        rtk_commands=["rtk find taskflow tests -type f -name '*.py'"],
        reference_answer=(
            "The project is a layered Python package. taskflow/ contains: top-level "
            "config.py, db.py, cli.py; models/ (base, user, task, project); "
            "repositories/ (base_repo, user_repo, task_repo, project_repo); services/ "
            "(auth, task, project, notification); api/ (app, deps, routes_users, "
            "routes_tasks, routes_projects); utils/ (validation, dates, logging). "
            "tests/ holds four test modules covering repositories, auth, tasks, and the API."
        ),
    ),
    # ---------------------------------------------------------------- B3
    Task(
        id="B3",
        category="B",
        title="Grep for deprecated API and TODOs",
        goal="Find the deprecated old_token_hash function and all TODO/FIXME comments.",
        baseline_commands=["grep -rn --include='*.py' \"old_token_hash\\|TODO\\|FIXME\" taskflow"],
        rtk_commands=['rtk grep "old_token_hash|TODO|FIXME" taskflow -t py'],
        reference_answer=(
            "Deprecated API: AuthService.old_token_hash in "
            "taskflow/services/auth_service.py (legacy unsalted SHA-1; scheduled for "
            "removal). TODO/FIXME comments: taskflow/services/task_service.py has a TODO "
            "(validate project_id exists in create_task) and a FIXME (reject completing an "
            "already-done task in complete_task)."
        ),
    ),
    # ---------------------------------------------------------------- C1
    Task(
        id="C1",
        category="C",
        title="Explain the architecture",
        goal="Explain the overall architecture and how the modules interact.",
        baseline_files=[
            "taskflow/__init__.py",
            "taskflow/config.py",
            "taskflow/db.py",
            "taskflow/api/deps.py",
            "taskflow/api/app.py",
            "taskflow/services/task_service.py",
            "taskflow/services/auth_service.py",
            "taskflow/repositories/base_repo.py",
            "taskflow/models/base.py",
            "taskflow/cli.py",
        ],
        rtk_read_files=[
            "taskflow/__init__.py",
            "taskflow/config.py",
            "taskflow/db.py",
            "taskflow/api/deps.py",
            "taskflow/api/app.py",
            "taskflow/services/task_service.py",
            "taskflow/services/auth_service.py",
            "taskflow/repositories/base_repo.py",
            "taskflow/models/base.py",
            "taskflow/cli.py",
        ],
        serena_calls=[
            {"tool": "list_dir", "args": {"relative_path": ".", "recursive": True}},
            {"tool": "get_symbols_overview", "args": {"relative_path": "db.py"}},
            {"tool": "get_symbols_overview", "args": {"relative_path": "api/deps.py"}},
            {"tool": "get_symbols_overview", "args": {"relative_path": "api/app.py"}},
            {"tool": "get_symbols_overview", "args": {"relative_path": "services/task_service.py"}},
            {"tool": "get_symbols_overview", "args": {"relative_path": "services/auth_service.py"}},
            {"tool": "get_symbols_overview", "args": {"relative_path": "repositories/base_repo.py"}},
            {"tool": "get_symbols_overview", "args": {"relative_path": "models/base.py"}},
            {"tool": "get_symbols_overview", "args": {"relative_path": "cli.py"}},
        ],
        graphify_argv=[["query",
                        "What is the overall architecture and how do the api, services, "
                        "repositories, db and models layers interact?",
                        "--budget", "1200"]],
        codegraph_argv=[["explore",
                         "overall architecture how api services repositories db models "
                         "layers interact", "--max-files", "3"]],
        reference_answer=(
            "taskflow is a small task-management application with a strict layered "
            "architecture: api/cli -> services -> repositories -> db.\n\n"
            "- Models (taskflow/models): dataclasses (User, Task, Project) all subclassing "
            "BaseModel, which provides id/created_at/updated_at plus to_dict() and touch().\n"
            "- DB (taskflow/db.py): a framework-free in-memory Database with insert/get/"
            "list/update/delete over per-table dicts. It is the single persistence leaf.\n"
            "- Repositories (taskflow/repositories): BaseRepository is a generic CRUD layer "
            "mapping models to rows in one table; UserRepository/TaskRepository/"
            "ProjectRepository add domain queries (e.g. get_by_email, list_by_project).\n"
            "- Services (taskflow/services): business logic. AuthService hashes passwords "
            "and authenticates; TaskService creates/assigns/completes tasks and calls "
            "NotificationService; ProjectService manages membership.\n"
            "- API (taskflow/api): deps.build_services wires one Database into repositories "
            "and services (a Services container); app.App is a tiny (method, path) -> "
            "handler dispatcher; routes_* register handlers that call services.\n"
            "- CLI (taskflow/cli.py): argparse front-end that shares the same services.\n\n"
            "Dependency wiring is centralized in build_services, so api and cli share one "
            "object graph. Each request flows down the layers and back up with results."
        ),
    ),
    # ---------------------------------------------------------------- C2
    Task(
        id="C2",
        category="C",
        title="Describe adding a feature end-to-end",
        goal="Describe how to add a due-date field to tasks across all layers.",
        baseline_files=[
            "taskflow/models/task.py",
            "taskflow/repositories/task_repo.py",
            "taskflow/services/task_service.py",
            "taskflow/api/routes_tasks.py",
            "tests/test_task_service.py",
        ],
        rtk_read_files=[
            "taskflow/models/task.py",
            "taskflow/repositories/task_repo.py",
            "taskflow/services/task_service.py",
            "taskflow/api/routes_tasks.py",
            "tests/test_task_service.py",
        ],
        serena_calls=[
            {"tool": "get_symbols_overview", "args": {"relative_path": "models/task.py"}},
            {"tool": "get_symbols_overview", "args": {"relative_path": "services/task_service.py"}},
            {"tool": "get_symbols_overview", "args": {"relative_path": "api/routes_tasks.py"}},
            {"tool": "find_symbol",
             "args": {"name_path_pattern": "TaskService/create_task",
                      "relative_path": "services/task_service.py", "include_body": True}},
        ],
        graphify_argv=[["query",
                        "Where are task fields defined and how does creating a task flow "
                        "through models, services and the api?",
                        "--budget", "1000"]],
        codegraph_argv=[["impact", "create_task"]],
        reference_answer=(
            "To add a due_date to tasks end-to-end:\n"
            "1. Model: add `due_date: Optional[str] = None` to the Task dataclass in "
            "taskflow/models/task.py. Because BaseModel.to_dict uses asdict, it is "
            "serialized automatically.\n"
            "2. Service: extend TaskService.create_task in taskflow/services/task_service.py "
            "to accept due_date and pass it to Task(...). Optionally add a helper to query "
            "overdue tasks via TaskRepository.\n"
            "3. Repository: no change needed for storage (BaseRepository.add serializes all "
            "fields), but you may add list_overdue(now) to taskflow/repositories/task_repo.py.\n"
            "4. API: read due_date from the body in the create_task handler in "
            "taskflow/api/routes_tasks.py and forward it to the service.\n"
            "5. Tests: add a case to tests/test_task_service.py asserting the due_date round-"
            "trips through create_task and is present in the task dict.\n"
            "No DB schema change is required because Database stores arbitrary row dicts."
        ),
    ),
    # ---------------------------------------------------------------- D1
    Task(
        id="D1",
        category="D",
        title="Implement a due-date field across all layers",
        goal="Write the code that adds a due_date field to tasks end-to-end.",
        codegen=True,
        # Same context retrieval as C2 — the agent must see the same layers to
        # implement the feature it described in C2.
        baseline_files=[
            "taskflow/models/task.py",
            "taskflow/repositories/task_repo.py",
            "taskflow/services/task_service.py",
            "taskflow/api/routes_tasks.py",
            "tests/test_task_service.py",
        ],
        rtk_read_files=[
            "taskflow/models/task.py",
            "taskflow/repositories/task_repo.py",
            "taskflow/services/task_service.py",
            "taskflow/api/routes_tasks.py",
            "tests/test_task_service.py",
        ],
        serena_calls=[
            {"tool": "get_symbols_overview", "args": {"relative_path": "models/task.py"}},
            {"tool": "get_symbols_overview", "args": {"relative_path": "services/task_service.py"}},
            {"tool": "get_symbols_overview", "args": {"relative_path": "api/routes_tasks.py"}},
            {"tool": "find_symbol",
             "args": {"name_path_pattern": "TaskService/create_task",
                      "relative_path": "services/task_service.py", "include_body": True}},
        ],
        graphify_argv=[["query",
                        "Where are task fields defined and how does creating a task flow "
                        "through models, services and the api?",
                        "--budget", "1000"]],
        codegraph_argv=[["impact", "create_task"]],
        # The "output" component for a codegen task is generated code. This is a
        # representative *verbose* implementation — the kind a default agent emits:
        # an unrequested is_overdue property, an overdue-query helper threaded
        # through service + repo, defensive ISO parsing, and a multi-step test.
        # caveman leaves code blocks ~unchanged; ponytail (lazy-senior-dev) trims
        # the unrequested abstractions to the minimum that satisfies the feature.
        reference_answer=(
            "Add a `due_date` field to tasks across every layer.\n\n"
            "```python\n"
            "# taskflow/models/task.py\n"
            "from datetime import datetime, timezone\n"
            "from typing import Optional\n\n"
            "@dataclass\n"
            "class Task(BaseModel):\n"
            "    title: str = \"\"\n"
            "    description: str = \"\"\n"
            "    status: Status = Status.TODO\n"
            "    project_id: Optional[int] = None\n"
            "    assignee_id: Optional[int] = None\n"
            "    due_date: Optional[str] = None  # ISO-8601 date string\n\n"
            "    @property\n"
            "    def is_overdue(self) -> bool:\n"
            "        if self.due_date is None:\n"
            "            return False\n"
            "        try:\n"
            "            due = datetime.fromisoformat(self.due_date)\n"
            "        except ValueError:\n"
            "            return False\n"
            "        return due < datetime.now(timezone.utc) and not self.is_done()\n"
            "```\n\n"
            "```python\n"
            "# taskflow/services/task_service.py\n"
            "    def create_task(\n"
            "        self, title: str, project_id: int, assignee_id: Optional[int] = None,\n"
            "        due_date: Optional[str] = None,\n"
            "    ) -> Task:\n"
            "        if due_date is not None:\n"
            "            try:\n"
            "                datetime.fromisoformat(due_date)\n"
            "            except ValueError:\n"
            "                raise ValidationError(f\"invalid due_date: {due_date!r}\")\n"
            "        task = Task(title=title, project_id=project_id,\n"
            "                    assignee_id=assignee_id, due_date=due_date)\n"
            "        task = self.tasks.add(task)\n"
            "        if assignee_id is not None:\n"
            "            self.notifications.notify(assignee_id, f\"Assigned task {task.id}\")\n"
            "        return task\n\n"
            "    def overdue_tasks(self, project_id: int) -> List[Task]:\n"
            "        return self.tasks.list_overdue(project_id)\n"
            "```\n\n"
            "```python\n"
            "# taskflow/repositories/task_repo.py\n"
            "    def list_overdue(self, project_id: int) -> List[Task]:\n"
            "        return [t for t in self.list_by_project(project_id) if t.is_overdue]\n"
            "```\n\n"
            "```python\n"
            "# taskflow/api/routes_tasks.py\n"
            "    def create_task(app: App, body: dict) -> dict:\n"
            "        due_date = body.get(\"due_date\")\n"
            "        if due_date is not None and not isinstance(due_date, str):\n"
            "            return {\"status\": 400, \"error\": \"due_date must be a string\"}\n"
            "        task = app.services.tasks.create_task(\n"
            "            title=body.get(\"title\", \"\"),\n"
            "            project_id=body.get(\"project_id\"),\n"
            "            assignee_id=body.get(\"assignee_id\"),\n"
            "            due_date=due_date,\n"
            "        )\n"
            "        return {\"status\": 201, \"task\": task.to_dict()}\n"
            "```\n\n"
            "```python\n"
            "# tests/test_task_service.py\n"
            "def test_create_task_with_due_date():\n"
            "    services = build_services()\n"
            "    task = services.tasks.create_task(\n"
            "        \"Write report\", project_id=1, assignee_id=7,\n"
            "        due_date=\"2099-01-01T00:00:00+00:00\",\n"
            "    )\n"
            "    assert task.due_date == \"2099-01-01T00:00:00+00:00\"\n"
            "    assert task.to_dict()[\"due_date\"] == \"2099-01-01T00:00:00+00:00\"\n"
            "    assert task.is_overdue is False\n"
            "```\n"
        ),
    ),
]


def task_by_id(task_id: str) -> Task:
    for t in TASKS:
        if t.id == task_id:
            return t
    raise KeyError(task_id)
