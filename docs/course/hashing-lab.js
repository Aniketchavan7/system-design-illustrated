(() => {
  "use strict";
  const controls = document.getElementById("hash-controls");
  const nodesInput = document.getElementById("hash-nodes");
  const vnodesInput = document.getElementById("hash-vnodes");
  const deltaInput = document.getElementById("hash-delta");
  const ringGroup = document.getElementById("hash-ring-nodes");

  // Deterministic 32-bit FNV-1a + Murmur3 finalizer for uniform ring distribution
  function hash32(str) {
    let h = 2166136261;
    for (let i = 0; i < str.length; i++) {
      h ^= str.charCodeAt(i);
      h = Math.imul(h, 16777619);
    }
    h ^= h >>> 16;
    h = Math.imul(h, 0x85ebca6b);
    h ^= h >>> 13;
    h = Math.imul(h, 0xc2b2ae35);
    h ^= h >>> 16;
    return h >>> 0;
  }

  function buildRing(nodeCount, vnodeCount) {
    const entries = [];
    for (let n = 0; n < nodeCount; n++) {
      for (let v = 0; v < vnodeCount; v++) {
        entries.push({ pos: hash32(`node-${n}#v-${v}`), node: n });
      }
    }
    entries.sort((a, b) => a.pos - b.pos);
    return entries;
  }

  function lookup(ring, keyHash) {
    let lo = 0;
    let hi = ring.length - 1;
    while (lo <= hi) {
      const mid = (lo + hi) >>> 1;
      if (ring[mid].pos >= keyHash) hi = mid - 1;
      else lo = mid + 1;
    }
    return lo < ring.length ? ring[lo].node : ring[0].node;
  }

  function drawRing(beforeCount, afterCount, vnodes) {
    while (ringGroup.firstChild) ringGroup.removeChild(ringGroup.firstChild);
    const ns = "http://www.w3.org/2000/svg";
    const total = Math.max(beforeCount, afterCount);
    const sampleV = Math.min(vnodes, 8);
    for (let n = 0; n < total; n++) {
      for (let v = 0; v < sampleV; v++) {
        const angle = (hash32(`node-${n}#v-${v}`) / 4294967295) * Math.PI * 2;
        const cx = 130 + 56 * Math.cos(angle);
        const cy = 75 + 56 * Math.sin(angle);
        const dot = document.createElementNS(ns, "circle");
        dot.setAttribute("cx", cx.toFixed(1));
        dot.setAttribute("cy", cy.toFixed(1));
        dot.setAttribute("r", n >= afterCount || (afterCount > beforeCount && n === total - 1) ? "4.5" : "3.2");
        dot.setAttribute("fill", "currentColor");
        if (n >= afterCount) dot.setAttribute("opacity", "0.3");
        ringGroup.appendChild(dot);
      }
    }
  }

  function render() {
    const nodes = nodesInput.valueAsNumber;
    const vnodes = vnodesInput.valueAsNumber;
    const delta = deltaInput.valueAsNumber;
    const nextNodes = Math.max(1, nodes + delta);

    controls.querySelector('[data-hash-value="nodes"]').textContent = String(nodes);
    controls.querySelector('[data-hash-value="vnodes"]').textContent = String(vnodes);
    const deltaLabel = delta === 1 ? "+1 node added" : delta === -1 ? "1 node failed" : "Steady state (0 change)";
    controls.querySelector('[data-hash-value="delta"]').textContent = deltaLabel;

    const ringBefore = buildRing(nodes, vnodes);
    const ringAfter = buildRing(nextNodes, vnodes);

    const TOTAL_KEYS = 1000;
    let chMoved = 0;
    let modMoved = 0;
    const counts = new Array(nextNodes).fill(0);

    for (let k = 0; k < TOTAL_KEYS; k++) {
      const kh = hash32(`cache-key:${k}`);
      const bCh = lookup(ringBefore, kh);
      const aCh = lookup(ringAfter, kh);
      if (bCh !== aCh) chMoved++;
      counts[aCh]++;
      if (kh % nodes !== kh % nextNodes) modMoved++;
    }

    const chPct = Math.round((chMoved / TOTAL_KEYS) * 100);
    const modPct = Math.round((modMoved / TOTAL_KEYS) * 100);
    const mean = TOTAL_KEYS / nextNodes;
    const skew = mean > 0 ? Math.max(...counts) / mean : 1;

    document.getElementById("hash-ch-moved").textContent = `${chPct}%`;
    document.getElementById("hash-mod-moved").textContent = `${modPct}%`;
    document.getElementById("hash-skew").textContent = `${skew.toFixed(2)}×`;

    const msgEl = document.getElementById("hash-message");
    if (delta === 0) {
      msgEl.textContent = vnodes < 8
        ? "Few virtual nodes leave uneven hash arcs; increase vnodes to smooth load skew."
        : "Steady state balanced across the ring with tight load distribution.";
    } else {
      const saved = Math.max(0, modPct - chPct);
      msgEl.textContent = `Consistent hashing preserves ${saved}% more cache hits than modulo hashing during resize.`;
    }
    drawRing(nodes, nextNodes, vnodes);
  }

  controls.disabled = false;
  controls.addEventListener("input", render);
  render();
})();
