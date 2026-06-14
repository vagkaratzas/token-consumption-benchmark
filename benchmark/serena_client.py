"""Minimal stdio MCP client that drives serena's semantic tools headlessly.

serena runs as an MCP server. A real coding agent connects to it over stdio and
calls tools like ``get_symbols_overview`` / ``find_symbol`` /
``find_referencing_symbols`` instead of reading whole files. We do exactly that
here: start the server once against the ``taskflow`` project, call the tools the
benchmark tasks specify, and capture the textual results.
"""

from __future__ import annotations

import json
import os
import subprocess
import threading
import time
from pathlib import Path
from typing import Optional

REPO = Path(__file__).resolve().parent.parent
PROJECT = REPO / "taskflow"


class SerenaClient:
    """Start serena's MCP server and call tools over newline-delimited JSON-RPC."""

    def __init__(self, project: Path = PROJECT) -> None:
        self.project = project
        self.proc: Optional[subprocess.Popen] = None
        self._id = 0

    def start(self, timeout: float = 240.0) -> None:
        env = dict(os.environ)
        env["PATH"] = f"{Path.home()}/.local/bin:" + env.get("PATH", "")
        cmd = [
            "serena", "start-mcp-server",
            "--project", str(self.project),
            "--transport", "stdio",
            "--context", "ide-assistant",
            "--enable-web-dashboard", "False",
            "--enable-gui-log-window", "False",
            "--log-level", "ERROR",
        ]
        self.proc = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
            env=env,
        )
        threading.Thread(target=self._drain_stderr, daemon=True).start()

        rid = self._send("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "token-benchmark", "version": "0"},
        })
        self._read_until(rid, timeout)
        self._send("notifications/initialized", {}, notify=True)

    def _drain_stderr(self) -> None:
        assert self.proc and self.proc.stderr
        for _ in self.proc.stderr:
            pass

    def _send(self, method: str, params=None, notify: bool = False) -> Optional[int]:
        assert self.proc and self.proc.stdin
        msg = {"jsonrpc": "2.0", "method": method}
        if params is not None:
            msg["params"] = params
        rid = None
        if not notify:
            self._id += 1
            rid = self._id
            msg["id"] = rid
        self.proc.stdin.write(json.dumps(msg) + "\n")
        self.proc.stdin.flush()
        return rid

    def _read_until(self, want_id: int, timeout: float = 180.0) -> dict:
        assert self.proc and self.proc.stdout
        deadline = time.time() + timeout
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                time.sleep(0.02)
                continue
            line = line.strip()
            if not line or not line.startswith("{"):
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("id") == want_id:
                return obj
        raise TimeoutError(f"serena: no response to id={want_id}")

    def call(self, tool: str, args: dict, timeout: float = 180.0) -> str:
        """Call an MCP tool and return its concatenated text content."""
        rid = self._send("tools/call", {"name": tool, "arguments": args})
        resp = self._read_until(rid, timeout)
        if "error" in resp:
            raise RuntimeError(f"serena tool {tool} error: {resp['error']}")
        parts = resp["result"].get("content", [])
        return "\n".join(p.get("text", "") for p in parts)

    def stop(self) -> None:
        if not self.proc:
            return
        try:
            self._send("shutdown", {}, notify=True)
        except Exception:
            pass
        self.proc.terminate()
        try:
            self.proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proc.kill()
        self.proc = None

    def __enter__(self) -> "SerenaClient":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.stop()
