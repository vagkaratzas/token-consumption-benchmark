"""Run all task x scenario cells and write results to results/.

Scenarios:
  baseline  - read whole files / run raw commands; full prose answer
  serena    - semantic symbol retrieval replaces file reads; full prose answer
  graphify  - code-graph queries replace file reads; full prose answer
  codegraph - codegraph index queries replace file reads; full prose answer
  rtk       - command output / file reads piped through rtk; full prose answer
  caveman   - baseline input; answer compressed by the real caveman tool
  ponytail  - baseline input; generated code minimised by ponytail's rules
              (only bites on code-generation tasks; otherwise == baseline)
  stacked   - best code/command input + best output (caveman, or ponytail on codegen)

Each tool only changes the component it targets; the rest is held equal to
baseline, isolating each tool's real contribution.
"""

from __future__ import annotations

import argparse
import csv
import json
from datetime import date
from pathlib import Path

from benchmark import tools
from benchmark.serena_client import SerenaClient
from benchmark.tasks import TASKS
from benchmark.tokenizer import count_tokens

REPO = Path(__file__).resolve().parent.parent
RESULTS = REPO / "results"
SCENARIOS = ["baseline", "serena", "graphify", "codegraph", "rtk",
             "caveman", "ponytail", "stacked"]


def gather_serena(client: SerenaClient, calls) -> str:
    parts = []
    for call in calls:
        tool = call["tool"]
        args = call["args"]
        text = client.call(tool, args)
        parts.append(f"## serena {tool}({args})\n{text}")
    return "\n".join(parts)


def gather_graphify(argvs) -> str:
    parts = []
    for argv in argvs:
        parts.append(tools.graphify_run(argv))
    return "\n".join(parts)


