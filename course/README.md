# Trail Notes course site

GitHub Pages serves the checked-in files under `docs/`. The six beginner lessons are generated from the First pass and Trail Notes exercise sections in the repository chapters.

## Update the lessons

1. Edit the source chapter or the metadata in `build.py`.
2. Run `python -m pip install -r course/requirements.txt`, then `python course/build.py` from the repo root.
3. Commit the sources and generated pages together. CI runs `python course/build.py --check` to catch any drift.

Open `http://127.0.0.1:8000/docs/` after running `python -m http.server 8000 --bind 127.0.0.1` from the repository root. Use HTTP for progress testing because browser storage behavior for local files can vary.

## Run the browser checks

~~~sh
python -m pip install -r course/requirements-browser.txt
python -m playwright install chromium
python course/browser_smoke.py
~~~

The smoke test serves the static site on a local project path and uses a temporary browser profile. It opens all six lessons, restarts the browser, transfers progress to a fresh profile, tests a failed storage write, checks that lessons still work without JavaScript, and exercises the simulator and flashcard entry point.

Course progress stays in local browser storage. The progress files contain lesson IDs and completion state. Import merges completions with progress on the current browser.
