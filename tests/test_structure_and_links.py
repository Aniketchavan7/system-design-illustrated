import os
import re
import pytest
from tests.conftest import REPO_ROOT, get_module_folders

MODULE_FOLDERS = get_module_folders()

def test_master_files_exist():
    required_master_files = [
        "README.md",
        "CHEATSHEET.md",
        "DECISION_FLOWCHARTS.md",
        "calculate.py",
        "index.html",
        "app.css",
        "app.js",
        "cards-data.js",
        "docs/index.html",
        "docs/app.css",
        "docs/app.js",
        "docs/cards-data.js"
    ]
    for mf in required_master_files:
        p = os.path.join(REPO_ROOT, mf)
        assert os.path.isfile(p), f"Required file missing: {mf}"
        assert os.path.getsize(p) > 0, f"File is empty: {mf}"

@pytest.mark.parametrize("folder", MODULE_FOLDERS)
def test_module_directory_contract(folder):
    """Ensure every module has README.md, REAL_WORLD_EXAMPLES.md, and demo.py with required sections."""
    mod_dir = os.path.join(REPO_ROOT, folder)
    
    readme = os.path.join(mod_dir, "README.md")
    assert os.path.isfile(readme), f"README.md missing in {folder}"
    with open(readme, "r", encoding="utf-8") as f:
        readme_txt = f.read()
    
    # Must have 30-second version / ELI5
    assert re.search(r"##\s*.*?(?:30-second|ELI5)", readme_txt, re.IGNORECASE), f"ELI5/30-second section missing in {folder}"
    # Must have analogy
    assert re.search(r"##\s*.*?(?:analogy)", readme_txt, re.IGNORECASE), f"Analogy section missing in {folder}"
    # Must have interview questions
    assert re.search(r"##\s*.*?(?:Interview Questions|Top \d+ Interview|Interview)", readme_txt, re.IGNORECASE), f"Interview section missing in {folder}"

    rwe = os.path.join(mod_dir, "REAL_WORLD_EXAMPLES.md")
    assert os.path.isfile(rwe), f"REAL_WORLD_EXAMPLES.md missing in {folder}"
    with open(rwe, "r", encoding="utf-8") as f:
        rwe_txt = f.read()
    assert "##" in rwe_txt
    assert len(rwe_txt) > 200, f"REAL_WORLD_EXAMPLES.md too short in {folder}"

    demo = os.path.join(mod_dir, "demo.py")
    assert os.path.isfile(demo), f"demo.py missing in {folder}"

def test_relative_markdown_links():
    """Verify all internal relative markdown links point to existing files."""
    broken_links = []
    
    md_files = [
        os.path.join(REPO_ROOT, "README.md"),
        os.path.join(REPO_ROOT, "CHEATSHEET.md"),
        os.path.join(REPO_ROOT, "DECISION_FLOWCHARTS.md")
    ]
    for fld in MODULE_FOLDERS:
        md_files.append(os.path.join(REPO_ROOT, fld, "README.md"))
        md_files.append(os.path.join(REPO_ROOT, fld, "REAL_WORLD_EXAMPLES.md"))

    link_pattern = re.compile(r'\[([^\]]+)\]\(((\./|\.\./)[^)]+)\)')

    for md_path in md_files:
        if not os.path.isfile(md_path):
            continue
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        matches = link_pattern.findall(content)
        for text, link, _ in matches:
            # Strip anchors (#section) and queries (?...)
            clean_link = link.split('#')[0].split('?')[0]
            if not clean_link or clean_link.endswith('/'):
                continue
            target_path = os.path.normpath(os.path.join(os.path.dirname(md_path), clean_link))
            if not os.path.exists(target_path):
                rel_source = os.path.relpath(md_path, REPO_ROOT)
                broken_links.append(f"{rel_source} -> {link} (resolved to {target_path})")

    assert not broken_links, f"Found {len(broken_links)} broken relative markdown links:\n" + "\n".join(broken_links[:10])
