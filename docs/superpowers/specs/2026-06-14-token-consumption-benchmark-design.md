# Token-Consumption Benchmark — Design Spec

**Date:** 2026-06-14
**Status:** Approved (pending spec review)

## 1. Goal

Quantify how much each of four "token-saving" code-context tools reduces the token
consumption of an AI coding agent, relative to a no-tool baseline, on a standardized
benchmark over a realistic dummy codebase. Produce a shareable Markdown report
(team-internal and Hacker-News-ready) covering: what each tool does, whether and how
well it tackles the problem, token consumption per scenario, percentage increase/decrease
vs. baseline, **which combinations (if any) make more sense than a single tool, and which
tools (if any) to avoid.**

## 2. Tools under test

| Tool | Type | Layer it reduces | Install |
|------|------|------------------|---------|
| **baseline** | — | nothing (control) | — |
| **serena** (oraios/serena) | MCP server, LSP-based | **input** — semantic symbol retrieval instead of whole-file reads | `uv tool install serena-agent` |
| **graphify** (safishamsi/graphify) | CLI + optional MCP | **input** — query a code knowledge graph instead of grepping/reading | `uv tool install graphifyy` |
| **rtk** (rtk-ai/rtk) | Rust CLI proxy | **input** — compresses verbose *command output* (pytest/git/ls/grep/cat) | cargo / curl |
| **caveman** (juliusbrussee/caveman) | skill / style ruleset | **output** — terse "caveman" replies, fewer generated tokens | curl installer |

Key insight driving the design: **serena/graphify/rtk reduce tokens going *into* context;
caveman reduces tokens coming *out*.** A fair benchmark must measure both components.

## 3. Measurement methodology (deterministic, artifact-based)

`ANTHROPIC_API_KEY` is not available, so we do **not** run a live LLM. Instead, for each
task we model the realistic agent workflow and measure the **real artifacts** each tool
produces, counted with a real tokenizer.

### 3.1 Token decomposition

For each task `t` and scenario `s`:

```
total(t,s) = input_tokens(t,s) + output_tokens(t,s)
Δ%(t,s)    = (total(t,s) - total(t,baseline)) / total(t,baseline) * 100
```

| Scenario | input_tokens | output_tokens |
|----------|--------------|---------------|
| baseline | full file reads + raw command output | full prose answer |
| serena   | real symbol-targeted retrieval output | full prose answer |
| graphify | real code-graph query output | full prose answer |
| rtk      | raw command output piped through the real rtk binary | full prose answer |
| caveman  | full file reads + raw command output | caveman-compressed reply (real ruleset) |

Each tool only alters the component it actually targets; the others are held equal to
baseline. This isolates each tool's true contribution and makes combinations additive
and analyzable.

### 3.2 Tokenizer

`tiktoken` with `o200k_base` encoding, applied identically to every scenario. Absolute
token counts are tokenizer-dependent; the **ratios** between scenarios (the thing we report)
are robust across tokenizers. This is stated explicitly in the report's limitations.

### 3.3 Real tools, graceful fallback

All four tools are really installed and really executed to produce the measured artifacts.
Any tool that cannot be installed/run in the environment is **clearly flagged** in the
report and modeled from its published spec — never silently faked. caveman's compression
is a documented transformation ruleset, applied faithfully to the reference replies (no LLM
needed).

## 4. Dummy codebase — `taskflow`

A realistic ~25–30 file Python task-management application (REST API + CLI):

```
taskflow/
  __init__.py  config.py  db.py  cli.py
  models/        base.py user.py task.py project.py
  repositories/  base_repo.py user_repo.py task_repo.py project_repo.py
  services/      auth_service.py task_service.py project_service.py notification_service.py
  api/           app.py deps.py routes_users.py routes_tasks.py routes_projects.py
  utils/         validation.py dates.py logging.py
tests/           test_task_service.py test_auth_service.py test_repositories.py test_api.py
```

Deliberate features that exercise the tools:
- **Inheritance** (`models/base.py`, `repositories/base_repo.py`) — symbol hierarchies.
- **Cross-module call chains** (api → service → repo → db) — call-path tracing.
- A **deprecated** function (e.g. `old_token_hash()`) and scattered `TODO`/`FIXME` comments — grep targets.
- A **runnable pytest suite** — real test-runner output for rtk.

## 5. Task suite (~8 tasks, 3 categories)

- **A. Comprehension / navigation** (favors serena, graphify)
  - A1: Locate a class and enumerate its methods.
  - A2: Find all references/callers of a given symbol.
  - A3: Trace the call path from an API route to the DB write.
- **B. Command / diagnostic** (favors rtk)
  - B1: Run the pytest suite and summarize pass/fail.
  - B2: List the project structure / all Python files.
  - B3: grep for the deprecated API and all TODO/FIXME comments.
- **C. Explanation** (favors caveman; its output reduction applies to *every* task's reply)
  - C1: Explain the project architecture and module interactions.
  - C2: Describe how to add a new feature end-to-end.

Each task ships with: a goal, the canonical baseline workflow (exact files/commands), and a
single canonical reference answer (the "output" component, identical across input-side tools).

## 6. Measurement engine

A Python harness in `benchmark/`:
- `tasks.py` — task definitions (goal, baseline files/commands, reference answer).
- `tokenizer.py` — `tiktoken` o200k_base wrapper.
- `scenarios/` — one runner per tool producing its real artifact for each task.
- `run_benchmark.py` — orchestrates all task×scenario cells, writes `results/results.json` and `results/results.csv`.
- `make_report.py` — renders `REPORT.md` tables and deltas from the results.

## 7. Combination & avoidance analysis (explicit report requirement)

Beyond the 5 single scenarios, the report must answer **"would a combination beat any single
tool, and which (if any) should be avoided?"** Supported by data:
- A **stacked** scenario (serena + rtk + caveman) measured the same way, plus reasoning about
  which combinations are complementary (reduce different components) vs. redundant (serena vs.
  graphify both reduce code-retrieval input — overlapping).
- Per-category results expose where each tool helps or hurts (e.g., a tool that *adds* tokens
  on tasks outside its niche, or whose one-time index/build cost outweighs savings on a small task).
- Concrete recommendation: best single tool, best combination, and any tool to avoid (for whom / when).

## 8. Deliverables

- `taskflow/` — dummy codebase.
- `benchmark/` — harness, tasks, scenario runners.
- `results/` — `results.json`, `results.csv`.
- `REPORT.md` — shareable report: intro, per-tool explainer, methodology, codebase + task
  descriptions, results tables (per-task / per-category / aggregate), %Δ vs baseline, key
  findings, combination & avoidance recommendation, limitations, and full reproduce steps.

## 9. Limitations (to be stated in the report)

- Token usage is **modeled from real tool artifacts**, not metered from a live LLM session
  (no API key). Real agent runs vary with model, prompting, and non-determinism.
- Single tokenizer proxy; absolute numbers vary by tokenizer, ratios are stable.
- A single dummy Python codebase and an ~8-task suite — directional, not a universal verdict.
- Caveman's output compression is applied via its documented ruleset, not a live model.
```
