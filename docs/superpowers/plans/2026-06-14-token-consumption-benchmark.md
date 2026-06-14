# Token-Consumption Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible benchmark that measures how much serena, graphify, rtk, and caveman reduce an AI agent's token consumption versus a no-tool baseline, and produce a shareable Markdown report.

**Architecture:** A generated Python dummy codebase (`taskflow`) is probed by an ~8-task suite. For each task×scenario, a Python harness measures the real artifact each tool produces, splits cost into input+output tokens (tiktoken o200k_base), and writes results that a report generator renders into `REPORT.md`.

**Tech Stack:** Python 3, tiktoken, uv (graphify/serena), cargo/curl (rtk), npm/curl (caveman), pytest.

**Execution note:** Phase 0 is exploratory — installs may fail. Record exactly what installs and what doesn't; fall back to documented-spec modeling for any failure and flag it in the report. Do not silently fake tool output.

---

## Phase 0: Environment & tool installation

### Task 0.1: Record environment + install base deps
**Files:** Create `results/environment.md`
- [ ] Capture versions: `python3 --version`, `uv --version`, `cargo --version`, `node --version`, `git --version`.
- [ ] Install harness deps into a venv: `uv venv .venv && .venv/bin/python -m pip install tiktoken pytest` (or `uv pip install`).
- [ ] Verify tiktoken loads: `.venv/bin/python -c "import tiktoken; print(tiktoken.get_encoding('o200k_base').encode('hello world'))"` → expect a list of ints.
- [ ] Write captured versions to `results/environment.md`.

### Task 0.2: Install the four tools (best-effort, record outcomes)
**Files:** Append to `results/environment.md` an "Install outcomes" table.
- [ ] graphify: `uv tool install graphifyy`; verify `graphify --help`. Record PASS/FAIL + version.
- [ ] serena: `uv tool install serena-agent` (or `--python 3.13`); verify `serena --help` / importable. Record PASS/FAIL.
- [ ] rtk: try `cargo install rtk` then fallback `curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh`; verify `rtk --version`. Record PASS/FAIL.
- [ ] caveman: `curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash`; locate the installed compression ruleset/skill files. Record PASS/FAIL + path to ruleset.
- [ ] For each FAIL, note the error and that the report will model it from spec.

---

## Phase 1: Build the `taskflow` dummy codebase

### Task 1.1: Package skeleton + config/db
**Files:** Create `taskflow/__init__.py`, `taskflow/config.py`, `taskflow/db.py`
- [ ] `config.py`: `Settings` dataclass (db_path, secret_key, page_size) + `load_settings()`.
- [ ] `db.py`: tiny in-memory `Database` class with `tables: dict[str, dict]`, `insert/get/list/update/delete`, used by repositories. This is the call-chain leaf (api→service→repo→**db**).
- [ ] Verify import: `.venv/bin/python -c "import taskflow.db"` → no error.

### Task 1.2: Models with inheritance
**Files:** Create `taskflow/models/__init__.py`, `base.py`, `user.py`, `task.py`, `project.py`
- [ ] `base.py`: `BaseModel` (id, created_at, `to_dict()`, `touch()`). All others subclass it (symbol hierarchy for serena/graphify).
- [ ] `user.py`: `User(BaseModel)` (email, name, password_hash, role).
- [ ] `task.py`: `Task(BaseModel)` (title, status, assignee_id, project_id) + `Status` enum.
- [ ] `project.py`: `Project(BaseModel)` (name, owner_id, member_ids).
- [ ] Verify import of each.

### Task 1.3: Repositories with inheritance
**Files:** Create `taskflow/repositories/__init__.py`, `base_repo.py`, `user_repo.py`, `task_repo.py`, `project_repo.py`
- [ ] `base_repo.py`: `BaseRepository` generic CRUD over `Database` (`add/get/list/update/remove`).
- [ ] `user_repo.py`: `UserRepository(BaseRepository)` + `get_by_email()`.
- [ ] `task_repo.py`: `TaskRepository(BaseRepository)` + `list_by_project()`, `list_by_assignee()`.
- [ ] `project_repo.py`: `ProjectRepository(BaseRepository)` + `list_by_owner()`.
- [ ] Verify imports.

