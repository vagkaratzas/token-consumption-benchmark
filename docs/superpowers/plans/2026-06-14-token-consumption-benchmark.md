# Token-Consumption Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a reproducible benchmark that measures how much serena, graphify, rtk, and caveman reduce an AI agent's token consumption versus a no-tool baseline, and produce a shareable Markdown report.

**Architecture:** A generated Python dummy codebase (`taskflow`) is probed by an ~8-task suite. For each task×scenario, a Python harness measures the real artifact each tool produces, splits cost into input+output tokens (tiktoken o200k_base), and writes results that a report generator renders into `REPORT.md`.

**Tech Stack:** Python 3, tiktoken, uv (graphify/serena), cargo/curl (rtk), npm/curl (caveman), pytest.

**Execution note:** Phase 0 is exploratory — installs may fail. Record exactly what installs and what doesn't; fall back to documented-spec modeling for any failure and flag it in the report. Do not silently fake tool output.

---

## Phase 0: Environment & tool installation

### Task 0.1: Record environment + install base deps ✅
**Files:** Create `results/environment.md`
- [x] Capture versions: `python3 --version`, `uv --version`, `cargo --version`, `node --version`, `git --version`.
- [x] Install harness deps into a venv: `uv venv .venv && .venv/bin/python -m pip install tiktoken pytest` (or `uv pip install`).
- [x] Verify tiktoken loads: `.venv/bin/python -c "import tiktoken; print(tiktoken.get_encoding('o200k_base').encode('hello world'))"` → expect a list of ints.
- [x] Write captured versions to `results/environment.md`.

### Task 0.2: Install the four tools (best-effort, record outcomes) ✅
**Files:** Append to `results/environment.md` an "Install outcomes" table.
- [x] graphify: `uv tool install graphifyy`; verify `graphify --help`. Record PASS/FAIL + version. → PASS v0.8.39
- [x] serena: `uv tool install serena-agent` (or `--python 3.13`); verify `serena --help` / importable. Record PASS/FAIL. → PASS 1.5.3
- [x] rtk: try `cargo install rtk` then fallback `curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh`; verify `rtk --version`. Record PASS/FAIL. → PASS 0.42.4 (curl)
- [x] caveman: `curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash`; locate the installed compression ruleset/skill files. Record PASS/FAIL + path to ruleset. → PASS (LLM-based compressor via `claude` CLI)
- [x] For each FAIL, note the error and that the report will model it from spec. → no failures; all four run for real.

---

## Phase 1: Build the `taskflow` dummy codebase

### Task 1.1: Package skeleton + config/db ✅
**Files:** Create `taskflow/__init__.py`, `taskflow/config.py`, `taskflow/db.py`
- [x] `config.py`: `Settings` dataclass (db_path, secret_key, page_size) + `load_settings()`.
- [x] `db.py`: tiny in-memory `Database` class with `tables: dict[str, dict]`, `insert/get/list/update/delete`, used by repositories. This is the call-chain leaf (api→service→repo→**db**).
- [x] Verify import: `.venv/bin/python -c "import taskflow.db"` → no error.

### Task 1.2: Models with inheritance ✅
**Files:** Create `taskflow/models/__init__.py`, `base.py`, `user.py`, `task.py`, `project.py`
- [x] `base.py`: `BaseModel` (id, created_at, `to_dict()`, `touch()`). All others subclass it (symbol hierarchy for serena/graphify).
- [x] `user.py`: `User(BaseModel)` (email, name, password_hash, role).
- [x] `task.py`: `Task(BaseModel)` (title, status, assignee_id, project_id) + `Status` enum.
- [x] `project.py`: `Project(BaseModel)` (name, owner_id, member_ids).
- [x] Verify import of each.

### Task 1.3: Repositories with inheritance ✅
**Files:** Create `taskflow/repositories/__init__.py`, `base_repo.py`, `user_repo.py`, `task_repo.py`, `project_repo.py`
- [x] `base_repo.py`: `BaseRepository` generic CRUD over `Database` (`add/get/list/update/remove`).
- [x] `user_repo.py`: `UserRepository(BaseRepository)` + `get_by_email()`.
- [x] `task_repo.py`: `TaskRepository(BaseRepository)` + `list_by_project()`, `list_by_assignee()`.
- [x] `project_repo.py`: `ProjectRepository(BaseRepository)` + `list_by_owner()`.
- [x] Verify imports.

