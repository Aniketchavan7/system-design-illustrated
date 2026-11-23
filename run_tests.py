#!/usr/bin/env python3
"""
System Design Illustrated - Test Runner
Executes comprehensive validation across:
- All 45 module runnable demo.py files
- calculate.py capacity calculator
- Repository structure, syllabus modules, and markdown links
- Interactive Flashcard Web App data and DOM parity
"""

import os
import sys
import subprocess

def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(errors="backslashreplace")

    repo_root = os.path.dirname(os.path.abspath(__file__))
    os.chdir(repo_root)

    print("=" * 70)
    print("🧠 SYSTEM DESIGN ILLUSTRATED - COMPREHENSIVE TEST RUNNER")
    print("=" * 70)

    # Check if pytest is available
    try:
        import pytest
        print("\n🚀 Running full test suite via pytest...\n")
        exit_code = pytest.main(["-v", "tests"])
        sys.exit(exit_code)
    except ImportError:
        print("\n⚠️ pytest not installed. Running standard library test runner...\n")

    # Fallback standard library validation
    import py_compile
    import re
    import json

    errors = []
    passed = 0

    # 1. Compile all .py files
    print("1️⃣ Checking Python syntax across repository...")
    for root, _, files in os.walk(repo_root):
        if ".git" in root or ".venv" in root:
            continue
        for f in files:
            if f.endswith(".py"):
                fpath = os.path.join(root, f)
                rel = os.path.relpath(fpath, repo_root)
                try:
                    py_compile.compile(fpath, doraise=True)
                    passed += 1
                except Exception as e:
                    errors.append(f"Syntax error in {rel}: {e}")

    # 2. Run all 45 demo.py files
    print("\n2️⃣ Executing all 45 module demo.py scripts...")
    module_folders = [
        d for d in sorted(os.listdir(repo_root))
        if os.path.isdir(os.path.join(repo_root, d)) and re.match(r'^\d{2}-', d)
    ]
    for mod in module_folders:
        demo_path = os.path.join(repo_root, mod, "demo.py")
        if not os.path.isfile(demo_path):
            errors.append(f"Missing demo.py in {mod}")
            continue
        res = subprocess.run(
            [sys.executable, "-X", "utf8", "demo.py"],
            cwd=os.path.join(repo_root, mod),
            capture_output=True,
            encoding="utf-8",
            timeout=15
        )
        if res.returncode == 0:
            print(f"  ✓ {mod}")
            passed += 1
        else:
            errors.append(f"Demo failed in {mod} (exit {res.returncode}):\n{res.stderr}")

    # 3. Test calculate.py
    print("\n3️⃣ Testing calculate.py capacity calculator...")
    for preset in ["twitter", "youtube", "uber", "chat"]:
        res = subprocess.run(
            [sys.executable, "-X", "utf8", "calculate.py", "--preset", preset],
            capture_output=True,
            encoding="utf-8",
            timeout=5
        )
        if res.returncode == 0 and "SYSTEM DESIGN CAPACITY ESTIMATION REPORT" in res.stdout:
            passed += 1
        else:
            errors.append(f"calculate.py failed on preset '{preset}'")

    # 4. Flashcard validation
    print("\n4️⃣ Validating Flashcard Web App integrity...")
    cards_path = os.path.join(repo_root, "cards-data.js")
    with open(cards_path, "r", encoding="utf-8") as f:
        m = re.search(r"window\.SYSTEM_DESIGN_FLASHCARDS\s*=\s*(\[.*\]);", f.read(), re.DOTALL)
        if m:
            cards = json.loads(m.group(1))
            if len(cards) == 45:
                passed += 1
            else:
                errors.append(f"Expected 45 flashcards, got {len(cards)}")
        else:
            errors.append("Failed to extract flashcards from cards-data.js")

    print("\n" + "=" * 70)
    if errors:
        print(f"❌ TEST SUITE FAILED with {len(errors)} error(s):")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    else:
        print(f"✅ ALL TESTS PASSED! Total checks passed: {passed}")
        print("=" * 70)
        sys.exit(0)

if __name__ == "__main__":
    main()
