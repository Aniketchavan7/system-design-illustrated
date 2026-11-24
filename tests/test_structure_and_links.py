import os
import re
from pathlib import Path
import pytest
from tests.conftest import REPO_ROOT, get_module_folders

MODULE_FOLDERS = get_module_folders()


def curriculum_markdown():
    root = Path(REPO_ROOT)
    paths = list(root.glob("*.md"))
    for folder in [*MODULE_FOLDERS, "advanced", "labs"]:
        paths.extend((root / folder).rglob("*.md"))
    return sorted(paths)

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
        "docs/flashcards.html",
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

    assets_dir = Path(mod_dir) / "assets"
    visuals = [
        p for p in assets_dir.glob("*")
        if p.is_file() and p.suffix.lower() in {".gif", ".svg", ".png", ".jpg", ".webp"}
    ] if assets_dir.is_dir() else []
    assert visuals, f"No visual diagram (.gif/.svg/.png) found in {folder}/assets/"


def test_generated_docs_integrity():
    """Ensure rendered course chapters and guides have zero broken local links, raw mermaid fences, or leaked TeX."""
    docs = Path(REPO_ROOT) / "docs"
    broken = []
    raw_mermaid = []
    raw_tex = []

    for html_file in sorted(docs.rglob("*.html")):
        txt = html_file.read_text(encoding="utf-8")
        if "language-mermaid" in txt:
            raw_mermaid.append(str(html_file.relative_to(docs)))
        no_code = re.sub(r"<(?:script|pre|code)[^>]*>.*?</(?:script|pre|code)>", "", txt, flags=re.DOTALL)
        for m in re.finditer(r"\$([^$\n<]{1,80})\$", no_code):
            inner = m.group(1)
            if any(tok in inner for tok in ("\\", "^", "_", "=", "×", "≈", "→", "<", ">")):
                raw_tex.append(f"{html_file.relative_to(docs)}: ${inner}$")
        for attr in ("href", "src"):
            for m in re.finditer(rf'{attr}="([^"]+)"', txt):
                target = m.group(1)
                if target.startswith(("http://", "https://", "mailto:", "#", "data:")):
                    continue
                path_part = target.split("#")[0].split("?")[0]
                if not path_part or path_part == "./":
                    continue
                resolved = html_file.parent / path_part
                if path_part.endswith("/"):
                    resolved = resolved / "index.html"
                if not os.path.exists(os.path.normpath(resolved)):
                    broken.append(f"{html_file.relative_to(docs)} -> {attr}=\"{target}\"")

    assert not raw_mermaid, f"Unrendered Mermaid code blocks in docs/: {raw_mermaid[:10]}"
    assert not raw_tex, f"Unrendered LaTeX math in docs/: {raw_tex[:10]}"
    assert not broken, f"Broken local links/assets in docs/: {broken[:10]}"

def test_relative_markdown_links():
    """Verify all internal relative markdown links point to existing files."""
    broken_links = []
    
    link_pattern = re.compile(r'\[([^\]]+)\]\(((\./|\.\./)[^)]+)\)')

    for md_path in curriculum_markdown():
        if md_path.name == "TEMPLATE.md":
            continue
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        matches = link_pattern.findall(content)
        for text, link, _ in matches:
            # Strip anchors (#section) and queries (?...)
            clean_link = link.split('#')[0].split('?')[0]
            if not clean_link:
                continue
            target_path = os.path.normpath(os.path.join(os.path.dirname(md_path), clean_link))
            if not os.path.exists(target_path):
                rel_source = os.path.relpath(md_path, REPO_ROOT)
                broken_links.append(f"{rel_source} -> {link} (resolved to {target_path})")

    assert not broken_links, f"Found {len(broken_links)} broken relative markdown links:\n" + "\n".join(broken_links[:10])


def test_markdown_has_no_unexpected_control_characters():
    invalid = re.compile(r"[\x00-\x08\x09\x0b-\x1f]")
    root = Path(REPO_ROOT)
    findings = []
    for path in curriculum_markdown():
        with path.open(encoding="utf-8", newline="") as file:
            lines = file.read().replace("\r\n", "\n").split("\n")
        for line, text in enumerate(lines, 1):
            for match in invalid.finditer(text):
                findings.append(
                    f"{path.relative_to(root)}:{line}:{match.start() + 1} "
                    f"U+{ord(match[0]):04X}"
                )
    assert not findings, "\n".join(findings)
