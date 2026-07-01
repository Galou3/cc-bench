import pytest

from ccbench.sandbox import wrap_command


def test_none_returns_command_unchanged():
    assert wrap_command(["pytest", "-q"], "/ws", mode="none") == ["pytest", "-q"]


def test_docker_wraps_with_isolation():
    out = wrap_command(["pytest", "-q"], "/ws", mode="docker",
                       image="python:3.12-slim", network="none")
    assert out[0] == "docker" and "run" in out and "--rm" in out
    assert "--network=none" in out
    assert "-w" in out and "/work" in out
    assert out[-2:] == ["pytest", "-q"]          # the real command is appended
    assert "python:3.12-slim" in out


def test_unknown_mode_raises():
    with pytest.raises(ValueError):
        wrap_command(["x"], "/ws", mode="bogus")
