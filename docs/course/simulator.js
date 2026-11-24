(() => {
  "use strict";
  const form = document.querySelector("[data-sim-controls]");
  const traffic = document.getElementById("traffic");
  const servers = document.getElementById("servers");
  const perServer = document.getElementById("per-server");
  const failed = document.getElementById("failed");
  const hitRate = document.getElementById("hit-rate");
  const outage = document.getElementById("cache-outage");
  const toggle = document.querySelector("[data-failure-toggle]");
  const output = Object.fromEntries(["capacity", "healthy", "hits", "origin", "served", "shortfall", "sim-message"]
    .map(name => [name, document.querySelector(`[data-${name}]`)]));
  const inputValues = [traffic, servers, perServer, failed, hitRate].map(input =>
    [input, form.querySelector(`[data-value="${input.id}"]`)]);
  const format = new Intl.NumberFormat("en");

  function render() {
    failed.max = servers.value;
    const healthy = servers.valueAsNumber - failed.valueAsNumber;
    const capacity = healthy * perServer.valueAsNumber;
    const demand = traffic.valueAsNumber;
    const hits = outage.checked ? 0 : demand * hitRate.valueAsNumber / 100;
    const origin = demand - hits;
    const served = hits + Math.min(origin, capacity);
    hitRate.disabled = outage.checked;
    const shortfall = demand - served;

    for (const [input, label] of inputValues) {
      label.textContent = format.format(input.valueAsNumber);
    }
    output.capacity.textContent = format.format(capacity);
    output.healthy.textContent = format.format(healthy);
    output.hits.textContent = format.format(hits);
    output.origin.textContent = format.format(origin);
    output.served.textContent = format.format(served);
    output.shortfall.textContent = format.format(shortfall);
    output["sim-message"].textContent = shortfall
      ? `The site is short ${format.format(shortfall)} requests per second at this load.`
      : "The site can serve all incoming requests.";
    toggle.textContent = failed.valueAsNumber ? "Restore all servers" : "Fail one server";
  }

  form.disabled = false;
  form.addEventListener("input", render);
  toggle.addEventListener("click", () => {
    failed.value = failed.valueAsNumber ? "0" : "1";
    render();
  });
  render();
})();
