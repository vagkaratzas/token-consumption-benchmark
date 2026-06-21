# token-consumption-benchmark

A Claude Code (Opus 4.8 + ultracode) benchmark of tools that promise to cut the token consumption of agentic AI coding:
**[serena](https://github.com/oraios/serena)** vs **[graphify](https://github.com/safishamsi/graphify)**
vs **[CodeGraph](https://github.com/colbymchenry/codegraph)** vs **[rtk](https://github.com/rtk-ai/rtk)**
vs **[caveman](https://github.com/juliusbrussee/caveman)** vs **[Ponytail](https://github.com/DietrichGebert/ponytail)**
vs a no-tool baseline.

👉 **Read the results: [REPORT.md](REPORT.md)**

## TL;DR

Six tools, **four token layers**, one rule: match the tool to the layer the task stresses.
Measured over an 8-task comprehension suite (+1 code-gen task) on a realistic ~30-file Python app,
totals vs the no-tool baseline (5 tools run for real, Ponytail modeled; tokenizer `tiktoken o200k_base`):

| Tool | Layer it targets | Δ tokens vs baseline |
|------|------------------|:--------------------:|
| serena | code-read input (LSP symbols) | **−66.1%** |
| graphify | code-read input (code graph) | **−65.6%** |
| CodeGraph | code-read input (indexed graph) | **−54.1%** |
| rtk | command-output input | −4.6% (but −36% on command tasks) |
| caveman | generated **prose** output | −0.7% (output-only; understated here) |
| Ponytail | generated **code** output | ~0% on comprehension; ~40% on code-gen* |
| **serena + rtk + caveman** (stacked) | three layers at once | **−69.6%** |

The tools target **different layers** and are complementary — except the three code-read tools
(serena / graphify / CodeGraph), which overlap (pick one). They split the wins by question type:
serena on broad comprehension, graphify on call-path tracing, CodeGraph on pinpoint caller lookups.

\* Ponytail has no headless CLI (it's a behavioural plugin), so its figure is *modeled and
illustrative* — see the caveat in [REPORT.md](REPORT.md). For methodology, per-task tables, the
combination recommendations, and limitations, read the full report.

## Repository layout

```
taskflow/            the dummy codebase under test (REST API + CLI, 13 passing tests)
benchmark/           the measurement harness
  tasks.py             8 comprehension tasks + 1 code-gen task (D1) + per-tool specs
  tools.py             real artifact producers (read/rtk/graphify/codegraph/caveman/ponytail)
  serena_client.py     stdio MCP client driving serena
  run_benchmark.py     orchestrator -> results/
  make_report.py       renders REPORT.md from results
  fixtures/caveman/    committed real caveman outputs (reproducible)
  fixtures/ponytail/   vendored Ponytail rule text + committed modeled output
results/             environment.md, results.json, results.csv
token-saviour/       SKILL.md routing agents to the right tool by scenario (+ tool_links.md)
docs/superpowers/    design spec + implementation plan
REPORT.md            the shareable write-up
```

## Reproduce

```bash
uv venv .venv && uv pip install --python .venv/bin/python tiktoken pytest
uv tool install graphifyy
uv tool install --python 3.13 serena-agent
npm i -g @colbymchenry/codegraph
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash
# Ponytail is a behavioural plugin (no CLI); its rule text is vendored at
# benchmark/fixtures/ponytail/rules.md (from DietrichGebert/ponytail).

PATH="$HOME/.local/bin:$PATH" .venv/bin/python -m benchmark.run_benchmark
.venv/bin/python -m benchmark.make_report
```
