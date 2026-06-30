"""Agent adapters and a small factory.

Adapters are kept behind ``make_agent`` so the runner and CLI depend on the
``Agent`` protocol, not on concrete classes - adding a new agent (e.g. another
CLI) is one new module plus one line here.
"""

from __future__ import annotations

from typing import Any

from .base import Agent, AgentRunInfo, RunContext
from .claude_code import ClaudeCodeAgent, parse_claude_json
from .mock import MockAgent

_REGISTRY = {
    "mock": MockAgent,
    "claude": ClaudeCodeAgent,
}


def make_agent(name: str, **opts: Any) -> Agent:
    """Construct an agent by name, passing ``opts`` to its constructor.

    Raises ``ValueError`` (listing the known names) on an unknown agent so a
    typo on the CLI fails fast instead of silently doing nothing.
    """
    try:
        cls = _REGISTRY[name]
    except KeyError:
        known = ", ".join(sorted(_REGISTRY))
        raise ValueError(f"unknown agent '{name}'; known agents: {known}") from None
    return cls(**opts)


def available_agents() -> list[str]:
    return sorted(_REGISTRY)


__all__ = [
    "Agent",
    "AgentRunInfo",
    "RunContext",
    "MockAgent",
    "ClaudeCodeAgent",
    "parse_claude_json",
    "make_agent",
    "available_agents",
]
