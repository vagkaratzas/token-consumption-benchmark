---
name: token-saviour
description: >
  Pick the most token-efficient tool for a coding task instead of reflexively reading whole
  files, dumping raw command output into context, or writing more code than asked. Use this
  skill BEFORE you explore or explain a codebase, locate a symbol/definition/callers, trace a
  call path, map an architecture, plan or implement a feature across layers, or run verbose
  commands (tests, builds, git, grep, directory listings) — and whenever context/token budget,
  cost, or "make this use fewer tokens" comes up. It routes the scenario to serena, graphify,
  CodeGraph, rtk, caveman, Ponytail, or plain tools, with concrete commands and the
  combinations to use vs. avoid. Reach for it even when the user doesn't name a tool: if you're
  about to `cat`/Read several files, or about to generate a big implementation, that's the trigger.
---

# token-saviour: spend tokens where they matter

Reading whole files to answer a narrow question is the single most wasteful thing an agent
does. On a benchmark over a ~30-file Python app, swapping whole-file reads for **semantic
retrieval cut total tokens ~66%**; the other tools each own a narrower slice. This skill
helps you reach for the right one *before* you blow the context budget — then get back to the
actual task.

The mental model: token cost has **four independent layers**, and a different tool owns each.
Match the tool to the layer the task actually stresses.

| Layer | What it is | Tool | Don't bother with |
|------|------------|------|-------------------|
| Code-read **input** | Understanding code: symbols, callers, call paths, architecture | **serena** *or* **graphify** *or* **CodeGraph** (pick one) | rtk, caveman, Ponytail |
| Command-output **input** | Verbose stdout: tests, builds, git, grep, listings | **rtk** | the code-read tools |
| Generated **prose output** | Your own long, chatty replies / write-ups | **caveman** | the input tools, Ponytail |
| Generated **code output** | Implementations you write/edit | **Ponytail** | the input tools, caveman |
| — | Tiny/one-off work | plain Read/Grep/Bash | everything (overhead > benefit) |

> **First, check availability.** These are optional third-party tools. Run the relevant
> `--help`/`--version` once; if a tool isn't installed, see `references/tool_links.md` for
> install + verify commands, or fall back to the next-best option in its row (ultimately plain
> Read/Grep/Bash). Never pretend a tool ran — degrade gracefully.

---

## Decision guide

Work top-down. The moment a row matches, use that tool and stop.

1. **"Where is X / what calls X / how does A reach B / what breaks if I change X / explain this
   module / list its methods?"** → a **code-read tool** (serena / graphify / CodeGraph). This is
   the dominant cost — code-reading was ~88% of the baseline bill — so this is the highest-value
   switch. They overlap; see the next section to pick one. Measured: tracing a 4-layer call path
   cost **65 tokens vs 1,633** reading the files (−89%); explaining the whole architecture **243
   vs 3,250** (−85%); listing one class's methods **55 vs 458** (−71%); finding all callers **49
   vs 525** (−78%).

2. **Running something noisy — test suite, build, linter, `git`, `grep`, a big directory
   listing** → **rtk** (compresses command output). Measured: the test run **−65%**, the
   structure listing **−38%**. Its win scales with verbosity, so it's biggest on failing test
   dumps and long build logs (this clean repo is a lower bound).

3. **About to write a long, prose-heavy answer** (explanations, write-ups, status) → consider
   **caveman** (terse "caveman" reply style). It trims filler/hedging/pleasantries. Small on
   already-concise text and it can *grow* terse list/structured output by adding markdown — so
   use it for genuinely chatty output, not for short factual answers or anything where exact
   wording/order matters (warnings, irreversible steps, ordered procedures).

4. **About to generate or edit a chunk of code** (implement a feature, scaffold, refactor) →
   **Ponytail** (a "lazy senior dev" rules plugin that biases you toward minimal code). It
   applies YAGNI: skip unrequested abstractions/helpers, prefer stdlib + one-liners, delete over
   add. In our benchmark it trimmed a verbose due-date implementation by **~40% (illustrative —
   the size depends on how much scope the baseline over-built)** by dropping helpers and a derived
   property nobody asked for. It does ~nothing on prose — it's the mirror image of caveman.

5. **None of the above / a one-file, one-line lookup** → just use plain Read/Grep/Bash. The
   tools have setup and call overhead; on tiny tasks that overhead can cost *more* than it
   saves. Don't tool-ify trivial work.

---

## The three code-read tools overlap — pick ONE

serena, graphify, and CodeGraph all cut the *same* layer (code-read input), so installing more
than one is mostly redundant. They split the wins by *how* the agent mostly works:

- **graphify** — *navigation-heavy*: "who calls this", call paths, impact/blast radius,
  cross-module structure. Best measured on call-path tracing (A3 −89%). Read-only; one-time
  graph build, rebuild after code changes.
