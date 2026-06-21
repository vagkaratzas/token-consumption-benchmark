"""Produce the real context artifact for each scenario.

Every function returns the *text* that would enter the model's context (or, for
caveman, the text the model would emit). ``run_benchmark`` counts tokens on
these strings. All tools are invoked for real.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import List

REPO = Path(__file__).resolve().parent.parent
GRAPH_PATH = REPO / "taskflow" / "graphify-out" / "graph.json"
CODEGRAPH_DIR = REPO / "taskflow" / ".codegraph"
CAVEMAN_DIR = REPO / ".agents" / "skills" / "caveman-compress"
FIXTURES = REPO / "benchmark" / "fixtures" / "caveman"
PONYTAIL_DIR = REPO / "benchmark" / "fixtures" / "ponytail"

_ANSI = re.compile(r"\x1b\[[0-9;]*[mGKHF]")


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


# -------------------------------------------------------------------- codegraph
def codegraph_build() -> str:
    """Build the codegraph index once (tree-sitter, SQLite, no LLM/API key).

    The ``.codegraph`` dir is removed first so the index is deterministic across
    repeated runs. Telemetry is disabled.
    """
    if CODEGRAPH_DIR.exists():
        shutil.rmtree(CODEGRAPH_DIR)
    return run_cmd("CODEGRAPH_TELEMETRY=0 codegraph init taskflow", timeout=300)


def codegraph_run(argv: List[str]) -> str:
    """Run a codegraph node/callers/explore/impact command; strip ANSI styling."""
    quoted = " ".join(_shell_quote(a) for a in argv)
    out = run_cmd(f"CODEGRAPH_TELEMETRY=0 codegraph {quoted} -p taskflow")
    return _ANSI.sub("", out)


# --------------------------------------------------------------------- ponytail
def _call_claude(prompt: str) -> str:
    """Send a prompt to the headless ``claude --print`` CLI and return stdout."""
    claude_bin = shutil.which("claude") or "claude"
    result = subprocess.run(
        [claude_bin, "--print"], input=prompt, text=True,
        capture_output=True, check=True, encoding="utf-8", errors="replace",
    )
    return result.stdout.strip()


def ponytail_minify(task_id: str, code: str, regenerate: bool = False) -> str:
    """Apply ponytail's real 'lazy senior dev' rules to a verbose implementation.

    ponytail ships no headless CLI — it is a behavioural plugin (a rules prompt
    that biases an agent toward minimal code). We *model* it by feeding its real
    rule text plus a fixed baseline implementation to the ``claude`` CLI and
    asking it to apply that philosophy, then cache the result as a committed
    fixture so the token measurement reproduces without re-invoking a model.
    """
    PONYTAIL_DIR.mkdir(parents=True, exist_ok=True)
    fixture = PONYTAIL_DIR / f"{task_id}.md"
    if fixture.exists() and not regenerate:
        return fixture.read_text(encoding="utf-8")
    rules = (PONYTAIL_DIR / "rules.md").read_text(encoding="utf-8")
    prompt = (
        f"{rules}\n\n---\n\n"
        "The ONLY feature requested is: add a `due_date` field to tasks so it can be set "
        "when creating a task and is returned with the task. Nothing else was asked for.\n\n"
        "Below is a verbose implementation another developer wrote for this request. Apply "
        "the philosophy above and rewrite it as the minimum that delivers ONLY the requested "
        "feature against the same codebase. Per the decision ladder, delete everything that "
        "was not requested: speculative query helpers, derived properties, abstractions, and "
        "defensive checks that aren't at a real trust boundary (YAGNI). Prefer one-liners and "
        "fewest edits. Keep it correct and leave exactly ONE runnable check. Output ONLY the "
        "resulting code (fenced blocks per file), no preamble or commentary.\n\n"
        f"{code}"
    )
    out = _call_claude(prompt).strip()
    fixture.write_text(out, encoding="utf-8")
    return out


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
