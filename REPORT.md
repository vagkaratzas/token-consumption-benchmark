# Do code-context tools actually cut agent tokens? A 6-tool benchmark

**serena vs graphify vs CodeGraph vs rtk vs caveman vs Ponytail vs a no-tool baseline** — measured on a real codebase with the real tools.

_Generated 2026-06-21 · tokenizer: tiktoken o200k_base · 6 tools (+ a stacked combo) vs a no-tool baseline · 8 comprehension tasks + 1 code-gen task · 5 tools run for real, 1 (Ponytail) modeled._

## TL;DR

Six tools claim to cut the tokens an AI coding agent burns. They attack **different layers** of the bill, so we measured each on the layer it actually targets, across an 8-task comprehension suite over a ~30-file Python app (plus a code-generation task for the one tool that needs it). Totals across the comprehension suite (input context + generated output), vs the no-tool baseline:

| Tool | Layer it targets | Total tokens | Δ vs baseline |
|------|------------------|-------------:|:-------------:|
| **baseline** (no tool) | — | 8,564 | — |
| **serena** | code-read **input** (LSP symbols) | 2,906 | -66.1% |
| **graphify** | code-read **input** (code graph) | 2,948 | -65.6% |
| **CodeGraph** | code-read **input** (indexed graph) | 3,932 | -54.1% |
| **rtk** | command-output **input** | 8,171 | -4.6% |
| **caveman** | generated **prose output** | 8,505 | -0.7% |
| **stacked** (serena + rtk + caveman) | three layers at once | 2,602 | -69.6% |
| **Ponytail** | generated **code output** | n/a here | 0% (no code generated) |

**Headline:** a semantic code-retrieval tool is by far the biggest single lever — serena **-66.1%**, graphify **-65.6%**, CodeGraph **-54.1%** in aggregate. The three *overlap* (all shrink code-read input — pick one), but they split the wins by question type: serena on broad comprehension, graphify on call-path tracing, CodeGraph on pinpoint caller lookups. rtk (**-4.6%** overall) and caveman (**-0.7%**) look small in aggregate **only because they target narrow slices** — but they're nearly free and stack cleanly: serena + rtk + caveman hits **-69.6%**. **Ponytail** is invisible on this suite (it cuts *generated code*, which comprehension tasks don't produce) but trimmed a verbose implementation by **~40% in our illustration** (authoring-dependent — see the code-generation section). Tools are complementary, not competing — except the three code-read tools, which are mutually redundant.

## The six tools (and the four layers)

Token cost splits into four layers; a different tool owns each. The first two are *input* (what enters context); the last two are *output* (what the model writes back).

