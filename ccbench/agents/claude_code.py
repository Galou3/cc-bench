"""Adapter that drives the real Claude Code CLI in headless mode.

It invokes ``claude -p "<prompt>" --output-format json`` with the run's workspace
as the working directory, lets Claude Code edit files there, then parses the JSON
envelope for usage/cost. Grading is still done independently by the harness.

The JSON shape has shifted across Claude Code versions, so parsing is defensive
and isolated in ``parse_claude_json`` (a pure function) - that function is what
the unit tests exercise, so we can validate parsing without spending tokens or
needing the CLI installed in CI. The live ``run`` path is intentionally not run
in CI; benchmarking real agents costs money and needs the user's auth.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from ..models import Usage
from .base import AgentRunInfo, RunContext

# Default tools the agent may use to solve a coding task without interactive
# prompts. Conditions can override/extend via Condition.agent_args.
DEFAULT_ALLOWED_TOOLS = "Edit,Write,Read"


def parse_claude_json(text: str) -> tuple[Usage, str, bool]:
    """Parse a ``claude -p --output-format json`` envelope into ``(usage, result, is_error)``.

    Tolerant of missing keys and of either a single result object or a list of
    stream events (we take the last object that looks like a result). Unknown
    shapes degrade to zero usage rather than raising, so one weird envelope can't
    abort a whole benchmark sweep.
    """
    text = (text or "").strip()
    if not text:
        return Usage(), "", True
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        # Some versions emit JSON lines; try the last non-empty line.
        last = text.splitlines()[-1]
        try:
            data = json.loads(last)
        except json.JSONDecodeError:
            return Usage(), "unparseable claude output", True

    if isinstance(data, list):
        results = [d for d in data if isinstance(d, dict)]
        data = results[-1] if results else {}
    if not isinstance(data, dict):
        return Usage(), "", True

    usage_block = data.get("usage") or {}
    usage = Usage(
        input_tokens=int(usage_block.get("input_tokens", 0) or 0),
        output_tokens=int(usage_block.get("output_tokens", 0) or 0),
        cost_usd=float(data.get("total_cost_usd", data.get("cost_usd", 0.0)) or 0.0),
        num_turns=int(data.get("num_turns", 0) or 0),
    )
    result = str(data.get("result", ""))
    is_error = bool(data.get("is_error", False))
    return usage, result, is_error


class ClaudeCodeAgent:
    name = "claude"

    def __init__(
        self,
        claude_bin: str = "claude",
        permission_mode: str = "acceptEdits",
        allowed_tools: str = DEFAULT_ALLOWED_TOOLS,
        model: str | None = None,
    ) -> None:
        self.claude_bin = claude_bin
        self.permission_mode = permission_mode
        self.allowed_tools = allowed_tools
        self.model = model

    def _build_cmd(self, ctx: RunContext) -> list[str]:
        cmd = [
            self.claude_bin,
            "-p",
            ctx.task.prompt,
            "--output-format",
            "json",
            "--permission-mode",
            self.permission_mode,
            "--allowedTools",
            self.allowed_tools,
        ]
        if self.model:
            cmd += ["--model", self.model]
        cmd += list(ctx.condition.agent_args)
        return cmd

    def run(self, ctx: RunContext) -> AgentRunInfo:
        try:
            proc = subprocess.run(
                self._build_cmd(ctx),
                cwd=str(ctx.workspace),
                capture_output=True,
                text=True,
                timeout=ctx.task.timeout_s,
            )
        except subprocess.TimeoutExpired:
            return AgentRunInfo(usage=Usage(), detail="claude timed out")
        except (FileNotFoundError, OSError) as exc:
            return AgentRunInfo(usage=Usage(), detail=f"claude not runnable: {exc}")

        usage, result, is_error = parse_claude_json(proc.stdout)
        note = result[:200] if result else (proc.stderr or "")[-200:]
        prefix = "error: " if is_error else ""
        return AgentRunInfo(usage=usage, detail=f"{prefix}{note}")


__all__ = ["ClaudeCodeAgent", "parse_claude_json", "DEFAULT_ALLOWED_TOOLS"]
