"""Produce the real context artifact for each scenario.

Every function returns the *text* that would enter the model's context (or, for
caveman, the text the model would emit). ``run_benchmark`` counts tokens on
these strings. All tools are invoked for real.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path
from typing import List

REPO = Path(__file__).resolve().parent.parent
GRAPH_PATH = REPO / "taskflow" / "graphify-out" / "graph.json"
CAVEMAN_DIR = REPO / ".agents" / "skills" / "caveman-compress"
FIXTURES = REPO / "benchmark" / "fixtures" / "caveman"


def _env() -> dict:
    env = dict(os.environ)
    env["PATH"] = f"{Path.home()}/.local/bin:" + env.get("PATH", "")
    return env


# --------------------------------------------------------------------- baseline
def read_files(files: List[str]) -> str:
    """Concatenate full file contents, the way a no-tool agent ingests them."""
    chunks = []
    for rel in files:
        path = REPO / rel
        text = path.read_text(encoding="utf-8", errors="replace")
        chunks.append(f"# {rel}\n{text}")
    return "\n".join(chunks)


def run_cmd(cmd: str, timeout: float = 300.0) -> str:
    """Run a shell command from the repo root; return combined stdout+stderr."""
    proc = subprocess.run(
        cmd, shell=True, cwd=str(REPO), env=_env(),
        capture_output=True, text=True, timeout=timeout,
    )
    return (proc.stdout or "") + (proc.stderr or "")


# -------------------------------------------------------------------------- rtk
def rtk_read(files: List[str]) -> str:
    """Read files through ``rtk read`` (token-optimized proxy for cat)."""
    if not files:
        return ""
    return run_cmd("rtk read " + " ".join(files))


# --------------------------------------------------------------------- graphify
def graphify_build() -> str:
    """Build the code graph once via tree-sitter (no LLM). Returns build log.

    The output dir is removed first so the build is deterministic — ``graphify
    update`` otherwise merges into an existing graph, which makes results drift
    slightly across repeated runs.
    """
    import shutil
    out = REPO / "taskflow" / "graphify-out"
    if out.exists():
        shutil.rmtree(out)
    return run_cmd("graphify update taskflow --no-cluster", timeout=300)


def graphify_run(argv: List[str]) -> str:
    """Run a graphify query/explain/path/affected command against the graph."""
    quoted = " ".join(_shell_quote(a) for a in argv)
    return run_cmd(f"graphify {quoted} --graph {GRAPH_PATH}")


def _shell_quote(arg: str) -> str:
    if arg.startswith("--"):
        return arg
    return "'" + arg.replace("'", "'\\''") + "'"


# --------------------------------------------------------------------- caveman
def _load_caveman():
    """Import caveman's real compression functions (prompt + claude-CLI path)."""
    if str(CAVEMAN_DIR) not in sys.path:
        sys.path.insert(0, str(CAVEMAN_DIR))
    from scripts.compress import build_compress_prompt, call_claude  # type: ignore
    return build_compress_prompt, call_claude


def caveman_compress(task_id: str, text: str, regenerate: bool = False) -> str:
    """Compress text with the real caveman tool, caching the output as a fixture.

    First run invokes caveman (which calls the ``claude`` CLI); the result is
    written to ``benchmark/fixtures/caveman/<task_id>.md`` so later runs — and
    anyone reproducing the benchmark — reuse the committed output deterministically.
    """
    FIXTURES.mkdir(parents=True, exist_ok=True)
    fixture = FIXTURES / f"{task_id}.md"
    if fixture.exists() and not regenerate:
        return fixture.read_text(encoding="utf-8")
    build_compress_prompt, call_claude = _load_caveman()
    out = call_claude(build_compress_prompt(text)).strip()
    fixture.write_text(out, encoding="utf-8")
    return out