### Task 1.4: Services (business logic + deprecated fn + TODOs) ✅
**Files:** Create `taskflow/services/__init__.py`, `auth_service.py`, `task_service.py`, `project_service.py`, `notification_service.py`
- [x] `auth_service.py`: `AuthService` with `hash_password()` (current) and a **deprecated** `old_token_hash()` (grep target B3) marked with a docstring deprecation note; `register()`, `authenticate()`.
- [x] `task_service.py`: `TaskService.create_task()`, `assign_task()`, `complete_task()` — calls `TaskRepository` and `NotificationService` (cross-module refs for A2/A3). Add 2–3 `# TODO:` / `# FIXME:` comments (grep targets B3).
- [x] `project_service.py`: `ProjectService.create_project()`, `add_member()`.
- [x] `notification_service.py`: `NotificationService.notify()` (referenced by task_service).
- [x] Verify imports.

### Task 1.5: API layer + CLI (call-chain roots) ✅
**Files:** Create `taskflow/api/__init__.py`, `app.py`, `deps.py`, `routes_users.py`, `routes_tasks.py`, `routes_projects.py`, `taskflow/cli.py`
- [x] `deps.py`: wires `Database` → repositories → services (dependency container).
- [x] `app.py`: minimal framework-free `App` with a `route()` registry + `dispatch(method, path, body)`.
- [x] `routes_tasks.py`: handlers calling `TaskService` (root of api→service→repo→db chain for A3).
- [x] `routes_users.py`, `routes_projects.py`: analogous handlers.
- [x] `cli.py`: `main(argv)` dispatching subcommands to services (second call-chain root).
- [x] Verify: `.venv/bin/python -m taskflow.cli --help`-style smoke (or `python -c` import). → CLI created user 1

### Task 1.6: utils + tests (runnable pytest suite for rtk) ✅
**Files:** Create `taskflow/utils/__init__.py`, `validation.py`, `dates.py`, `logging.py`; `tests/test_task_service.py`, `test_auth_service.py`, `test_repositories.py`, `test_api.py`
- [x] utils: `validation.validate_email()`, `dates.format_iso()`, `logging.get_logger()`.
- [x] Tests covering services/repos/api so `pytest` produces realistic multi-line output (B1). All tests should PASS.
- [x] Run: `.venv/bin/python -m pytest -q` → expect all green. → 13 passed.

### Task 1.7: Commit codebase ✅
- [x] `git add taskflow tests && git commit -m "Add taskflow dummy codebase"`.

---

## Phase 2: Benchmark harness

> **Implementation note:** the separate `scenarios/*.py` files in Tasks 2.3–2.7 were consolidated into two modules — `benchmark/tools.py` (real artifact producers: `read_files`, `run_cmd`, `rtk_read`, `graphify_build/run`, `caveman_compress`) and `benchmark/serena_client.py` (stdio MCP client) — driven by the `benchmark/run_benchmark.py` orchestrator (Task 2.8). Same behavior, fewer files. Tasks 2.3–2.8 are checked off once the orchestrator run verifies them end-to-end.

### Task 2.1: Tokenizer wrapper ✅
**Files:** Create `benchmark/__init__.py`, `benchmark/tokenizer.py`
- [x] `tokenizer.py`:
```python
import tiktoken
_ENC = tiktoken.get_encoding("o200k_base")
def count_tokens(text: str) -> int:
    return len(_ENC.encode(text or ""))
```
- [x] Behavior: `count_tokens("") == 0` and `count_tokens("hello world") > 0` (validated inline; tiktoken `o200k_base`).

### Task 2.2: Task definitions ✅
**Files:** Create `benchmark/tasks.py`
- [x] Define a `Task` dataclass: `id, category (A/B/C), goal, baseline_files, baseline_commands, rtk_read_files, rtk_commands, serena_calls, graphify_argv, reference_answer`.
- [x] Define `TASKS` = the 8 tasks from spec §5. For each, fill the exact files/commands and a single canonical `reference_answer`, plus the per-tool invocation specs.
- [x] Verify: `.venv/bin/python -c "from benchmark.tasks import TASKS; print(len(TASKS))"` → 8.

### Task 2.3: Baseline scenario runner ✅ (in `tools.read_files`/`run_cmd` + orchestrator)
- [x] `input_tokens` = tokens(baseline_files content) + tokens(raw `baseline_commands` output, run for real). `output_tokens` = tokens(reference_answer).
- [x] Verify on task A1 → positive numbers (A1 baseline in=458 out=107).

