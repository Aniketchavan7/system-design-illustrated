(() => {
  "use strict";

  const form = document.querySelector("[data-library-filter]");
  const search = form.elements.namedItem("q");
  const category = form.elements.namedItem("topic");
  const count = document.querySelector("[data-catalog-count]");
  const empty = document.querySelector("[data-no-topics]");
  const normalize = text => text.normalize("NFKD").replace(/\p{Mark}/gu, "")
    .toLowerCase().replace(/[^\p{Letter}\p{Number}]+/gu, " ").trim();
  const groups = [...document.querySelectorAll("[data-topic-group]")].map(group => ({
    element: group,
    category: group.dataset.topicGroup,
    entries: [...group.querySelectorAll("[data-topic-row]")].map(row => ({
      element: row,
      text: normalize(row.dataset.search),
    })),
  }));
  const total = groups.reduce((sum, group) => sum + group.entries.length, 0);

  function render(updateUrl = true) {
    const words = normalize(search.value).split(/\s+/).filter(Boolean);
    let shown = 0;
    for (const group of groups) {
      const categoryMatches = !category.value || group.category === category.value;
      let groupCount = 0;
      for (const entry of group.entries) {
        const matches = categoryMatches && words.every(word => entry.text.includes(word));
        entry.element.hidden = !matches;
        if (matches) groupCount += 1;
      }
      group.element.hidden = groupCount === 0;
      shown += groupCount;
    }
    count.textContent = `${shown} of ${total} topics`;
    empty.hidden = shown !== 0;

    if (updateUrl && window.location.protocol !== "file:") {
      const url = new URL(window.location.href);
      for (const [key, value] of [["q", search.value.trim()], ["topic", category.value]]) {
        if (value) url.searchParams.set(key, value);
        else url.searchParams.delete(key);
      }
      if (url.href !== window.location.href) window.history.replaceState(null, "", url);
    }
  }

  function readUrl() {
    const params = new URLSearchParams(window.location.search);
    search.value = (params.get("q") ?? "").slice(0, search.maxLength);
    category.value = params.get("topic") ?? "";
    if (category.selectedIndex === -1) category.value = "";
    render(false);
  }

  form.hidden = false;
  count.hidden = false;
  readUrl();
  search.addEventListener("input", () => render());
  category.addEventListener("change", () => render());
  form.addEventListener("submit", event => {
    event.preventDefault();
    render();
  });
  form.addEventListener("reset", event => {
    event.preventDefault();
    search.value = "";
    category.value = "";
    render();
    search.focus();
  });
  window.addEventListener("popstate", readUrl);
})();
