import subprocess
import sys

import pytest

import main


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "main.py", *args],
        capture_output=True,
        text=True,
    )


def test_missing_database_is_reported_without_a_traceback():
    finished = run_cli("--db", "data/nope.db", "how many rows?")
    assert finished.returncode != 0
    assert "database not found: data/nope.db" in finished.stderr
    assert "Traceback" not in finished.stderr


def test_compare_without_a_question_is_rejected():
    finished = run_cli("--compare")
    assert finished.returncode != 0
    assert "--compare needs a question" in finished.stderr


def test_diagram_shows_every_node():
    finished = run_cli("--diagram")
    assert finished.returncode == 0
    for node in ("agent", "tools", "verify"):
        assert node in finished.stdout


def test_legacy_uses_the_same_model_as_the_agent():
    from sql_agent.llm import PROVIDERS

    assert main.PROVIDERS["groq"]["model"] == PROVIDERS["groq"]["model"]


@pytest.mark.parametrize("flag", ["--trace", "--compare", "--diagram", "--db"])
def test_flag_is_documented(flag):
    assert flag in run_cli("--help").stdout
