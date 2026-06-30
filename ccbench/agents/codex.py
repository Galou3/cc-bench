"""Experimental adapter for the OpenAI Codex CLI (enables claude-vs-codex).

Parsing isolated in parse_codex_output (pure, tested); flags/format vary by
version, and the live path is CI-excluded.
"""

from __future__ import annotations

import json
import subprocess

from ..models import Usage
from .base import AgentRunInfo, RunContext


def parse_codex_output(text: str) -> tuple[Usage, str]:
    """Best-effort extraction of token usage from Codex output.

    Scans lines for a JSON object carrying usage/token fields (Codex emits JSONL
    in some modes). Falls back to zero usage and the last non-empty line as a
    note. Never raises: a weird envelope must not abort a benchmark sweep.
    """
    text = (text or "").strip()
    if not text:
        return Usage(), ""
    usage = Usage()
    note = ""
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        note = line
        if not (line.startswith("{") and line.endswith("}")):
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        block = obj.get("usage") or obj
        it = block.get("input_tokens", block.get("prompt_tokens", 0)) or 0
        ot = block.get("output_tokens", block.get("completion_tokens", 0)) or 0
        cost = obj.get("total_cost_usd", obj.get("cost_usd", 0.0)) or 0.0
        if it or ot or cost:
            usage = Usage(int(it), int(ot), float(cost), usage.num_turns + 1)
        msg = obj.get("result") or obj.get("text") or obj.get("message")
        if isinstance(msg, str) and msg:
            note = msg
    return usage, note


class CodexAgent:
    name = "codex"

    def __init__(
        self,
        codex_bin: str = "codex",
        subcommand: str = "exec",
        extra_args: tuple[str, ...] = (),
        model: str | None = None,
    ) -> None:
        self.codex_bin = codex_bin
        self.subcommand = subcommand
        self.extra_args = tuple(extra_args)
        self.model = model

    def _build_cmd(self, ctx: RunContext) -> list[str]:
        cmd = [self.codex_bin, self.subcommand]
        if self.model:
            cmd += ["--model", self.model]
        cmd += list(self.extra_args)
        cmd += list(ctx.condition.agent_args)
        cmd.append(ctx.task.prompt)
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
            return AgentRunInfo(usage=Usage(), detail="codex timed out")
        except (FileNotFoundError, OSError) as exc:
            return AgentRunInfo(usage=Usage(), detail=f"codex not runnable: {exc}")
        usage, note = parse_codex_output(proc.stdout or proc.stderr)
        return AgentRunInfo(usage=usage, detail=note[:200])


__all__ = ["CodexAgent", "parse_codex_output"]
