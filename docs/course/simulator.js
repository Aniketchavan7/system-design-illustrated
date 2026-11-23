(() => {
  "use strict";
  const form = document.querySelector("[data-sim-controls]");
  const traffic = document.getElementById("traffic");
  const servers = document.getElementById("servers");
  const perServer = document.getElementById("per-server");
  const failed = document.getElementById("failed");
  const toggle = document.querySelector("[data-failure-toggle]");
  const output = Object.fromEntries(["capacity", "healthy", "served", "shortfall", "sim-message"]
    .map(name => [name, document.querySelector(`[data-${name}]`)]));
  const inputValues = [traffic, servers, perServer, failed].map(input =>
    [input, form.querySelector(`[data-value="${input.id}"]`)]);
  const format = new Intl.NumberFormat("en");

  function render() {
    failed.max = servers.value;
    const healthy = servers.valueAsNumber - failed.valueAsNumber;
    const capacity = healthy * perServer.valueAsNumber;
    const demand = traffic.valueAsNumber;
    const served = Math.min(demand, capacity);
    const shortfall = demand - served;

    for (const [input, label] of inputValues) {
      label.textContent = format.format(input.valueAsNumber);
    }
    output.capacity.textContent = format.format(capacity);
    output.healthy.textContent = format.format(healthy);
    output.served.textContent = format.format(served);
    output.shortfall.textContent = format.format(shortfall);
    output["sim-message"].textContent = shortfall
      ? `The site is short ${format.format(shortfall)} requests per second at this load.`
      : "The healthy servers can keep up with incoming traffic.";
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