### Task 2.4: rtk scenario runner ✅ (in `tools.rtk_read` + orchestrator)
- [x] Command output / file reads routed through the real `rtk` (`rtk read/grep/test/find`). `output_tokens` unchanged from baseline.
- [x] rtk installed → ran for real (no modeling needed).
- [x] Verify on B1 (pytest) → rtk in=17 ≤ baseline in=132 (−65%).

### Task 2.5: serena scenario runner ✅ (in `serena_client.py` + orchestrator)
- [x] Comprehension tasks use real `get_symbols_overview`/`find_symbol`/`find_referencing_symbols` via a stdio MCP client; command tasks fall back to baseline. `output_tokens` unchanged.
- [x] serena driven headlessly for real (no modeling needed).
- [x] Verify on A1/A3 → serena in < baseline in (A1 55<458, A3 550<1633).

### Task 2.6: graphify scenario runner ✅ (in `tools.graphify_build/run` + orchestrator)
- [x] One-time `graphify update taskflow` builds the graph (tree-sitter, no LLM). Per task: `query`/`explain`/`path` result tokens = input. Command tasks fall back to baseline. `output_tokens` unchanged.
- [x] graphify ran for real (no modeling needed).
- [x] Verify on A3 (path) → 65 tokens (−89%).

### Task 2.7: caveman scenario runner ✅ (in `tools.caveman_compress` + orchestrator)
- [x] `input_tokens` = baseline input. `output_tokens` = tokens of the **real** caveman-compressed answer (caveman's own prompt + `claude` CLI), cached to `benchmark/fixtures/caveman/`.
- [x] caveman ran for real (no modeling needed).
- [x] Verify: caveman output ≤ baseline output for 7/8 tasks; B2 grew +12 (caveman added markdown backticks) — recorded as an honest finding.

### Task 2.8: Orchestrator ✅
**Files:** `benchmark/run_benchmark.py`
- [x] Loop tasks × {baseline, serena, graphify, rtk, caveman, stacked}. `stacked` = serena (code) or rtk (commands) for input + caveman output. Compute `Δ%` per cell.
- [x] Write `results/results.json` and `results/results.csv`.
- [x] Run → both files created, no scenario crashes (exit 0).

### Task 2.9: Commit harness ✅
- [x] `git add benchmark results/* && git commit` → commit c8f68f4.

---

## Phase 3: Report

### Task 3.1: Report generator ✅
**Files:** `benchmark/make_report.py`
- [x] Read `results/results.json`; render `REPORT.md` with TL;DR, per-tool explainer, methodology (tokenizer + "all tools run for real" honesty), codebase + task descriptions, results tables (per-task, per-category, aggregate) with %Δ, the stacked combo, key findings, **combination & which-to-avoid recommendation**, limitations, reproduce steps, and a real before/after appendix.
- [x] Run: `.venv/bin/python -m benchmark.make_report` → `REPORT.md` written (all numbers computed from results, so they can't drift).

### Task 3.2: Review & finalize report ✅
- [x] Read `REPORT.md` end-to-end; numbers cross-checked against `results.csv` (serena −66.1%, graphify −65.6%, rtk −4.9%, caveman −0.7%, stacked −69.6%); placeholder scan clean; combinations/avoidance section answers the explicit ask; limitations honest (modeled-not-metered, small codebase understating rtk/caveman, one-retrieval-per-task).
- [x] `git commit` → c1803db (also updated repo README to point at the report).

---

## Phase 4: Wrap up
- [ ] Run `superpowers:verification-before-completion`: re-run `run_benchmark` + `make_report` clean; confirm report claims match results.
- [ ] Invoke `superpowers:finishing-a-development-branch` to offer merge/PR.

---

## Self-Review (done)
- **Spec coverage:** §2 tools → Task 0.2 + scenario runners 2.4–2.7; §3 decomposition → 2.3–2.8; §3.2 tokenizer → 2.1; §4 codebase → Phase 1; §5 tasks → 2.2; §6 engine → Phase 2; §7 combos/avoid → 2.8 stacked + 3.1; §8 deliverables → all; §9 limitations → 3.1. No gaps.
- **Placeholders:** none — each task names exact files/commands/expected results. (Dummy-file *bodies* are specified by responsibility + required symbols, intentionally, since they are illustrative; harness logic shows real code.)
- **Type consistency:** `count_tokens`, `Task` fields, scenario return dict, results schema consistent across tasks.
