(() => {
  "use strict";
  const controls = document.getElementById("quorum-controls");
  const nEl = document.getElementById("q-n");
  const wEl = document.getElementById("q-w");
  const rEl = document.getElementById("q-r");
  const fEl = document.getElementById("q-f");

  function render() {
    const n = nEl.valueAsNumber;
    wEl.max = String(n);
    rEl.max = String(n);
    fEl.max = String(n);

    const w = Math.min(wEl.valueAsNumber, n);
    const r = Math.min(rEl.valueAsNumber, n);
    const f = Math.min(fEl.valueAsNumber, n);
    wEl.value = String(w);
    rEl.value = String(r);
    fEl.value = String(f);

    controls.querySelector('[data-q-value="n"]').textContent = String(n);
    controls.querySelector('[data-q-value="w"]').textContent = String(w);
    controls.querySelector('[data-q-value="r"]').textContent = String(r);
    controls.querySelector('[data-q-value="f"]').textContent = String(f);

    const overlap = w + r - n;
    const healthy = n - f;
    const writeOk = healthy >= w;
    const readOk = healthy >= r;

    document.getElementById("q-overlap").textContent = overlap > 0
      ? `${overlap} node${overlap === 1 ? "" : "s"}`
      : "0 (no overlap)";
    document.getElementById("q-consistency").textContent = overlap > 0
      ? "Strong quorum overlap"
      : "Eventual / stale reads possible";
    document.getElementById("q-availability").textContent =
      `Writes ${writeOk ? "OK" : "Blocked"} · Reads ${readOk ? "OK" : "Blocked"}`;

    let msg = "";
    if (!writeOk || !readOk) {
      msg = `With ${healthy} healthy replica${healthy === 1 ? "" : "s"}, strict quorum cannot satisfy ${!writeOk ? "W" : "R"} (CP behavior).`;
    } else if (overlap <= 0) {
      msg = "Reads and writes operate fast on local subsets, but reads may return stale versions until async repair catches up.";
    } else {
      msg = `Every read intersects at least ${overlap} replica holding the latest write, even with ${f} failed node${f === 1 ? "" : "s"}.`;
    }
    document.getElementById("q-message").textContent = msg;
  }

  controls.disabled = false;
  controls.addEventListener("input", render);
  render();
})();