### Task 1.4: Services (business logic + deprecated fn + TODOs)
**Files:** Create `taskflow/services/__init__.py`, `auth_service.py`, `task_service.py`, `project_service.py`, `notification_service.py`
- [ ] `auth_service.py`: `AuthService` with `hash_password()` (current) and a **deprecated** `old_token_hash()` (grep target B3) marked with a docstring deprecation note; `register()`, `authenticate()`.
- [ ] `task_service.py`: `TaskService.create_task()`, `assign_task()`, `complete_task()` — calls `TaskRepository` and `NotificationService` (cross-module refs for A2/A3). Add 2–3 `# TODO:` / `# FIXME:` comments (grep targets B3).
- [ ] `project_service.py`: `ProjectService.create_project()`, `add_member()`.
- [ ] `notification_service.py`: `NotificationService.notify()` (referenced by task_service).
- [ ] Verify imports.

### Task 1.5: API layer + CLI (call-chain roots)
**Files:** Create `taskflow/api/__init__.py`, `app.py`, `deps.py`, `routes_users.py`, `routes_tasks.py`, `routes_projects.py`, `taskflow/cli.py`
- [ ] `deps.py`: wires `Database` → repositories → services (dependency container).
- [ ] `app.py`: minimal framework-free `App` with a `route()` registry + `dispatch(method, path, body)`.
- [ ] `routes_tasks.py`: handlers calling `TaskService` (root of api→service→repo→db chain for A3).
- [ ] `routes_users.py`, `routes_projects.py`: analogous handlers.
- [ ] `cli.py`: `main(argv)` dispatching subcommands to services (second call-chain root).
- [ ] Verify: `.venv/bin/python -m taskflow.cli --help`-style smoke (or `python -c` import).

### Task 1.6: utils + tests (runnable pytest suite for rtk)
**Files:** Create `taskflow/utils/__init__.py`, `validation.py`, `dates.py`, `logging.py`; `tests/test_task_service.py`, `test_auth_service.py`, `test_repositories.py`, `test_api.py`
- [ ] utils: `validation.validate_email()`, `dates.format_iso()`, `logging.get_logger()`.
- [ ] Tests covering services/repos/api so `pytest` produces realistic multi-line output (B1). All tests should PASS.
- [ ] Run: `.venv/bin/python -m pytest -q` → expect all green. Record the raw output for the rtk task fixture.

### Task 1.7: Commit codebase
- [ ] `git add taskflow tests && git commit -m "Add taskflow dummy codebase"`.

---

## Phase 2: Benchmark harness

### Task 2.1: Tokenizer wrapper
**Files:** Create `benchmark/__init__.py`, `benchmark/tokenizer.py`; Test `benchmark/test_tokenizer.py`
- [ ] `tokenizer.py`:
```python
import tiktoken
_ENC = tiktoken.get_encoding("o200k_base")
def count_tokens(text: str) -> int:
    return len(_ENC.encode(text or ""))
```
- [ ] Test: `assert count_tokens("") == 0` and `count_tokens("hello world") > 0`.
- [ ] Run: `.venv/bin/python -m pytest benchmark/test_tokenizer.py -q` → PASS.

### Task 2.2: Task definitions
**Files:** Create `benchmark/tasks.py`
- [ ] Define a `Task` dataclass: `id, category (A/B/C), goal, baseline_files (list[path]), baseline_commands (list[str]), reference_answer (str)`.
- [ ] Define `TASKS` = the 8 tasks from spec §5. For each, fill: the exact `taskflow` files a baseline agent would read, the exact shell commands it would run, and a single canonical `reference_answer` (the shared "output" component).
- [ ] Verify: `.venv/bin/python -c "from benchmark.tasks import TASKS; print(len(TASKS))"` → 8.

### Task 2.3: Baseline scenario runner
**Files:** Create `benchmark/scenarios/__init__.py`, `benchmark/scenarios/baseline.py`
- [ ] For a task: `input_tokens` = sum of tokens of each `baseline_files` content + tokens of raw output of each `baseline_commands` (run them for real, capture stdout+stderr). `output_tokens` = tokens(reference_answer).
- [ ] Return dict `{input_tokens, output_tokens, total, detail}`.
- [ ] Verify on task A1 → prints positive numbers.

### Task 2.4: rtk scenario runner
**Files:** Create `benchmark/scenarios/rtk.py`
- [ ] Same as baseline, but each `baseline_command`'s output is passed through the real `rtk` (per its docs: wrap/pipe the command). File reads via `cat` are also routed through rtk where rtk supports it. `output_tokens` unchanged from baseline.
- [ ] If rtk not installed: mark `modeled=True`, apply rtk's documented compression behavior to command output and flag it.
- [ ] Verify on task B1 (pytest) → rtk input_tokens ≤ baseline input_tokens.

