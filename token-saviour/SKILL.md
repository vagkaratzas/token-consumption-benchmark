---
name: token-saviour
description: >
  Pick the most token-efficient tool for a coding task instead of reflexively reading whole
  files or dumping raw command output into context. Use this skill BEFORE you explore or
  explain a codebase, locate a symbol/definition/callers, trace a call path, map an
  architecture, plan a feature across layers, or run verbose commands (tests, builds, git,
  grep, directory listings) — and whenever context/token budget, cost, or "make this use
  fewer tokens" comes up. It routes the scenario to serena, graphify, rtk, caveman, or
  plain tools, with concrete commands and the combinations to use vs. avoid. Reach for it
  even when the user doesn't name a tool: if you're about to `cat`/Read several files to
  answer a question, that's the trigger.
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
| Code-read **input** | Understanding code: symbols, callers, call paths, architecture | **serena** or **graphify** | rtk, caveman |
| Command-output **input** | Verbose stdout: tests, builds, git, grep, listings | **rtk** | serena, graphify |
| Generated **output** | Your own long, chatty replies | **caveman** | the input tools |
| — | Tiny/one-off work | plain Read/Grep/Bash | everything (overhead > benefit) |

> **First, check availability.** These are optional third-party tools. Run the relevant
> `--help`/`--version` once; if a tool isn't installed, fall back to the next-best option in
> its row (ultimately plain Read/Grep/Bash). Never pretend a tool ran — degrade gracefully.

---

## Decision guide

Work top-down. The moment a row matches, use that tool and stop.

1. **"Where is X / what calls X / how does A reach B / what breaks if I change X?"**
   → **graphify** (a queryable code graph). It shines at *navigation and impact*: callers,
   call-path tracing, cross-module flow. Measured: tracing a 4-layer call path cost **65
   tokens vs 1,633** reading the files (−89%).

2. **"Explain this module/class, list its methods, summarize the architecture"** — or you're
   about to **edit** code by symbol → **serena** (live LSP symbols + semantic edits). It
   shines at *broad comprehension and editing*: symbol overviews across many files, and
   refactors/renames that graphify can't do. Measured: explaining the whole architecture cost
   **243 tokens vs 3,250** (−85%); one class's methods, **55 vs 458** (−71%).

3. **Running something noisy — test suite, build, linter, `git`, `grep`, a big directory
   listing** → **rtk** (compresses command output). Measured: the test run **−65%**, the
   structure listing **−38%**. Its win scales with verbosity, so it's biggest on failing test
   dumps and long build logs.

4. **About to write a long, prose-heavy answer** (explanations, write-ups, status) → consider
   **caveman** (terse "caveman" reply style). It trims filler/hedging/pleasantries. Small on
   already-concise text and it can *grow* terse list/structured output by adding markdown — so
   use it for genuinely chatty output, not for short factual answers or anything where exact
   wording/order matters (warnings, irreversible steps, ordered procedures).

5. **None of the above / a one-file, one-line lookup** → just use plain Read/Grep/Bash. The
   tools have setup and call overhead; on tiny tasks that overhead can cost *more* than it
   saves. Don't tool-ify trivial work.

---

## serena vs graphify — they overlap, so pick ONE

Both cut the same layer (code-read input), so installing both is mostly redundant — choose by
how the agent mostly works:

- **graphify** if the work is *navigation-heavy*: "who calls this", call paths, impact/blast
  radius, cross-repo structure. Read-only; needs a one-time graph build and a rebuild after
  code changes.
- **serena** if the work is *comprehension- and edit-heavy*: broad multi-file understanding
  plus semantic edits/renames (graphify can't edit). Needs a language server; indexes once at
  session start.

If you can only have one tool at all, make it the code-retrieval one (serena or graphify) —
it's the only lever that moves the dominant (code-reading) cost.

---

## Best combination, and what to avoid

The layers are independent, so combining one-per-layer is additive:

- 🥇 **Recommended stack:** *(serena **or** graphify)* + **rtk** + **caveman**. Each owns a
  distinct slice; rtk and caveman cost ~nothing to add. Measured combined: **−70%**.
- ❌ **Don't run serena *and* graphify together** — two integrations, one benefit. Pick one.
- ❌ **Don't reach for rtk to fix comprehension cost** — it's ~0% there. Use it *for*
  command-heavy loops.
- ❌ **Don't expect caveman to move the bill on input-heavy codebase work** — it only shrinks
  *your* output, which is a small share when you're reading lots of code.

---

## Tool quick-reference (commands)

Use these in place of the reflexive `Read`/`Grep`/`Bash` equivalents.

### serena (MCP server, LSP) — instead of reading files to understand code
Connect to the serena MCP server for the project, then call tools rather than reading files:
- `get_symbols_overview(relative_path)` — top-level symbols in a file (add `depth: 1` for methods).
- `find_symbol(name_path_pattern, relative_path, include_body=true)` — a symbol's body.
- `find_referencing_symbols(name_path, relative_path)` — every caller, with context.
- It also edits: `replace_symbol_body`, `insert_after_symbol`, `rename_symbol`.

Headless (no MCP client): `serena start-mcp-server --project <dir> --transport stdio` and
speak newline-delimited JSON-RPC (see `benchmark/serena_client.py` in this repo for a minimal client).

### graphify (CLI + code graph) — instead of grepping/reading to navigate
```bash
graphify update <dir> --no-cluster        # build the graph once (tree-sitter, no LLM/API key)
graphify explain "ClassName"              # a node + its methods + neighbors
graphify query   "who calls notify?"      # BFS over the graph for a question (--budget N)
graphify path    "create_task" "Database" # shortest path between two symbols
graphify affected "ClassName"             # reverse traversal: impact of a change
```
Graph lives at `<dir>/graphify-out/graph.json`; rebuild with `graphify update` after edits.

### rtk (Rust CLI proxy) — instead of raw verbose commands
```bash
rtk test  <test cmd>     # e.g. rtk test pytest      → only failures + summary
rtk read  <files...>     # cat with filtering
rtk grep  <pattern> <p>  # compact grep (groups, truncates); -t py to scope by type
rtk find  <find args>    # compact file listing
rtk ls / rtk tree / rtk git / rtk diff / rtk log ...
```

### caveman — instead of a long, chatty reply
Activate terse mode (say "caveman mode" / `/caveman`, levels `lite|full|ultra`) when you're
about to emit a verbose explanation. Keep code blocks, commands, API names, error strings, and
ordered/irreversible steps **verbatim** — caveman compresses prose, not substance.

---

## Why this works (so you can adapt it)

Input dominates the bill when an agent works in a codebase (it was ~88% in the benchmark), and
most of that input is *over-reading* — pulling entire files to answer something a symbol lookup
or a graph query answers in a fraction of the tokens. Semantic retrieval wins because it
returns *just the relevant structure*. rtk and caveman look small in aggregate only because
they target narrow slices — but they're cheap, so stack them. The one trap is treating these
as interchangeable: each is excellent in its lane and ~useless outside it, so route by scenario
rather than reaching for a favorite. When in doubt, ask "which layer is this task spending
tokens on?" and pick that row.