- **serena** — *comprehension- and edit-heavy*: broad multi-file understanding **plus semantic
  edits/renames** (the graph tools can't edit). Best on listing a class's members (−71%) and
  whole-architecture explanation (−85%). Needs a language server; indexes once at session start.
- **CodeGraph** — *batteries-included single binary* (npm install, local SQLite, no API key).
  Best on pinpoint caller lookups (`callers`, −78%). Its `explore` returns **verbatim source
  inline** so you don't re-read — heavier per call on broad questions (architecture −45% vs
  serena's −85%) but it saves the follow-up reads. Rebuild the index after code changes.

Rule of thumb: **graphify** for navigation, **serena** for broad reading + editing, **CodeGraph**
for a zero-config single binary. If you can only have one tool at all, make it a code-read one —
it's the only lever that moves the dominant (code-reading) cost.

---

## Best combinations, and what to avoid

The four layers are independent, so combining one-per-layer is additive:

- 🥇 **Comprehension / navigation work:** *(serena **or** graphify **or** CodeGraph)* + **rtk** +
  **caveman**. Each owns a distinct slice; rtk and caveman cost ~nothing to add. Measured
  combined: **−70%**.
- 🥇 **Code-generation work:** *(a code-read tool)* + **Ponytail** — swap caveman→Ponytail because
  the output is code, not prose. On the codegen task ≈ **−60%** (the code-read half measured, the
  Ponytail half illustrative).
- ❌ **Don't run two code-read tools** (serena / graphify / CodeGraph) together — two integrations,
  one benefit. Pick one.
- ❌ **Don't reach for rtk to fix comprehension cost** — it's ~0% there. Use it *for*
  command-heavy loops.
- ❌ **Don't mix up the two output tools** — caveman shrinks prose (~0% or worse on code);
  Ponytail shrinks code (~0% on prose). Route by whether the output is prose or code.
- ❌ **Don't expect any output tool to move an input-heavy bill** — when you're reading lots of
  code, output is a small share; the code-read tool is what matters.

---

## Tool quick-reference (commands)

Use these in place of the reflexive `Read`/`Grep`/`Bash`/"write it all out" equivalents.
Install/verify details for any missing tool: `references/tool_links.md`.

### serena (MCP server, LSP) — instead of reading files to understand/edit code
Connect to the serena MCP server for the project, then call tools rather than reading files:
- `get_symbols_overview(relative_path)` — top-level symbols in a file (add `depth: 1` for methods).
- `find_symbol(name_path_pattern, relative_path, include_body=true)` — a symbol's body.
- `find_referencing_symbols(name_path, relative_path)` — every caller, with context.
- Edits too: `replace_symbol_body`, `insert_after_symbol`, `rename_symbol`.

### graphify (CLI + code graph) — instead of grepping/reading to navigate
```bash
graphify update <dir> --no-cluster        # build the graph once (tree-sitter, no LLM/API key)
graphify explain "ClassName"              # a node + its methods + neighbors
graphify query   "who calls notify?"      # BFS over the graph for a question (--budget N)
graphify path    "create_task" "Database" # shortest path between two symbols
graphify affected "ClassName"             # reverse traversal: impact of a change
```
Graph lives at `<dir>/graphify-out/graph.json`; rebuild with `graphify update` after edits.

### CodeGraph (CLI + SQLite index) — single-binary code-read tool
```bash
CODEGRAPH_TELEMETRY=0 codegraph init <dir>       # build the index once (no API key)
codegraph node    <Symbol> -p <dir>              # one symbol: members/signature + caller trail
codegraph callers <symbol> -p <dir>              # just the call sites (leanest navigation)
codegraph impact  <symbol> -p <dir>              # what's affected by changing it
codegraph explore "<question>" -p <dir>          # one-shot: symbols + source inline (heavier)
```
Index lives at `<dir>/.codegraph/`; re-run `codegraph init` (or `sync`) after edits.
Skip `codegraph install` unless you want it to auto-wire MCP into your agent configs.

### rtk (Rust CLI proxy) — instead of raw verbose commands
```bash
rtk test  <test cmd>     # e.g. rtk test pytest      → only failures + summary
rtk read  <files...>     # cat with filtering
rtk grep  <pattern> <p>  # compact grep (groups, truncates); -t py to scope by type
rtk find  <find args>    # compact file listing
rtk ls / rtk tree / rtk git / rtk diff / rtk log ...
```

### caveman — instead of a long, chatty prose reply
Activate terse mode (say "caveman mode" / `/caveman`, levels `lite|full|ultra`) when you're
about to emit a verbose explanation. Keep code blocks, commands, API names, error strings, and
ordered/irreversible steps **verbatim** — caveman compresses prose, not substance.

### Ponytail — instead of writing more code than the task needs
Enable the plugin (`/ponytail lite|full|ultra`) before generating an implementation. Its rules:
don't build what wasn't requested (YAGNI), prefer stdlib/native + one-liners, no speculative
abstractions/helpers, delete over add, leave one runnable check. It stays out of your way on
input validation at real trust boundaries, error handling, and security.

---

## Why this works (so you can adapt it)

Input dominates the bill when an agent works in a codebase (it was ~88% in the benchmark), and
most of that input is *over-reading* — pulling entire files to answer something a symbol lookup
or a graph query answers in a fraction of the tokens. Semantic retrieval wins because it
returns *just the relevant structure*. rtk, caveman, and Ponytail look small in aggregate only
because they target narrow slices — but they're cheap, so stack them. The one trap is treating
these as interchangeable: each is excellent in its lane and ~useless outside it (the three
code-read tools are interchangeable *with each other* but not with rtk/caveman/Ponytail). When
in doubt, ask "which layer is this task spending tokens on — reading code, reading command
output, writing prose, or writing code?" and pick that row.