def gather_codegraph(argvs) -> str:
    parts = []
    for argv in argvs:
        parts.append(tools.codegraph_run(argv))
    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--regenerate-caveman", action="store_true",
                    help="re-run the caveman compressor instead of using cached fixtures")
    ap.add_argument("--regenerate-ponytail", action="store_true",
                    help="re-run the ponytail minifier instead of using cached fixtures")
    args = ap.parse_args()

    RESULTS.mkdir(exist_ok=True)

    print("[1/4] Building code graphs (tree-sitter, no LLM)...")
    build_log = tools.graphify_build()
    print("    graphify:", build_log.strip().splitlines()[-1] if build_log.strip() else "(no output)")
    graph_bytes = tools.GRAPH_PATH.stat().st_size if tools.GRAPH_PATH.exists() else 0
    cg_log = tools.codegraph_build()
    cg_line = next((l for l in reversed(cg_log.strip().splitlines()) if "nodes" in l), "")
    print("    codegraph:", cg_line.strip() or "(built)")
    codegraph_bytes = sum(p.stat().st_size for p in tools.CODEGRAPH_DIR.rglob("*")
                          if p.is_file()) if tools.CODEGRAPH_DIR.exists() else 0

    print("[2/4] Starting serena MCP server (LSP backend)...")
    serena = SerenaClient()
    serena.start()

    results = []
    try:
        for task in TASKS:
            print(f"[3/4] Task {task.id} ({task.category}): {task.title}")

            base_input_text = tools.read_files(task.baseline_files)
            base_cmd_text = "".join(tools.run_cmd(c) for c in task.baseline_commands)
            baseline_input = count_tokens(base_input_text) + count_tokens(base_cmd_text)
            base_output = count_tokens(task.reference_answer)

            # serena
            if task.serena_calls:
                serena_text = gather_serena(serena, task.serena_calls)
                serena_input = count_tokens(serena_text)
            else:
                serena_input = baseline_input

            # graphify
            if task.graphify_argv:
                graphify_text = gather_graphify(task.graphify_argv)
                graphify_input = count_tokens(graphify_text)
            else:
                graphify_input = baseline_input

            # codegraph
            if task.codegraph_argv:
                codegraph_text = gather_codegraph(task.codegraph_argv)
                codegraph_input = count_tokens(codegraph_text)
            else:
                codegraph_input = baseline_input

            # rtk
            rtk_read_text = tools.rtk_read(task.rtk_read_files)
            rtk_cmd_text = "".join(tools.run_cmd(c) for c in task.rtk_commands)
            if task.rtk_read_files or task.rtk_commands:
                rtk_input = count_tokens(rtk_read_text) + count_tokens(rtk_cmd_text)
            else:
                rtk_input = baseline_input

            # caveman (compresses prose; leaves code blocks ~unchanged)
            cave_answer = tools.caveman_compress(
                task.id, task.reference_answer, regenerate=args.regenerate_caveman)
            cave_output = count_tokens(cave_answer)

            # ponytail (minimises generated code; no-op on non-codegen tasks)
            if task.codegen:
                pony_answer = tools.ponytail_minify(
                    task.id, task.reference_answer, regenerate=args.regenerate_ponytail)
                pony_output = count_tokens(pony_answer)
            else:
                pony_output = base_output

            # stacked = best input (serena for code / rtk for commands) + best output
            # (ponytail on codegen tasks, otherwise caveman)
            stacked_input = serena_input if task.serena_calls else rtk_input
            stacked_output = pony_output if task.codegen else cave_output

            cells = {
                "baseline": (baseline_input, base_output),
                "serena": (serena_input, base_output),
                "graphify": (graphify_input, base_output),
                "codegraph": (codegraph_input, base_output),
                "rtk": (rtk_input, base_output),
                "caveman": (baseline_input, cave_output),
                "ponytail": (baseline_input, pony_output),
                "stacked": (stacked_input, stacked_output),
            }

            baseline_total = baseline_input + base_output
            scen = {}
            for name, (inp, out) in cells.items():
                total = inp + out
                delta = round((total - baseline_total) / baseline_total * 100, 1)
                scen[name] = {
                    "input": inp, "output": out, "total": total, "delta_pct": delta,
                }
                print(f"      {name:9s} in={inp:5d} out={out:4d} total={total:5d} "
                      f"({delta:+.1f}%)")

            results.append({
                "id": task.id,
                "category": task.category,
                "title": task.title,
                "goal": task.goal,
                "reference_answer_tokens": base_output,
                "caveman_answer_tokens": cave_output,
                "ponytail_answer_tokens": pony_output,
                "codegen": task.codegen,
                "scenarios": scen,
            })
    finally:
        serena.stop()

    meta = {
        "date": str(date.today()),
        "tokenizer": "tiktoken o200k_base",
        "scenarios": SCENARIOS,
        "n_tasks": len(TASKS),
        "one_time_costs": {
            "graphify_graph_bytes": graph_bytes,
            "codegraph_index_bytes": codegraph_bytes,
            "graphify_note": "graph.json is built once and not ingested into context; "
                             "only query results enter context.",
            "codegraph_note": "codegraph builds a local SQLite index once; not ingested.",
            "serena_note": "LSP indexing happens once at server start; not a context cost.",
        },
        "tools_run_for_real": ["serena", "graphify", "codegraph", "rtk", "caveman"],
        "tools_modeled": ["ponytail"],
        "ponytail_note": "ponytail ships no headless CLI (behavioural plugin); modelled by "
                         "applying its real rule text to a fixed baseline implementation via "
                         "the claude CLI. Result cached as a committed fixture.",
    }

    print("[4/4] Writing results...")
    (RESULTS / "results.json").write_text(
        json.dumps({"meta": meta, "tasks": results}, indent=2))

    with (RESULTS / "results.csv").open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["task", "category", "scenario",
                    "input_tokens", "output_tokens", "total_tokens", "delta_pct"])
        for t in results:
            for name in SCENARIOS:
                c = t["scenarios"][name]
                w.writerow([t["id"], t["category"], name,
                            c["input"], c["output"], c["total"], c["delta_pct"]])

    print("Wrote results/results.json and results/results.csv")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
