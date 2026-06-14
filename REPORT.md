# Do code-context tools actually cut agent tokens? A 5-way benchmark

**serena vs graphify vs rtk vs caveman vs no-tool baseline** — measured on a real codebase with the real tools.

_Generated 2026-06-14 · tokenizer: tiktoken o200k_base · 8 tasks × 6 scenarios · every tool installed and run for real._

## TL;DR

Four tools claim to reduce the tokens an AI coding agent burns. They attack **different layers**, so we measured each on the layer it actually targets, across an 8-task suite over a ~30-file Python app. Totals across all tasks (input context + generated output), vs the no-tool baseline:

| Tool | What it reduces | Total tokens | Δ vs baseline |
|------|-----------------|-------------:|:-------------:|
| **baseline** (no tool) | — | 8,564 | — |
| **serena** | code-read **input** (LSP symbols) | 2,906 | -66.1% |
| **graphify** | code-read **input** (code graph) | 2,948 | -65.6% |
| **rtk** | command-output **input** | 8,148 | -4.9% |
| **caveman** | generated **output** (terse replies) | 8,505 | -0.7% |
| **serena + rtk + caveman** (stacked) | all three layers | 2,602 | -69.6% |

**Headline:** a semantic code-retrieval tool (serena **-66.1%** or graphify **-65.6%**) is by far the biggest single lever. rtk (**-4.9%** overall) and caveman (**-0.7%** overall) look small in aggregate **only because they target narrow slices** — but they're nearly free and stack cleanly: the combined stack hits **-69.6%**. The four are complementary, not competing — except serena vs graphify, which overlap (pick one).

## The five scenarios

