(() => {
  "use strict";

  const cutover = 15;
  const oldAddress = "192.0.2.10";
  const newAddress = "192.0.2.20";
  const controls = document.querySelector("[data-dns-controls]");
  const time = document.getElementById("dns-time");
  const ttl = document.getElementById("dns-ttl");
  const timeLabel = controls.querySelector("[data-dns-time]");
  const ttlLabel = controls.querySelector("[data-dns-ttl]");
  const authority = document.querySelector("[data-dns-authority]");
  const message = document.querySelector("[data-dns-message]");
  const resolvers = [["a", 0], ["b", 10]].map(([id, fetchedAt]) => ({
    fetchedAt,
    address: document.querySelector(`[data-dns-address="${id}"]`),
    detail: document.querySelector(`[data-dns-detail="${id}"]`),
  }));

  function render() {
    const selected = time.valueAsNumber;
    const seconds = ttl.valueAsNumber;
    timeLabel.textContent = `${selected} s`;
    ttlLabel.textContent = `${seconds} s`;
    authority.textContent = selected < cutover ? oldAddress : newAddress;

    const answers = resolvers.map(resolver => {
      const expiry = resolver.fetchedAt + seconds;
      if (selected < resolver.fetchedAt) {
        resolver.address.textContent = "—";
        resolver.detail.textContent = "First lookup has not happened";
        return null;
      }
      const expired = selected >= expiry;
      const address = expired ? newAddress : oldAddress;
      resolver.address.textContent = address;
      resolver.detail.textContent = expired ? "Successful refresh returns the new address" :
        `${expiry - selected} s until the old answer expires`;
      return address;
    });

    if (answers.includes(null)) {
      message.textContent = "Only resolver A has looked up the name.";
    } else if (answers[0] !== answers[1]) {
      message.textContent = "The two resolvers return different addresses.";
    } else {
      message.textContent = answers[0] === oldAddress
        ? "Both resolvers still have the old address in cache."
        : "Both resolvers return the new address.";
    }
  }

  controls.disabled = false;
  controls.addEventListener("input", render);
  for (const button of controls.querySelectorAll("[data-dns-jump]")) {
    button.addEventListener("click", () => {
      const times = {
        cutover,
        first: resolvers[0].fetchedAt + ttl.valueAsNumber,
        second: resolvers[1].fetchedAt + ttl.valueAsNumber,
      };
      time.value = String(times[button.dataset.dnsJump]);
      render();
    });
  }
  render();
})();
