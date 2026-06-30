import textwrap
from pathlib import Path

import pytest

from ccbench.suite import SuiteError, load_conditions, load_suite

SAMPLE = Path(__file__).resolve().parents[1] / "suites" / "sample"


def test_load_sample_suite():
    name, tasks = load_suite(SAMPLE)
    assert name == "sample"
    assert {t.id for t in tasks} == {"fizzbuzz", "parse_version", "dedup_stable"}
    # paths resolved to absolute, existing directories
    for t in tasks:
        assert Path(t.template_dir).is_dir()
        assert Path(t.reference_dir).is_dir()


def test_missing_manifest(tmp_path):
    with pytest.raises(SuiteError):
        load_suite(tmp_path)


def test_duplicate_task_id(tmp_path):
    (tmp_path / "tpl").mkdir()
    (tmp_path / "tasks.yaml").write_text(textwrap.dedent("""
        name: dup
        tasks:
          - {id: a, prompt: p, template_dir: tpl, verify_cmd: [pytest]}
          - {id: a, prompt: p, template_dir: tpl, verify_cmd: [pytest]}
    """), encoding="utf-8")
    with pytest.raises(SuiteError):
        load_suite(tmp_path)


def test_missing_template_dir(tmp_path):
    (tmp_path / "tasks.yaml").write_text(textwrap.dedent("""
        name: bad
        tasks:
          - {id: a, prompt: p, template_dir: nope, verify_cmd: [pytest]}
    """), encoding="utf-8")
    with pytest.raises(SuiteError):
        load_suite(tmp_path)


def test_load_conditions_from_dir():
    conds = load_conditions(Path(__file__).resolve().parents[1] / "conditions")
    names = {c.name for c in conds}
    assert {"baseline", "with-claude-md", "bloated-context"} <= names


def test_load_conditions_duplicate(tmp_path):
    (tmp_path / "a.yaml").write_text("name: same\n", encoding="utf-8")
    (tmp_path / "b.yaml").write_text("name: same\n", encoding="utf-8")
    with pytest.raises(SuiteError):
        load_conditions(tmp_path)
