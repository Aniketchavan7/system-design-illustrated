import os
import sys
import subprocess
import pytest
from tests.conftest import REPO_ROOT, get_module_folders

MODULE_FOLDERS = get_module_folders()

def test_module_count():
    """Assert all 45 modules are present."""
    assert len(MODULE_FOLDERS) == 45, f"Expected 45 modules, found {len(MODULE_FOLDERS)}"

@pytest.mark.parametrize("folder", MODULE_FOLDERS)
def test_demo_execution(folder):
    """Execute each module's demo.py in isolation and assert successful termination."""
    demo_path = os.path.join(REPO_ROOT, folder, "demo.py")
    assert os.path.isfile(demo_path), f"demo.py missing in {folder}"

    # Run demo.py as subprocess with working directory set to the module folder
    result = subprocess.run(
        [sys.executable, "demo.py"],
        cwd=os.path.join(REPO_ROOT, folder),
        capture_output=True,
        text=True,
        timeout=15
    )

    assert result.returncode == 0, (
        f"Demo failed in {folder} with return code {result.returncode}!\n"
        f"--- STDOUT ---\n{result.stdout}\n"
        f"--- STDERR ---\n{result.stderr}\n"
    )