### Task 2.5: serena scenario runner
**Files:** Create `benchmark/scenarios/serena.py`
- [ ] For comprehension tasks, replace whole-file reads with serena's real semantic outputs: `get_symbols_overview`, `find_symbol`, `find_referencing_symbols` (drive serena's Python tool API or an MCP stdio client against `taskflow`). `input_tokens` = tokens of those targeted outputs; for non-code/command tasks serena falls back to baseline behavior. `output_tokens` unchanged.
- [ ] If serena can't be driven headlessly: mark `modeled=True` and approximate symbol-overview output from the codebase AST, flag it.
- [ ] Verify on task A1/A2 → serena input_tokens < baseline input_tokens.

### Task 2.6: graphify scenario runner
**Files:** Create `benchmark/scenarios/graphify.py`
- [ ] One-time: `graphify .` over `taskflow` to build the graph (record build cost separately). Per comprehension task: use `graphify query/explain/path` and count the query-result tokens as input. Command/explanation tasks fall back to baseline. `output_tokens` unchanged.
- [ ] If graphify unavailable: `modeled=True` from graph.json structure, flagged.
- [ ] Verify on A3 (path) → produces a graph answer with token count.

### Task 2.7: caveman scenario runner
**Files:** Create `benchmark/scenarios/caveman.py`
- [ ] `input_tokens` = baseline input. `output_tokens` = tokens of the **caveman-compressed** reference answer, produced by applying caveman's installed ruleset to each `reference_answer`.
- [ ] If caveman ships a transform CLI, use it; else apply its documented compression rules deterministically and set `modeled=True`, flagged.
- [ ] Verify: caveman output_tokens < baseline output_tokens for every task.

### Task 2.8: Orchestrator
**Files:** Create `benchmark/run_benchmark.py`
- [ ] Loop tasks × {baseline, serena, graphify, rtk, caveman, stacked}. `stacked` = serena-or-graphify input reduction + rtk command compression + caveman output. Compute `Δ%` vs baseline per cell.
- [ ] Write `results/results.json` (full detail incl. `modeled` flags + graphify build cost) and `results/results.csv` (task, scenario, input, output, total, delta_pct).
- [ ] Run: `.venv/bin/python -m benchmark.run_benchmark` → both files created, no scenario crashes.

### Task 2.9: Commit harness
- [ ] `git add benchmark results/environment.md results/results.* && git commit -m "Add benchmark harness and first results"`.

---

## Phase 3: Report

### Task 3.1: Report generator
**Files:** Create `benchmark/make_report.py`
- [ ] Read `results/results.json`; render `REPORT.md` with: title/TL;DR, per-tool explainer, methodology (incl. tokenizer + modeled-flag honesty), codebase + task descriptions, **results tables** (per-task, per-category, aggregate) with %Δ vs baseline, the stacked-combo result, key findings, **combination & which-to-avoid recommendation** (spec §7), limitations (spec §9), and full reproduce steps.
- [ ] Run: `.venv/bin/python -m benchmark.make_report` → `REPORT.md` written.

### Task 3.2: Review & finalize report
- [ ] Read `REPORT.md` end-to-end; verify every number traces to `results.csv`, no placeholders, combinations/avoidance section answers the user's explicit question, limitations are honest about modeled cells.
- [ ] `git add REPORT.md benchmark/make_report.py && git commit -m "Add shareable benchmark report"`.

---

## Phase 4: Wrap up
- [ ] Run `superpowers:verification-before-completion`: re-run `run_benchmark` + `make_report` clean; confirm report claims match results.
- [ ] Invoke `superpowers:finishing-a-development-branch` to offer merge/PR.

---

## Self-Review (done)
- **Spec coverage:** §2 tools → Task 0.2 + scenario runners 2.4–2.7; §3 decomposition → 2.3–2.8; §3.2 tokenizer → 2.1; §4 codebase → Phase 1; §5 tasks → 2.2; §6 engine → Phase 2; §7 combos/avoid → 2.8 stacked + 3.1; §8 deliverables → all; §9 limitations → 3.1. No gaps.
- **Placeholders:** none — each task names exact files/commands/expected results. (Dummy-file *bodies* are specified by responsibility + required symbols, intentionally, since they are illustrative; harness logic shows real code.)
- **Type consistency:** `count_tokens`, `Task` fields, scenario return dict, results schema consistent across tasks.
