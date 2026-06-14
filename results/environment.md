# Benchmark Environment

Captured: 2026-06-14

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
| **caveman** | `curl install.sh \| bash` | ✅ PASS | latest | Installs skill dirs + a real Python compressor `caveman-compress`. **Mechanism is an LLM** (`call_claude`): uses `ANTHROPIC_API_KEY` if set, else the `claude` CLI (present, v2.1.177, verified working headlessly). Compression ruleset documented in `caveman/SKILL.md` (levels: lite/full/ultra/wenyan*). |

**All four tools installed and run for real — no tool was modeled-from-spec.**

## Key methodological consequence

caveman is the only tool whose compression is produced by an LLM rather than a
deterministic transform. We run the **real** caveman compressor (via the `claude` CLI),
then commit its outputs as fixtures so the token *measurement* remains fully reproducible
without re-invoking the model. In normal interactive use caveman adds no extra call — it
simply makes the agent reply tersely; our fixtures stand in for those terse replies.
