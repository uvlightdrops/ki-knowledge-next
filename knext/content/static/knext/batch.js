document.querySelectorAll("[data-batch-form]").forEach(form => {
  const header = document.querySelector(`[data-batch-toggle="${form.id}"]`);
  const status = form.querySelector("[data-batch-status]");
  const boxes = Array.from(document.querySelectorAll('input[type="checkbox"]'))
    .filter(input => input.form === form && input !== header);
  function update() {
    const count = boxes.filter(input => input.checked).length;
    header.checked = boxes.length > 0 && count === boxes.length;
    header.indeterminate = count > 0 && count < boxes.length;
    header.disabled = boxes.length === 0;
    status.textContent = `${count} von ${boxes.length} Einträgen dieser Tabelle markiert (max. 100).`;
  }
  header.addEventListener("change", () => {
    boxes.forEach(input => { input.checked = header.checked; });
    update();
  });
  boxes.forEach(input => input.addEventListener("change", update));
  form.addEventListener("submit", event => {
    const count = boxes.filter(input => input.checked).length;
    if (count < 1 || count > 100) {
      event.preventDefault();
      status.textContent = "Bitte 1 bis 100 Einträge in der zugehörigen Tabelle markieren.";
      status.setAttribute("role", "alert");
      (boxes[0] || header).focus();
    }
  });
  update();
});
