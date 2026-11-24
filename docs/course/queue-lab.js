(() => {
  "use strict";
  const controls = document.getElementById("queue-controls");
  const inputs = [...controls.querySelectorAll("input")];
  const number = new Intl.NumberFormat("en", { maximumFractionDigits: 2 });

  function render() {
    const values = {};
    for (const input of inputs) {
      values[input.id] = input.valueAsNumber;
      controls.querySelector(`[data-value="${input.id}"]`).textContent = input.value;
    }
    const { burst, duration, workers, after } = values;
    const capacity = workers * 20;
    const pending = Math.max(0, burst - capacity) * duration;
    const spare = capacity - after;
    const drain = spare > 0 ? pending / spare : 0;
    const horizon = duration + Math.max(60, drain);
    const end = Math.max(0, pending - spare * (horizon - duration));
    const peak = Math.max(1, pending, end);
    const point = (time, jobs) => `${10 + 300 * time / horizon},${115 - 105 * jobs / peak}`;
    const points = [point(0, 0), point(duration, pending)];
    if (drain > 0) points.push(point(duration + drain, 0));
    points.push(point(horizon, end));
    document.getElementById("queue-line").setAttribute("points", points.join(" "));
    document.getElementById("axis").textContent =
      `0 to ${number.format(horizon)} seconds · vertical scale 0 to ${number.format(peak)} jobs`;
    document.getElementById("queue-chart-title").textContent =
      `At ${duration} seconds, ${pending} jobs are pending. At ${number.format(horizon)} seconds, ${number.format(end)} are pending.`;
    document.getElementById("pending").textContent = number.format(pending);
    document.getElementById("capacity").textContent = `${capacity} jobs/s`;
    let message = "The queue stays empty after the burst.";
    if (spare < 0) message = `After the burst, the backlog grows by ${-spare} jobs per second.`;
    else if (pending && !spare) message = `The backlog stays at ${number.format(pending)} jobs after the burst.`;
    else if (pending) message = `The queue drains ${number.format(drain)} seconds after the burst.`;
    document.getElementById("recovery").textContent = message;
  }
  controls.disabled = false;
  controls.addEventListener("input", render);
  render();
})();
