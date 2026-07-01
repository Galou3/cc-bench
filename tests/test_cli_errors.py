from ccbench.cli import main


def test_report_on_missing_dir_returns_clean_error(capsys):
    rc = main(["report", "does_not_exist_dir"])
    assert rc == 2
    assert "error:" in capsys.readouterr().err


def test_run_with_bad_conditions_path_returns_error(tmp_path):
    rc = main(["run", "--suite", str(tmp_path), "--conditions", str(tmp_path / "nope")])
    assert rc == 2


def test_validate_missing_suite_returns_clean_error(capsys):
    rc = main(["validate", "--suite", "does_not_exist_dir"])
    assert rc == 2
    assert "error:" in capsys.readouterr().err