| Scenario | Type | Layer | How we ran it |
|----------|------|-------|---------------|
| **baseline** | — | — | Read whole files with the OS; run raw shell commands; full prose answer. |
| **serena** ([oraios/serena](https://github.com/oraios/serena)) | MCP server (LSP) | input: code | Drove its MCP tools `get_symbols_overview` / `find_symbol` / `find_referencing_symbols` over a stdio client instead of reading files. |
| **graphify** ([safishamsi/graphify](https://github.com/safishamsi/graphify)) | CLI + code graph | input: code | Built the graph once with `graphify update` (tree-sitter, no LLM), then `query` / `explain` / `path`. |
| **rtk** ([rtk-ai/rtk](https://github.com/rtk-ai/rtk)) | Rust CLI proxy | input: command output | Ran commands through `rtk read` / `rtk grep` / `rtk test` / `rtk find`. |
| **caveman** ([juliusbrussee/caveman](https://github.com/juliusbrussee/caveman)) | output style compressor | output: replies | Compressed each answer with caveman's real compressor (its prompt + the `claude` CLI). |

The key insight: **serena/graphify/rtk shrink what goes *into* the context; caveman shrinks what the model writes *out*.** Comparing them fairly means splitting every task's cost into an input component and an output component, and letting each tool change only the component it targets.

## Methodology

We do **not** run a live paid LLM (no API key). Instead we model the realistic agent workflow for each task and **measure the real artifact each tool produces**, counted with one consistent tokenizer. Every tool was installed and executed for real — *no tool was modeled from its docs* (see `results/environment.md`).

For each task and scenario:

```
total = input_tokens + output_tokens
Δ%   = (total_tool − total_baseline) / total_baseline
```

| Scenario | input_tokens | output_tokens |
|----------|--------------|---------------|
| baseline | full file reads + raw command output | full prose answer |
| serena   | real symbol-retrieval output | full prose answer |
| graphify | real code-graph query output | full prose answer |
| rtk      | command output / file reads via rtk | full prose answer |
| caveman  | full file reads + raw command output | real caveman-compressed answer |
| stacked  | serena (code) or rtk (commands) | caveman-compressed answer |

Each tool only changes its own component; the rest is held equal to baseline, which isolates each tool's true contribution and makes the stack additive. **Tokenizer:** `tiktoken o200k_base`, applied identically to every scenario — absolute counts are tokenizer-dependent, but the *ratios* we report are robust. **caveman** is the only tool whose mechanism is itself an LLM; we ran the real compressor via the `claude` CLI and committed its outputs as fixtures (`benchmark/fixtures/caveman/`) so the measurement reproduces without re-invoking a model.

**One-time costs (not counted as context tokens):** graphify builds a graph once (`graph.json`, 159 KB here) that is *not* ingested — only query results enter context; serena indexes via its language server once at startup. rtk and caveman need no build.

## The codebase & tasks

`taskflow` is a deliberately realistic ~30-file Python task-manager (REST API + CLI) with a strict `api/cli → services → repositories → db` layering, inheritance (`BaseModel`, `BaseRepository`), cross-module call chains, a deprecated function, scattered TODO/FIXME comments, and a green pytest suite. The 8 tasks span three categories:

| # | Category | Task |
|---|----------|------|
| A1 | Navigation | Locate a class and list its methods — Find the TaskService class and enumerate its public methods. |
| A2 | Navigation | Find all callers of a symbol — Find every place that calls NotificationService.notify. |
| A3 | Navigation | Trace a call path API -> DB — Trace how creating a task via the API reaches the database write. |
| B1 | Commands | Run the test suite and summarize — Run the pytest suite and report pass/fail. |
| B2 | Commands | List the project structure — List all Python source files in the project. |
| B3 | Commands | Grep for deprecated API and TODOs — Find the deprecated old_token_hash function and all TODO/FIXME comments. |
| C1 | Explanation | Explain the architecture — Explain the overall architecture and how the modules interact. |
| C2 | Explanation | Describe adding a feature end-to-end — Describe how to add a due-date field to tasks across all layers. |

## Results

### Aggregate (all 8 tasks)

| Scenario | Input | Output | Total | Δ total |
|----------|------:|-------:|------:|:-------:|
| baseline (no tool) | 7,560 | 1,004 | 8,564 | — |
| serena | 1,902 | 1,004 | 2,906 | -66.1% |
| graphify | 1,944 | 1,004 | 2,948 | -65.6% |
| rtk | 7,144 | 1,004 | 8,148 | -4.9% |
| caveman | 7,560 | 945 | 8,505 | -0.7% |
| serena + rtk + caveman (stacked) | 1,657 | 945 | 2,602 | -69.6% |

Where the savings come from — **input** dropped -74.8% (serena) / -74.3% (graphify) / -5.5% (rtk); **output** dropped -5.9% (caveman). Input is ~88% of the baseline bill here, which is why input tools dominate.

### By category (total tokens, Δ vs baseline)

| Scenario | A · Navigation | B · Commands | C · Explanation |
|----------|:--------------:|:------------:|:---------------:|
| baseline (abs) | 2,934 | 678 | 4,952 |
| serena | -58.6% | +0.0% | -79.6% |
| graphify | -75.1% | +0.0% | -68.9% |
| rtk | -1.9% | -36.1% | -2.3% |
| caveman | -0.9% | +0.7% | -0.7% |
| stacked | -59.5% | -35.4% | -80.3% |

This is the real story: **navigation (A) → graphify wins; explanation (C) → serena wins; commands (B) → rtk wins; everything else is ~0 for the tool outside its niche.**

### Per task (total tokens; Δ% vs baseline for each tool)

| Task | Baseline | serena | graphify | rtk | caveman | stacked |
|------|---------:|:------:|:--------:|:---:|:-------:|:-------:|
| A1 Locate a class and list its methods | 565 | -71.3% | -44.6% | -1.4% | -0.9% | -72.2% |
| A2 Find all callers of a symbol | 607 | -38.2% | -63.3% | -1.2% | -1.8% | -40.0% |
| A3 Trace a call path API -> DB | 1,762 | -61.5% | -89.0% | -2.3% | -0.6% | -62.1% |
| B1 Run the test suite and summarize | 176 | +0.0% | +0.0% | -65.3% | -0.6% | -65.9% |
| B2 List the project structure | 336 | +0.0% | +0.0% | -38.4% | +3.6% | -34.8% |
| B3 Grep for deprecated API and TODOs | 166 | +0.0% | +0.0% | -0.6% | -3.6% | -4.2% |
| C1 Explain the architecture | 3,521 | -85.4% | -64.1% | -2.1% | -0.4% | -85.8% |
| C2 Describe adding a feature end-to-end | 1,431 | -65.2% | -80.7% | -2.8% | -1.6% | -66.8% |

## Key findings

1. **Semantic code retrieval is the big lever.** serena and graphify cut total tokens by ~66% in aggregate — an order of magnitude more than the output/command tools — because reading whole files to answer a question is the single most wasteful thing an agent does. On the trace-a-call-path task, graphify replaced **1,633 tokens of file reads with a 65-token path query (−89%)**.

2. **serena and graphify split the wins by question type.** graphify (a queryable graph) dominates *navigation*: callers (A2), call-path tracing (A3 −89%), feature-impact (C2 −81%). serena (live LSP symbols) dominates *broad comprehension*: single-symbol overviews (A1 −71%) and whole-architecture explanation (C1 −85%). They **overlap** — both reduce code-read input — so installing both is mostly redundant.

3. **rtk is a specialist, and that's fine.** It does ~nothing on code-comprehension tasks (-1.9% on navigation) but owns command output: **-36.1% on the command category** (−65% on the test run, −38% on the structure listing). Its wins scale with output *verbosity* — on our small, green codebase command outputs are short, so this is a **lower bound**; rtk's own 60–90% figures assume noisy build logs and failing test dumps.

4. **caveman is real but small here — and can backfire.** It compressed answers by ~6% overall, but on the terse, list-shaped structure answer (B2) it *added* tokens by wrapping every filename in markdown backticks (103 → 115). Our reference answers are already concise and filler-free — caveman's headline ~65–75% needs the chatty prose, hedging, and pleasantries that a verbose agent emits. Treat its numbers here as a worst case.

5. **The layers are additive.** Because each tool reduces a different component, the stack (serena + rtk + caveman) reaches **-69.6%** — better than any single tool — with no double-counting.

## Which combination — and what to avoid

**Would a combination beat a single tool?** Yes. The tools sit on three independent layers (code-read input / command-output input / generated output), so combining one-per-layer is strictly additive:

- 🥇 **Recommended stack: serena *or* graphify, + rtk, + caveman.** Best measured result (**-69.6%**). Each owns a distinct slice; setup for rtk and caveman is ~zero.

- 🥈 **Just one tool? Pick the code-retrieval one** (serena or graphify) — it alone gets you ~66% and is the only tool that moves the needle on the dominant (code-reading) cost.

- **serena vs graphify — choose by workload.** graphify if your agent mostly *navigates* (impact analysis, call paths, 'who calls X', cross-repo); serena if it mostly *reads broadly and edits* (serena also does semantic edits/renames, which graphify doesn't). graphify is read-only and needs a graph rebuild on code change; serena needs a language server.

**What to avoid:**

- ❌ **Don't run serena *and* graphify together** — they reduce the same component, so you pay two integrations for one benefit. Pick one.

- ❌ **Don't reach for rtk to fix comprehension cost** — it's ~0% there. Add it *for* command-heavy loops (tests, builds, git, greps), where it's excellent.

- ❌ **Don't expect caveman to move your bill on input-heavy work** (-0.7% overall), and watch it on terse/structured output. It's a cheap complement for chatty, output-heavy chat — not a primary lever for codebase work.

## Appendix: real before/after artifacts

**A1 — "list TaskService's methods."** Baseline reads the whole file (458 tokens). serena returns:

```json
{"Class": [{"TaskService": {"Method": ["__init__", "create_task", "assign_task", "complete_task", "open_tasks"]}}]}
```

That's ~55 tokens — same answer, **−71%**.

**A3 — "trace create-task to the DB write."** Baseline reads 5 files across 4 layers (1,633 tokens). graphify returns a path (~65 tokens, **−89%**):

```
Shortest path (3 hops):
  .create_task() <--method-- TaskService <--calls-- build_services() --references--> Database
```

**caveman — "add a due_date feature" (C2).** Prose answer, compressed in place:

> _before:_ "…Because BaseModel.to_dict uses asdict, it is serialized automatically."

> _after:_ "…BaseModel.to_dict use asdict → serialize auto."

## Reproduce it yourself

```bash
# 1. Harness deps
uv venv .venv && uv pip install --python .venv/bin/python tiktoken pytest

# 2. Install the four tools
uv tool install graphifyy
uv tool install --python 3.13 serena-agent
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash

# 3. Run + report
PATH="$HOME/.local/bin:$PATH" .venv/bin/python -m benchmark.run_benchmark
.venv/bin/python -m benchmark.make_report
```

Results are written to `results/results.json` and `results/results.csv`; this report is regenerated from them. caveman compression reuses committed fixtures unless you pass `--regenerate-caveman` (requires the `claude` CLI or an `ANTHROPIC_API_KEY`).

## Limitations (read before believing the numbers)

- **Modeled, not metered.** Token usage is computed from the *real artifacts each tool produces*, not metered from a live LLM session. Real agents add reasoning, retries, and non-determinism; exact totals will differ, but the relative picture is what we claim.

- **One small, clean codebase.** ~30 files, all tests green. This **understates rtk** (short command output) and **understates caveman** (concise answers, no filler to cut). Bigger/noisier repos would widen their wins.

- **One tokenizer.** Absolute counts vary by tokenizer; ratios are stable.

- **Reference answers are ours.** Every input-side scenario shares one canonical answer, so the input comparison is apples-to-apples; but a different answer style would shift caveman's numbers.

- **One retrieval per task.** We count a single tool call (or file-read set) per task. A whole-file read is self-contained, whereas a terse graph path may in practice need a follow-up query — so this slightly favors the retrieval tools (serena/graphify). The effect is small relative to the gaps shown.

- **Single run.** Deterministic for the input tools; caveman output is fixed via committed fixtures.

