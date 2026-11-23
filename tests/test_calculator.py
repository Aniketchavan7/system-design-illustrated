import os
import sys
import subprocess
import pytest
from tests.conftest import REPO_ROOT

CALC_PATH = os.path.join(REPO_ROOT, "calculate.py")

def test_calculator_exists():
    assert os.path.isfile(CALC_PATH), "calculate.py missing from repository root"

def test_calculator_help():
    result = subprocess.run(
        [sys.executable, CALC_PATH, "--help"],
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode == 0
    assert "Capacity Planning Calculator" in result.stdout

@pytest.mark.parametrize("preset", ["twitter", "youtube", "uber", "chat"])
def test_calculator_presets(preset):
    result = subprocess.run(
        [sys.executable, CALC_PATH, "--preset", preset],
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode == 0
    assert "SYSTEM DESIGN CAPACITY ESTIMATION REPORT" in result.stdout
    assert "Average Write QPS" in result.stdout
    assert "QUERY THROUGHPUT" in result.stdout

def test_calculator_custom_parameters():
    result = subprocess.run(
        [
            sys.executable, CALC_PATH,
            "--dau", "50000000",
            "--writes", "10",
            "--reads", "100",
            "--write-size-kb", "2.0",
            "--read-size-kb", "20.0",
            "--retention-years", "3",
            "--replication", "3",
            "--peak-mult", "2.5"
        ],
        capture_output=True,
        text=True,
        timeout=5
    )
    assert result.returncode == 0
    assert "50,000,000" in result.stdout
    assert "SYSTEM DESIGN CAPACITY ESTIMATION REPORT" in result.stdout
