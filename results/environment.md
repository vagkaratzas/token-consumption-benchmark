# Benchmark Environment

Captured: 2026-06-14 · updated 2026-06-21 (added CodeGraph + Ponytail)

## Host toolchain

| Tool | Version |
|------|---------|
| python3 | 3.10.18 |
| uv | 0.11.8 |
| cargo | 1.90.0 |
| node | v22.22.3 |
| git | 2.34.1 |
| claude CLI | 2.1.177 (Claude Code) |
| tiktoken (harness) | 0.13.0 (encoding `o200k_base`) |

## Tool install outcomes

| Tool | Install method | Result | Version | Notes |
|------|----------------|--------|---------|-------|
| **graphify** | `uv tool install graphifyy` | ✅ PASS | v0.8.39 | Executables `graphify`, `graphify-mcp`. Code graph built with `graphify update .` via tree-sitter — **no LLM/API key needed** for code extraction. Queried with `query`/`explain`/`path`/`affected`. |
| **serena** | `uv tool install --python 3.13 serena-agent` | ✅ PASS | 1.5.3 | Executables `serena`, `serena-agent`, `serena-hooks`. Runs as MCP server (LSP backend). Driven headlessly here via a stdio JSON-RPC MCP client calling `get_symbols_overview`, `find_symbol`, `find_referencing_symbols`. No API key needed (LSP is local). |
| **rtk** | `curl install.sh \| sh` (prebuilt musl binary) | ✅ PASS | 0.42.4 | Single Rust binary at `~/.local/bin/rtk`. Token-optimized native-command proxies: `read`, `ls`, `tree`, `grep`, `find`, `test`. No LLM. |
| **CodeGraph** | `npm i -g @colbymchenry/codegraph` | ✅ PASS | 1.0.1 | Single CLI `codegraph`. Index built with `codegraph init` (tree-sitter → local SQLite `.codegraph/`) — **no LLM/API key needed**. Queried with `node`/`callers`/`callees`/`impact`/`explore`. We **skip `codegraph install`** (it auto-wires the MCP server into Claude Code/Cursor/etc. configs — out of scope and would mutate the host agent setup). Telemetry disabled with `CODEGRAPH_TELEMETRY=0`. |
| **caveman** | `curl install.sh \| bash` | ✅ PASS | latest | Installs skill dirs + a real Python compressor `caveman-compress`. **Mechanism is an LLM** (`call_claude`): uses `ANTHROPIC_API_KEY` if set, else the `claude` CLI (present, v2.1.177, verified working headlessly). Compression ruleset documented in `caveman/SKILL.md` (levels: lite/full/ultra/wenyan*). |
| **Ponytail** | plugin marketplace (`DietrichGebert/ponytail`) | ⚠️ MODELED | latest | Ships **no headless CLI** — it is a behavioural plugin: a rules prompt ("lazy senior dev") that biases an agent toward minimal code. There is nothing to execute deterministically. We vendor its **real** rule text (`benchmark/fixtures/ponytail/rules.md`) and model it by applying that text to a fixed verbose implementation via the `claude` CLI; output cached as a fixture. |

**Five tools installed and run for real; Ponytail is modeled (no headless CLI).**

## Key methodological consequence

caveman and Ponytail are the two tools whose effect is produced by an LLM rather than a
deterministic transform. We run the **real** caveman compressor (via the `claude` CLI) and
apply Ponytail's **real** rule text (also via the `claude` CLI), then commit their outputs as
fixtures so the token *measurement* remains fully reproducible without re-invoking the model.
caveman compresses a *fixed* answer (held-equal, like every other cell). Ponytail is a
design-time behaviour that changes *what code gets written*, so its cell compares two
non-equivalent solutions (verbose vs. minimal) — softer than the rest, hence reported in its
own code-generation section and kept out of the headline aggregate.
