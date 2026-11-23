(() => {
  "use strict";

  const lessons = [...document.querySelectorAll("[data-lesson-link]")];
  if (!lessons.length) return;

  const lessonById = new Map(lessons.map(link => [link.dataset.lessonLink, link]));
  const storageKey = "sdi-trail-notes-progress-v1";
  const currentLesson = document.body.dataset.lessonId;
  const completeButton = document.querySelector("[data-complete]");
  const status = document.querySelector("[data-save-status]");
  const importInput = document.querySelector("[data-import]");
  const exportButton = document.querySelector("[data-export]");
  const emptyState = { version: 1, completed: [], lastLesson: null };
  let state = emptyState;
  let saved = false;

  function readSnapshot(value) {
    const snapshot = JSON.parse(value);
    if (!snapshot || snapshot.version !== 1 || !Array.isArray(snapshot.completed)) {
      throw new Error("Unsupported progress file.");
    }
    if (!snapshot.completed.every(id => lessonById.has(id)) ||
        (snapshot.lastLesson !== null && !lessonById.has(snapshot.lastLesson))) {
      throw new Error("Unrecognized lesson in progress file.");
    }
    return {
      version: 1,
      completed: [...new Set(snapshot.completed)],
      lastLesson: snapshot.lastLesson,
    };
  }

  function readStored() {
    try {
      const raw = window.localStorage.getItem(storageKey);
      return raw === null ? { state: emptyState, exists: false } :
        { state: readSnapshot(raw), exists: true };
    } catch {
      return null;
    }
  }

  function merge(first, second, lastLesson = first.lastLesson ?? second.lastLesson) {
    return {
      version: 1,
      completed: [...new Set([...first.completed, ...second.completed])],
      lastLesson,
    };
  }

  function nextLesson() {
    return state.lastLesson && !state.completed.includes(state.lastLesson)
      ? lessonById.get(state.lastLesson)
      : lessons.find(link => !state.completed.includes(link.dataset.lessonLink));
  }

  function render(message) {
    const done = new Set(state.completed);
    const next = nextLesson();

    for (const link of lessons) {
      const badge = link.querySelector("[data-lesson-status]");
      if (badge) {
        badge.textContent = done.has(link.dataset.lessonLink) ? "Complete" : "";
      }
    }
    for (const meter of document.querySelectorAll("[data-progress-meter]")) {
      meter.max = lessons.length;
      meter.value = done.size;
    }
    for (const count of document.querySelectorAll("[data-progress-count]")) {
      count.textContent = `${done.size} of ${lessons.length} lessons complete`;
    }
    const resume = document.querySelector("[data-resume]");
    const caption = document.querySelector("[data-resume-caption]");
    if (resume && caption) {
      resume.href = next?.href ?? document.querySelector("[data-practice-link]").href;
      const started = state.lastLesson !== null || done.size > 0;
      resume.textContent = next ? (started ? "Continue learning" : "Start learning") : "Practice failures";
      caption.textContent = next ? next.dataset.lessonTitle : "All lessons complete";
      caption.hidden = !started;
    }
    if (completeButton) {
      const completed = done.has(currentLesson);
      completeButton.disabled = completed;
      completeButton.textContent = completed ? "Lesson complete" : "Mark complete";
    }
    if (status) {
      status.textContent = message ?? (saved ? "Saved on this browser." :
        "Progress is saved on this browser after you start a lesson.");
    }
  }

  function persist(update, message) {
    const stored = readStored();
    state = update(stored ? merge(state, stored.state) : state);
    try {
      const snapshot = JSON.stringify(state);
      window.localStorage.setItem(storageKey, snapshot);
      saved = window.localStorage.getItem(storageKey) === snapshot;
    } catch {
      saved = false;
    }
    render(saved ? (message ?? "Saved on this browser.") :
      "Could not save on this browser. Export your progress before leaving this page.");
  }

  function load() {
    const stored = readStored();
    if (!stored) {
      render("Saved progress could not be read. You can import a progress file here.");
      return;
    }
    state = merge(stored.state, state);
    saved = stored.exists;
    render();
  }

  for (const control of document.querySelectorAll("[data-requires-progress]")) {
    control.hidden = false;
  }

  load();
  if (currentLesson && !state.completed.includes(currentLesson) && state.lastLesson !== currentLesson) {
    persist(previous => ({ ...previous, lastLesson: currentLesson }));
  }

  completeButton?.addEventListener("click", () => {
    persist(previous => {
      const completed = [...new Set([...previous.completed, currentLesson])];
      const next = lessons.find(link => !completed.includes(link.dataset.lessonLink));
      return { ...previous, completed, lastLesson: next?.dataset.lessonLink ?? null };
    }, "Lesson complete. Saved on this browser.");
  });

  exportButton?.addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(state, null, 2) + "\n"], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = "trail-notes-progress.json";
    document.body.append(link);
    link.click();
    link.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  });

  importInput?.addEventListener("change", async () => {
    const file = importInput.files?.[0];
    if (!file) return;
    try {
      if (file.size > 16_384) throw new Error("Progress file is too large.");
      const imported = readSnapshot(await file.text());
      persist(previous => merge(previous, imported), "Progress imported. Saved on this browser.");
    } catch {
      render("Could not read this progress file. Choose a Trail Notes progress export.");
    } finally {
      importInput.value = "";
    }
  });

  window.addEventListener("storage", event => {
    if (event.key === storageKey || event.key === null) load();
  });
  window.addEventListener("pageshow", event => {
    if (event.persisted) load();
  });
})();
