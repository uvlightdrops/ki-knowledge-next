"use strict";
(() => {
    const form = document.getElementById("editor-form");
    const body = form.querySelector("textarea"), title = form.querySelector('input[name="title"]');
    const initial = JSON.parse(document.getElementById("editor-saved-data").textContent);
    initial.body = initial.body.replace(/\r\n?/g, "\n");
    const layout = document.getElementById("editor-layout");
    const network = document.getElementById("editor-network");
    const status = document.getElementById("editor-status");
    const select = document.getElementById("outline-select");
    const search = document.getElementById("outline-search");
    const refresh = document.getElementById("refresh-preview");
    let outline = JSON.parse(document.getElementById("editor-outline-data").textContent);
    let outlinedBody = initial.body;
    let requestNumber = 0;
    let leaving = false;
    const dirty = () => body.value !== initial.body || title.value !== initial.title;
    const message = text => { status.textContent = text; };
    const svgElement = (tag, attributes) => {
        const element = document.createElementNS("http://www.w3.org/2000/svg", tag);
        for (const [name, value] of Object.entries(attributes)) element.setAttribute(name, value);
        return element;
    };
    function choose(index) {
        if (body.value !== outlinedBody) {
            message("Bitte die Vorschau aktualisieren, bevor du im veränderten Text einen Abschnitt wählst.");
            return;
        }
        const block = outline[index];
        const offsets = [0];
        for (const match of body.value.matchAll(/\r\n|[\n\r\v\f\x1c-\x1e\x85\u2028\u2029]/g)) {
            offsets.push(match.index + match[0].length);
        }
        const offset = line => offsets[line] ?? body.value.length;
        const start = block ? offset(block.start - 1) : 0;
        const end = block ? Math.min(offset(block.end), body.value.length) : body.value.length;
        body.focus();
        body.setSelectionRange(start, end);
        message(block ? `Abschnitt: ${block.title}` : "Ganzer Text ausgewählt.");
    }
    function drawOutline() {
        const query = search.value.trim().toLocaleLowerCase();
        const matches = outline.map((block, index) => ({...block, index}))
            .filter(block => block.title.toLocaleLowerCase().includes(query));
        select.replaceChildren(new Option("Ganzer Text", ""));
        for (const block of matches) select.add(new Option(block.title, block.index));
        const container = document.getElementById("editor-bubbles");
        container.replaceChildren();
        const visible = matches.slice(0, 120);
        const svg = svgElement("svg", {viewBox: `0 0 320 ${Math.max(90, visible.length * 65 + 65)}`,
            role: "group", "aria-label": "Abschnitte als Bubble-Netz"});
        const positions = new Map(visible.map((block, row) =>
            [block.index, {x: 35 + (block.level - 1) * 22, y: row * 65 + 45}]));
        for (const block of visible) {
            const point = positions.get(block.index), parent = positions.get(block.parent);
            if (parent) svg.append(svgElement("line", {x1: parent.x, y1: parent.y, x2: point.x, y2: point.y}));
        }
        for (const block of visible) {
            const point = positions.get(block.index);
            const link = svgElement("a", {href: "#id_body", "aria-label": `Abschnitt ${block.title || "(ohne Titel)"}`});
            const tooltip = svgElement("title", {});
            tooltip.textContent = block.title;
            const text = svgElement("text", {x: point.x + 22, y: point.y + 4});
            text.textContent = block.title.length > 24 ? block.title.slice(0, 23) + "…" : block.title;
            link.append(tooltip, svgElement("circle", {cx: point.x, cy: point.y, r: 15}), text);
            link.addEventListener("click", event => { event.preventDefault(); choose(block.index); });
            svg.append(link);
        }
        container.append(svg);
        if (!matches.length || matches.length > visible.length) {
            const hint = document.createElement("p");
            hint.textContent = !matches.length ? "Keine passenden Überschriften."
                : "Die Bubble-Ansicht zeigt die ersten 120 Treffer. Alle Treffer sind in der Abschnittsauswahl erreichbar.";
            container.append(hint);
        }
    }
    for (const [buttonId, panel] of [
        ["toggle-network", network], ["toggle-preview", document.getElementById("editor-preview")],
    ]) {
        const button = document.getElementById(buttonId);
        button.hidden = false;
        button.addEventListener("click", () => {
            panel.hidden = !panel.hidden;
            button.setAttribute("aria-expanded", String(!panel.hidden));
            layout.classList.toggle("network-open", !network.hidden);
            layout.classList.toggle("preview-closed", document.getElementById("editor-preview").hidden);
        });
    }
    select.addEventListener("change", () => choose(select.value === "" ? -1 : Number(select.value)));
    search.addEventListener("input", drawOutline);
    for (const field of [body, title]) field.addEventListener("input", () => {
        leaving = false;
        message(dirty() ? "Ungespeicherte Änderungen." : "Gespeicherter Arbeitsstand");
        document.getElementById("preview-state").textContent = "Vorschau bei Bedarf aktualisieren; es wird nichts gespeichert.";
    });
    refresh.hidden = false;
    refresh.addEventListener("click", async () => {
        const serial = ++requestNumber, submitted = {body: body.value, title: title.value};
        refresh.disabled = true;
        try {
            const response = await fetch(form.dataset.previewUrl, {method: "POST", body: new FormData(form)});
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || Object.values(result.errors || {})
                .flat().map(error => error.message).join(" ") || "Vorschau konnte nicht erstellt werden.");
            if (serial !== requestNumber || submitted.body !== body.value || submitted.title !== title.value) {
                message("Text inzwischen geändert. Bitte die Vorschau erneut aktualisieren.");
                return;
            }
            document.getElementById("editor-preview-body").innerHTML = result.html;
            document.getElementById("preview-state").textContent = "Vorschau deiner Eingaben; noch nicht gespeichert.";
            outline = result.outline;
            outlinedBody = submitted.body;
            drawOutline();
            message("Vorschau und Bubble-Navigation aktualisiert. Es wurde nichts gespeichert.");
        } catch (error) {
            message(`Vorschau fehlgeschlagen: ${error.message}`);
        } finally {
            refresh.disabled = false;
        }
    });
    form.addEventListener("submit", event => {
        if (event.submitter?.id === "restore-backup") {
            const warning = dirty() ? "Ungespeicherte Eingaben werden verworfen. " : "";
            if (!confirm(warning + "Gewählten Sicherungsstand wiederherstellen?")) event.preventDefault();
        }
        if (!event.defaultPrevented) leaving = true;
    });
    for (const link of document.querySelectorAll("[data-leave-editor]")) link.addEventListener("click", event => {
        if (dirty() && !confirm("Ungespeicherte Änderungen verwerfen?")) event.preventDefault();
        else leaving = true;
    });
    window.addEventListener("beforeunload", event => {
        if (dirty() && !leaving) { event.preventDefault(); event.returnValue = ""; }
    });
    drawOutline();
    if (dirty()) message("Ungespeicherte Eingaben erhalten. Bitte Fehler oder Speicherkonflikt prüfen.");
})();
