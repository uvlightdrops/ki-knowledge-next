(() => {
  const status = document.getElementById("job-refresh-status");
  if (!status) return;
  document.addEventListener("click", event => {
    if (!event.target.closest("[data-job-select-all]")) return;
    const boxes = Array.from(document.querySelectorAll('#job-cancel-form input[name="jobs"]'));
    const checked = boxes.some(box => !box.checked);
    boxes.forEach(box => { box.checked = checked; });
  });
  document.addEventListener("submit", event => {
    if (event.target.id !== "job-cancel-form") return;
    const count = document.querySelectorAll('#job-cancel-form input[name="jobs"]:checked').length;
    if (!count) {
      event.preventDefault();
      status.textContent = "Bitte zuerst wartende Jobs markieren.";
    } else if (!window.confirm(`${count} markierte wartende Jobs abbrechen?`)) {
      event.preventDefault();
    }
  });
  async function refresh() {
    if (!document.hidden) {
      try {
        const response = await fetch(window.location.href, {
          headers: { "X-Requested-With": "XMLHttpRequest" }, cache: "no-store",
          signal: AbortSignal.timeout(10000),
        });
        if (!response.ok || response.redirected) throw new Error("Status nicht verfügbar");
        const next = new DOMParser().parseFromString(await response.text(), "text/html");
        const blocks = Array.from(document.querySelectorAll("[data-job-live]"));
        const replacements = blocks.map(block => next.getElementById(block.id));
        if (replacements.some(block => !block)) throw new Error("Ungültige Statusantwort");
        const selected = new Set(Array.from(
          document.querySelectorAll('#job-cancel-form input[name="jobs"]:checked'),
          box => box.value,
        ));
        blocks.forEach((block, index) => {
          if (!block.contains(document.activeElement)) {
            replacements[index].querySelectorAll('input[name="jobs"]').forEach(box => {
              box.checked = selected.has(box.value);
            });
            block.replaceWith(replacements[index]);
          }
        });
        status.textContent = "Status automatisch aktualisiert · " + new Date().toLocaleTimeString();
      } catch (error) {
        status.textContent = "Aktualisierung fehlgeschlagen; zuletzt gelesener Stand bleibt sichtbar. Seite neu laden.";
        console.error("Importstatus:", error);
      }
    }
    window.setTimeout(refresh, 3000);
  }
  window.setTimeout(refresh, 3000);
})();
