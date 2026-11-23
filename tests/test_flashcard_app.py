import os
import re
import json
import pytest
from tests.conftest import REPO_ROOT

def test_cards_data_integrity():
    cards_path = os.path.join(REPO_ROOT, "cards-data.js")
    docs_cards_path = os.path.join(REPO_ROOT, "docs", "cards-data.js")
    
    assert os.path.isfile(cards_path), "cards-data.js missing from root"
    assert os.path.isfile(docs_cards_path), "docs/cards-data.js missing"
    
    with open(cards_path, "r", encoding="utf-8") as f:
        content = f.read()
    with open(docs_cards_path, "r", encoding="utf-8") as f:
        docs_content = f.read()
    
    assert content == docs_content, "cards-data.js and docs/cards-data.js are out of sync!"
    
    m = re.search(r"window\.SYSTEM_DESIGN_FLASHCARDS\s*=\s*(\[.*\]);", content, re.DOTALL)
    assert m, "Failed to extract window.SYSTEM_DESIGN_FLASHCARDS array"
    
    cards = json.loads(m.group(1))
    assert len(cards) == 45, f"Expected 45 cards, got {len(cards)}"
    
    required_keys = [
        "id", "number", "folder", "title", "category", "category_id",
        "eli5", "analogy", "key_numbers", "google_example",
        "netflix_example", "interview_question", "interview_answer"
    ]
    
    for c in cards:
        for rk in required_keys:
            assert rk in c and c[rk], f"Card {c.get('number')} has missing or empty '{rk}'"
        
        # Verify folder exists
        folder_dir = os.path.join(REPO_ROOT, c["folder"])
        assert os.path.isdir(folder_dir), f"Card {c['number']} folder not found: {c['folder']}"

def test_html_and_dom_ids():
    app_js_path = os.path.join(REPO_ROOT, "app.js")
    with open(app_js_path, "r", encoding="utf-8") as f:
        app_js = f.read()
    
    dom_ids = set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", app_js))
    assert len(dom_ids) > 0, "No getElementById calls found in app.js"
    
    for html_rel in ["index.html", "docs/index.html"]:
        p = os.path.join(REPO_ROOT, html_rel)
        assert os.path.isfile(p), f"Missing {html_rel}"
        with open(p, "r", encoding="utf-8") as f:
            html = f.read()
        for elem_id in dom_ids:
            assert f'id="{elem_id}"' in html or f"id='{elem_id}'" in html, (
                f"Element ID '{elem_id}' referenced in app.js not found in {html_rel}"
            )

def test_assets_parity():
    for asset in ["app.css", "app.js"]:
        root_asset = os.path.join(REPO_ROOT, asset)
        docs_asset = os.path.join(REPO_ROOT, "docs", asset)
        with open(root_asset, "r", encoding="utf-8") as f:
            c1 = f.read()
        with open(docs_asset, "r", encoding="utf-8") as f:
            c2 = f.read()
        assert c1 == c2, f"{asset} differs between root and docs/"
