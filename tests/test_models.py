from ccbench.models import Condition, Outcome, RunResult, SuiteRun, Task, Usage


def test_task_from_dict_defaults():
    t = Task.from_dict({"id": "a", "prompt": "p", "template_dir": "d", "verify_cmd": ["pytest"]})
    assert t.timeout_s == 300 and t.tags == () and t.reference_dir is None


def test_condition_metadata_roundtrips():
    c = Condition.from_dict({"name": "x", "metadata": {"mock_success_prob": 0.7}})
    assert c.metadata["mock_success_prob"] == 0.7


def test_usage_is_additive():
    total = Usage(1, 2, 0.5, 1) + Usage(3, 4, 0.25, 1)
    assert total == Usage(4, 6, 0.75, 2)


def test_runresult_roundtrip():
    rr = RunResult("t", "c", 2, Outcome.PASS, Usage(10, 5, 0.1, 1), 1.5, "mock", 0, "ok")
    again = RunResult.from_dict(rr.to_dict())
    assert again == rr and again.passed is True


def test_outcome_serialises_as_value():
    assert RunResult("t", "c", 0, Outcome.TIMEOUT, Usage(), 0.0).to_dict()["outcome"] == "timeout"


def test_suiterun_roundtrip_and_filter():
    results = (
        RunResult("t", "a", 0, Outcome.PASS, Usage(), 0.0),
        RunResult("t", "b", 0, Outcome.FAIL, Usage(), 0.0),
    )
    run = SuiteRun("s", "mock", ("a", "b"), results, 0, "2026-01-01T00:00:00+00:00")
    again = SuiteRun.from_dict(run.to_dict())
    assert again == run
    assert [r.condition for r in again.for_condition("a")] == ["a"]
