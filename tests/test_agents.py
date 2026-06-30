import json

import pytest

from ccbench.agents import available_agents, make_agent, parse_claude_json
from ccbench.agents.base import RunContext
from ccbench.models import Condition, Task


def _ctx(prob, rep, tmp_path):
    task = Task(id="t", prompt="p", template_dir=str(tmp_path), verify_cmd=["x"])
    cond = Condition(name="c", metadata={"mock_success_prob": prob})
    return RunContext(task=task, condition=cond, workspace=tmp_path, rep=rep, seed=0)


def test_mock_is_deterministic(tmp_path):
    m = make_agent("mock")
    a = m.run(_ctx(0.5, 3, tmp_path)).detail
    b = m.run(_ctx(0.5, 3, tmp_path)).detail
    assert a == b


def test_mock_extremes(tmp_path):
    m = make_agent("mock")
    # p=1 always "solves", p=0 never does; detail encodes the decision
    assert "solve" in m.run(_ctx(1.0, 0, tmp_path)).detail
    assert "no-op" in m.run(_ctx(0.0, 0, tmp_path)).detail


def test_unknown_agent_raises():
    with pytest.raises(ValueError):
        make_agent("nope")
    assert "mock" in available_agents() and "claude" in available_agents()


def test_parse_claude_json_object():
    text = json.dumps({"is_error": False, "result": "done", "num_turns": 3,
                       "total_cost_usd": 0.02, "usage": {"input_tokens": 100, "output_tokens": 40}})
    usage, result, is_err = parse_claude_json(text)
    assert usage.input_tokens == 100 and usage.output_tokens == 40
    assert usage.cost_usd == 0.02 and usage.num_turns == 3 and not is_err and result == "done"


def test_parse_claude_json_list_takes_last():
    text = json.dumps([{"type": "system"}, {"result": "ok", "usage": {"input_tokens": 7}}])
    usage, result, _ = parse_claude_json(text)
    assert usage.input_tokens == 7 and result == "ok"


def test_parse_claude_json_garbage_degrades():
    usage, _, is_err = parse_claude_json("not json")
    assert is_err and usage.input_tokens == 0