| Tool | Type | Layer | How we ran it |
|------|------|-------|---------------|
| **serena** ([oraios/serena](https://github.com/oraios/serena)) | MCP server (LSP) | input: code | Drove its MCP tools `get_symbols_overview` / `find_symbol` / `find_referencing_symbols` over a stdio client instead of reading files. |
| **graphify** ([safishamsi/graphify](https://github.com/safishamsi/graphify)) | CLI + code graph | input: code | Built the graph once with `graphify update` (tree-sitter, no LLM), then `query` / `explain` / `path`. |
| **CodeGraph** ([colbymchenry/codegraph](https://github.com/colbymchenry/codegraph)) | CLI + indexed graph (SQLite) | input: code | Indexed once with `codegraph init`, then `node` / `callers` / `impact` / `explore`. |
| **rtk** ([rtk-ai/rtk](https://github.com/rtk-ai/rtk)) | Rust CLI proxy | input: command output | Ran commands through `rtk read` / `rtk grep` / `rtk test` / `rtk find`. |
| **caveman** ([juliusbrussee/caveman](https://github.com/juliusbrussee/caveman)) | output-style compressor | output: prose | Compressed each answer with caveman's real compressor (its prompt + the `claude` CLI). |
| **Ponytail** ([DietrichGebert/ponytail](https://github.com/DietrichGebert/ponytail)) | behavioural plugin (rules) | output: code | Applied its real "lazy senior dev" rule text to a fixed verbose implementation via the `claude` CLI (modeled — no headless CLI). |

The key insight: **serena / graphify / CodeGraph / rtk shrink what goes *into* the context; caveman and Ponytail shrink what the model writes *out* — caveman for prose, Ponytail for code.** Comparing them fairly means splitting every task's cost into an input component and an output component, and letting each tool change only the component it targets.

## Methodology

We do **not** run a live paid LLM (no API key). Instead we model the realistic agent workflow for each task and **measure the real artifact each tool produces**, counted with one consistent tokenizer.

For each task and scenario:

```
total = input_tokens + output_tokens
Δ%   = (total_tool − total_baseline) / total_baseline
```

Each tool only changes its own component; the rest is held equal to baseline, which isolates each tool's true contribution and makes the stack additive. **Tokenizer:** `tiktoken o200k_base`, applied identically to every scenario — absolute counts are tokenizer-dependent, but the *ratios* we report are robust.

**What "run for real" means per tool:**

- **serena, graphify, CodeGraph, rtk** — installed and executed; we count their actual output. Fully deterministic.

- **caveman** — its mechanism *is* an LLM, so we ran the real compressor via the `claude` CLI and committed the outputs as fixtures (`benchmark/fixtures/caveman/`); the measurement reproduces without re-invoking a model.

- **Ponytail** — ships **no headless CLI**; it is a behavioural plugin (a rules prompt that biases an agent toward minimal code). We therefore **model** it: feed its *real* rule text plus a fixed, representative verbose implementation to the `claude` CLI and ask it to apply that philosophy, then commit the result as a fixture (`benchmark/fixtures/ponytail/`). This is a comparison of two non-equivalent solutions (verbose vs. minimal) — softer than the deterministic cells — so we keep it out of the headline aggregate and flag it as illustrative.

**One-time costs (not counted as context tokens):** graphify builds a graph once (`graph.json`, 159 KB) and CodeGraph an SQLite index once (`.codegraph/`, 412 KB) — neither is ingested; only query results enter context. serena indexes via its language server once at startup. rtk, caveman and Ponytail need no build.

## The codebase & tasks

`taskflow` is a deliberately realistic ~30-file Python task-manager (REST API + CLI) with a strict `api/cli → services → repositories → db` layering, inheritance (`BaseModel`, `BaseRepository`), cross-module call chains, a deprecated function, scattered TODO/FIXME comments, and a green pytest suite. The comprehension suite spans three categories; one code-generation task is added for the output-code layer:

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
| D1 | Code generation | Implement a due-date field across all layers — Write the code that adds a due_date field to tasks end-to-end. |

## Results — comprehension suite (8 tasks)

### Aggregate

| Scenario | Input | Output | Total | Δ total |
|----------|------:|-------:|------:|:-------:|
| baseline (no tool) | 7,560 | 1,004 | 8,564 | — |
| serena | 1,902 | 1,004 | 2,906 | -66.1% |
| graphify | 1,944 | 1,004 | 2,948 | -65.6% |
| CodeGraph | 2,928 | 1,004 | 3,932 | -54.1% |
| rtk | 7,167 | 1,004 | 8,171 | -4.6% |
| caveman | 7,560 | 945 | 8,505 | -0.7% |
| stacked (serena + rtk + caveman) | 1,657 | 945 | 2,602 | -69.6% |
| Ponytail | 7,560 | 1,004 | 8,564 | +0.0% |

Where the savings come from — **code-read input** dropped -74.8% (serena) / -74.3% (graphify) / -61.3% (CodeGraph); **command input** -5.2% (rtk); **prose output** -5.9% (caveman). Ponytail is flat here (no code to minimise). Input is ~88% of the baseline bill on this suite, which is why the code-read tools dominate.

### By category (total tokens, Δ vs baseline)

| Scenario | A · Navigation | B · Commands | C · Explanation |
|----------|:--------------:|:------------:|:---------------:|
| baseline (abs) | 2,934 | 678 | 4,952 |
| serena | -58.6% | +0.0% | -79.6% |
| graphify | -75.1% | +0.0% | -68.9% |
| codegraph | -64.6% | +0.0% | -55.3% |
| rtk | -1.1% | -36.1% | -2.3% |
| caveman | -0.9% | +0.7% | -0.7% |
| stacked | -59.5% | -35.4% | -80.3% |

The real story: **navigation (A) → the code-read tools split it** (serena best at listing a class's members, CodeGraph best at callers, graphify best at call paths); **explanation (C) → serena/graphify**; **commands (B) → rtk**; everything else is ~0 for the tool outside its niche.

### Per task (total tokens; Δ% vs baseline)

| Task | Baseline | serena | graphify | CodeGraph | rtk | caveman | stacked |
|------|---------:|:------:|:--------:|:---------:|:---:|:-------:|:-------:|
| A1 Locate a class and list its methods | 565 | -71.3% | -44.6% | -38.6% | +2.7% | -0.9% | -72.2% |
| A2 Find all callers of a symbol | 607 | -38.2% | -63.3% | -78.4% | -1.2% | -1.8% | -40.0% |
| A3 Trace a call path API -> DB | 1,762 | -61.5% | -89.0% | -68.2% | -2.3% | -0.6% | -62.1% |
| B1 Run the test suite and summarize | 176 | +0.0% | +0.0% | +0.0% | -65.3% | -0.6% | -65.9% |
| B2 List the project structure | 336 | +0.0% | +0.0% | +0.0% | -38.4% | +3.6% | -34.8% |
| B3 Grep for deprecated API and TODOs | 166 | +0.0% | +0.0% | +0.0% | -0.6% | -3.6% | -4.2% |
| C1 Explain the architecture | 3,521 | -85.4% | -64.1% | -45.0% | -2.1% | -0.4% | -85.8% |
| C2 Describe adding a feature end-to-end | 1,431 | -65.2% | -80.7% | -80.5% | -2.8% | -1.6% | -66.8% |

## Results — code generation (Ponytail's home turf)

Task **D1 — Write the code that adds a due_date field to tasks end-to-end.** The output here is *generated code*, not prose. The baseline is a representative verbose implementation (684 output tokens) — the kind a default agent emits: an unrequested `is_overdue` property, an overdue-query helper threaded through service + repo, defensive parsing, and a multi-assert test. Two output tools then act on that fixed artifact:

| Scenario | Input | Output | Total | Δ total | What changed |
|----------|------:|-------:|------:|:-------:|--------------|
| baseline | 1,229 | 684 | 1,913 | — |  |
| serena | 296 | 684 | 980 | -48.8% | output unchanged |
| graphify | 74 | 684 | 758 | -60.4% | output unchanged |
| codegraph | 77 | 684 | 761 | -60.2% | output unchanged |
| caveman | 1,229 | 681 | 1,910 | -0.2% | keeps code blocks ~verbatim |
| ponytail | 1,229 | 400 | 1,629 | -14.8% | drops unrequested scope |
| stacked | 296 | 400 | 696 | -63.6% | both layers |

On the **output component alone**, Ponytail cut the implementation **684 → 400 tokens (-41.5%)** by deleting the speculative helpers and derived property the feature never asked for; **caveman barely moved it (-0.4%)** because it compresses prose and leaves code blocks intact. That is the mirror image of the comprehension suite, where caveman helps and Ponytail doesn't — they own different *output* layers (prose vs. code). The code-read tools still help on the *input* side of a codegen task, so the best stack here is a code-read tool **+ Ponytail** (**-63.6%**).

> ⚠️ **This number is illustrative, not a clean measurement.** Both sides are choices we made: we *authored* the verbose baseline to contain typical scope creep, and the size of Ponytail's cut depends on how much removable scope we assumed and how the rule prompt is framed. Concretely, a "preserve the existing behaviour" framing trimmed only **−1.6%**, while a "deliver only the requested feature" framing (the realistic one for a YAGNI plugin) trimmed **−41.5%** — a 25× swing. We report the latter because it matches how Ponytail is meant to be used (and its own "~54% less code" claim), but the honest read is *direction and rough magnitude*, not a deterministic figure like the other tools'.

## Key findings

1. **Semantic code retrieval is the big lever.** serena, graphify and CodeGraph each cut comprehension-suite tokens by ~66/66/54% — an order of magnitude more than the output/command tools — because reading whole files to answer a question is the single most wasteful thing an agent does. On the trace-a-call-path task, graphify replaced **1,633 tokens of file reads with a 65-token path query (−89%)**.

2. **The three code-read tools overlap but split the wins by question type.** They reduce the *same* layer, so installing more than one is mostly redundant — but each has a best event: **serena** on listing a class's members (A1 -71.3%) and whole-architecture explanation (C1 -85.4%); **graphify** on call-path tracing (A3 -89.0%); **CodeGraph** on pinpoint caller lookups (A2 -78.4%, the best single result on that task).

3. **CodeGraph trades broad-query leanness for fewer follow-ups.** Its aggregate (-54.1%) trails serena/graphify because its `explore` command returns *verbatim source* inline (C1 -45.0%, vs serena's outline-only −85%). That's a deliberate design choice — it hands back the code so the agent doesn't re-read — and our "one retrieval per task" rule doesn't credit the follow-up reads it saves. On targeted lookups (`node`/`callers`/`impact`) it's right there with the others.

4. **rtk is a command-output specialist.** It does ~nothing on code-comprehension (-1.1% on navigation) but owns command output: **-36.1% on the command category** (−65% on the test run, −38% on the structure listing). Its wins scale with output *verbosity* — our small green codebase has short command output, so this is a **lower bound**; rtk's own 60–90% figures assume noisy build logs and failing test dumps.

5. **caveman and Ponytail are mirror-image output tools.** caveman compresses *prose* (~6% on answers, and it can even *add* tokens on terse/list output by wrapping items in markdown). Ponytail minimises *code* (**~40% in our illustration**, authoring-dependent — see the caveat in the code-generation section) and is invisible on prose. Each is useless in the other's lane — route by whether the output is prose or code.

6. **The layers are additive.** Because each tool reduces a different component, stacking one per layer beats any single tool: serena + rtk + caveman = **-69.6%** on comprehension; a code-read tool + Ponytail ≈ **-63.6%** on code generation (the code-read half is measured; the Ponytail half is the illustrative cut above) — with no double-counting.

## Which combination — and what to avoid

**Would a combination beat a single tool?** Yes. The tools sit on four independent layers (code-read input / command-output input / prose output / code output), so combining one-per-layer is strictly additive:

- 🥇 **Comprehension / navigation work:** *(serena **or** graphify **or** CodeGraph)* + **rtk** + **caveman**. Best measured result (**-69.6%**). Each owns a distinct slice; rtk and caveman cost ~zero to add.

- 🥇 **Code-generation work:** *(a code-read tool)* + **Ponytail** (≈**-63.6%** on the codegen task, with Ponytail's share illustrative) — swap caveman→Ponytail because the output is code, not prose.

- 🥈 **Just one tool? Pick a code-retrieval one** (serena / graphify / CodeGraph) — it alone gets you ~66% and is the only lever that moves the dominant (code-reading) cost.

- **Choosing among the three code-read tools:** graphify for *navigation* (impact, call paths, 'who calls X'); serena for *broad reading + editing* (it also does semantic edits/renames the graph tools can't); CodeGraph for a *batteries-included single binary* that returns source inline (fewer follow-up reads). They're read-mostly; graphify/CodeGraph need a rebuild on code change, serena needs a language server.

**What to avoid:**

- ❌ **Don't run more than one code-read tool** (serena / graphify / CodeGraph) — they reduce the same component, so you pay N integrations for one benefit. Pick one.

- ❌ **Don't reach for rtk to fix comprehension cost** — it's ~0% there. Add it *for* command-heavy loops (tests, builds, git, greps).

- ❌ **Don't expect caveman to shrink code, or Ponytail to shrink prose** — each is ~0% (or worse) outside its output lane.

- ❌ **Don't expect either output tool to move an input-heavy bill** — when you're reading lots of code, output is a small share; the code-read tool is what matters.

## Appendix: real before/after artifacts

**A1 — "list TaskService's methods."** Baseline reads the whole file (458 tokens). serena returns:

```json
{"Class": [{"TaskService": {"Method": ["__init__", "create_task", "assign_task", "complete_task", "open_tasks"]}}]}
```

That's ~55 tokens — same answer, **−71%**.

**A2 — "who calls notify?"** Baseline reads the file (525 tokens). CodeGraph returns just the call sites (~49 tokens, **−78%**):

```
Callers of "notify" (3):
  method create_task   services/task_service.py:21
  method assign_task   services/task_service.py:34
  method complete_task services/task_service.py:41
```

**A3 — "trace create-task to the DB write."** Baseline reads 5 files across 4 layers (1,633 tokens). graphify returns a path (~65 tokens, **−89%**):

```
Shortest path (3 hops):
  .create_task() <--method-- TaskService <--calls-- build_services() --references--> Database
```

**D1 — "add a due_date field."** Ponytail rewrites the verbose implementation, deleting the unrequested `is_overdue` property and `overdue_tasks`/`list_overdue` helpers:

> _before:_ model property + service helper + repo helper + defensive parsing + 3-assert test (684 tokens)

> _after:_ field + passthrough + 2-assert test (400 tokens, **-41.5%** — illustrative; see the code-generation caveat)

## Reproduce it yourself

```bash
# 1. Harness deps
uv venv .venv && uv pip install --python .venv/bin/python tiktoken pytest

# 2. Install the tools
uv tool install graphifyy
uv tool install --python 3.13 serena-agent
npm i -g @colbymchenry/codegraph
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash
#   Ponytail is a behavioural plugin; its rule text is vendored at
#   benchmark/fixtures/ponytail/rules.md (from DietrichGebert/ponytail).

# 3. Run + report
PATH="$HOME/.local/bin:$PATH" .venv/bin/python -m benchmark.run_benchmark
.venv/bin/python -m benchmark.make_report
```

Results are written to `results/results.json` and `results/results.csv`; this report is regenerated from them. caveman/Ponytail outputs reuse committed fixtures unless you pass `--regenerate-caveman` / `--regenerate-ponytail` (requires the `claude` CLI).

## Limitations (read before believing the numbers)

- **Modeled, not metered.** Token usage is computed from the *real artifacts each tool produces*, not metered from a live LLM session. Real agents add reasoning, retries, and non-determinism; exact totals will differ, but the relative picture is what we claim.

- **Ponytail is doubly modeled, and its % is authoring-dependent.** It has no headless CLI, so we apply its real rules to a fixed verbose baseline via the `claude` CLI and compare two non-equivalent solutions. Worse, *we* wrote the baseline's scope creep and *we* framed the rule prompt — and those choices set the magnitude: a "preserve behaviour" prompt gave −1.6%, a "deliver only what was requested" prompt gave −41.5%. We report the latter as it matches Ponytail's intended use, but treat it as directional illustration, not a measurement on par with the deterministic tools.

- **One small, clean codebase.** ~30 files, all tests green. This **understates rtk** (short command output) and **understates caveman** (concise answers). Bigger/noisier repos would widen their wins.

- **CodeGraph's `explore` returns source by design.** That inflates its single-call cost on broad-comprehension tasks but saves follow-up reads our one-retrieval-per-task rule doesn't count — so its aggregate here is a conservative read of its real-session value.

- **One tokenizer; reference answers are ours.** Absolute counts vary by tokenizer (ratios are stable); every input-side scenario shares one canonical answer so the input comparison is apples-to-apples.

- **One retrieval per task; single run.** We count one tool call (or file-read set) per task. Deterministic for the input tools; caveman/Ponytail outputs are fixed via committed fixtures.

