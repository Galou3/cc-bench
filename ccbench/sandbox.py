"""Optionally run the grading command inside an isolated Docker container."""

from __future__ import annotations

from pathlib import Path

DEFAULT_IMAGE = "python:3.12-slim"


def wrap_command(cmd, workspace, *, mode="none", image=DEFAULT_IMAGE, network="none"):
    """Wrap a command to run in a sandbox. ``mode='none'`` returns it unchanged.

    ``mode='docker'`` runs it in an ephemeral, auto-removed container with the
    workspace mounted at /work and network disabled by default, so grading (which
    executes arbitrary agent-produced code) cannot touch the host or the network.
    """
    cmd = list(cmd)
    if mode == "none":
        return cmd
    if mode == "docker":
        ws = str(Path(workspace).resolve())
        return ["docker", "run", "--rm", f"--network={network}",
                "-v", f"{ws}:/work", "-w", "/work", image, *cmd]
    raise ValueError(f"unknown sandbox mode: {mode!r} (use 'none' or 'docker')")


__all__ = ["wrap_command", "DEFAULT_IMAGE"]
