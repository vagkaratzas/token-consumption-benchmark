# token-consumption-benchmark

Benchmark of tools that promise to cut the token consumption of agentic AI coding:
**[serena](https://github.com/oraios/serena)** vs **[graphify](https://github.com/safishamsi/graphify)**
vs **[rtk](https://github.com/rtk-ai/rtk)** vs **[caveman](https://github.com/juliusbrussee/caveman)**
vs a no-tool baseline.

👉 **Read the results: [REPORT.md](REPORT.md)**

## TL;DR

Measured over an 8-task suite on a realistic ~30-file Python app, totals vs the no-tool baseline
(every tool installed and run for real; tokenizer `tiktoken o200k_base`):

| Tool | Reduces | Δ tokens vs baseline |
|------|---------|:--------------------:|
| serena | code-read input (LSP symbols) | **−66.1%** |
| graphify | code-read input (code graph) | **−65.6%** |
| rtk | command-output input | −4.9% (but −36% on command tasks) |
| caveman | generated output | −0.7% (output-only; understated here) |
| **serena + rtk + caveman** (stacked) | all three layers | **−69.6%** |

The four tools target **different layers** and are complementary — serena/graphify overlap (pick one).
See [REPORT.md](REPORT.md) for methodology, per-task tables, the combination recommendation, and limitations.

## Repository layout

```
taskflow/            the dummy codebase under test (REST API + CLI, 13 passing tests)
benchmark/           the measurement harness
  tasks.py             8-task suite + per-tool invocation specs
  tools.py             real artifact producers (read/rtk/graphify/caveman)
  serena_client.py     stdio MCP client driving serena
  run_benchmark.py     orchestrator -> results/
  make_report.py       renders REPORT.md from results
  fixtures/caveman/    committed real caveman outputs (reproducible)
results/             environment.md, results.json, results.csv
docs/superpowers/    design spec + implementation plan
REPORT.md            the shareable write-up
```

## Reproduce

```bash
uv venv .venv && uv pip install --python .venv/bin/python tiktoken pytest
uv tool install graphifyy
uv tool install --python 3.13 serena-agent
curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | sh
curl -fsSL https://raw.githubusercontent.com/JuliusBrussee/caveman/main/install.sh | bash

PATH="$HOME/.local/bin:$PATH" .venv/bin/python -m benchmark.run_benchmark
.venv/bin/python -m benchmark.make_report
```
