import os
import re
import pytest

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def get_module_folders():
    folders = [
        d for d in sorted(os.listdir(REPO_ROOT))
        if os.path.isdir(os.path.join(REPO_ROOT, d)) and re.match(r'^\d{2}-', d)
    ]
    return folders

@pytest.fixture(scope="session")
def repo_root():
    return REPO_ROOT

@pytest.fixture(scope="session")
def module_folders():
    return get_module_folders()
