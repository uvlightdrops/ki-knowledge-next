"use strict";
(() => {
    const panel = document.getElementById("editor-ai");
    const toggle = document.getElementById("toggle-ai");
    const layout = document.getElementById("editor-layout");
    toggle.hidden = false;
    toggle.addEventListener("click", () => {
        panel.hidden = !panel.hidden;
        toggle.setAttribute("aria-expanded", String(!panel.hidden));
        layout.classList.toggle("ai-open", !panel.hidden);
    });
    const generate = document.getElementById("ai-generate");
    if (!generate) return;
    const form = document.getElementById("editor-form");
    const body = form.querySelector("textarea"), title = form.querySelector('input[name="title"]');
    const get = id => document.getElementById(id);
    const status = get("ai-status"), result = get("ai-result");
    const instruction = get("ai-instruction"), context = get("ai-context");
    let target = null, proposal = null, busy = false, accepted = false;
    const message = (text, error = false) => {
        status.textContent = text;
        status.setAttribute("role", error ? "alert" : "status");
    };
    const unchanged = () => target && target.body === body.value && target.title === title.value
        && target.expected === form.querySelector('[name="expected"]').value;
    function selectTarget(whole) {
        if (busy) return;
        if (proposal) {
            message("Bitte den offenen Vorschlag zuerst übernehmen oder verwerfen.", true);
            return;
        }
        const start = whole ? 0 : body.selectionStart, end = whole ? body.value.length : body.selectionEnd;
        if (start === end) {
            message("Zuerst im Markdown-Editor Text markieren oder „Ganzen Text verwenden“ wählen.", true);
            return;
        }
        target = {
            body: body.value, title: title.value,
            expected: form.querySelector('[name="expected"]').value,
            start: Array.from(body.value.slice(0, start)).length,
            end: Array.from(body.value.slice(0, end)).length,
        };
        get("ai-original").value = body.value.slice(start, end);
        get("ai-scope").textContent = `${whole ? "Ganzer Text" : "Textauswahl"} · ${target.end - target.start} Zeichen`;
        message("Zieltext festgelegt. Auftrag prüfen und ausdrücklich absenden.");
    }
    get("ai-use-selection").addEventListener("click", () => selectTarget(false));
    get("ai-use-whole").addEventListener("click", () => selectTarget(true));
    get("ai-task").addEventListener("change", event => { instruction.value = event.target.value; });
    get("ai-add-context-preset").addEventListener("click", () => {
        if (busy) return;
        const preset = get("ai-context-preset").value;
        if (!preset) { message("Bitte eine Kontextvorlage wählen.", true); return; }
        const combined = context.value ? `${context.value}\n\n${preset}` : preset;
        if (combined.length > context.maxLength) {
            message("Zusatzkontext zu lang. Vor dem Einfügen kürzen.", true);
            return;
        }
        context.value = combined;
        get("ai-context-preset").value = "";
        context.focus();
        message("Kontextvorlage eingefügt. Zusatzkontext und Auftrag vor dem Absenden prüfen.");
    });
    function data() {
        const payload = new FormData(form);
        payload.set("instruction", instruction.value);
        payload.set("context", context.value);
        payload.set("start", target.start);
        payload.set("end", target.end);
        return payload;
    }
    async function post(url, payload) {
        const response = await fetch(url, {
            method: "POST", body: payload, signal: AbortSignal.timeout(135000),
        });
        if (response.redirected) throw new Error("Sitzung abgelaufen. Eingaben sichern und erneut anmelden.");
        const answer = await response.json();
        if (!response.ok) throw new Error(answer.error || "KI-Aktion fehlgeschlagen.");
        return answer;
    }
    function pending(value) {
        busy = value;
        for (const id of ["ai-generate", "ai-accept", "ai-discard", "ai-use-selection", "ai-use-whole", "ai-add-context-preset"]) {
            get(id).disabled = value;
        }
    }
    generate.addEventListener("click", async () => {
        if (!unchanged()) {
            message("Zieltext fehlt oder wurde inzwischen verändert. Auswahl erneut festlegen.", true);
            return;
        }
        if (proposal) {
            message("Bitte den offenen Vorschlag zuerst übernehmen oder verwerfen.", true);
            return;
        }
        if (!instruction.value.trim()) { message("Bitte einen Auftrag eingeben.", true); return; }
        pending(true);
        message("KI erstellt einen Vorschlag. Dein Arbeitsstand bleibt unverändert.");
        try {
            proposal = await post(panel.dataset.proposeUrl, data());
            get("ai-proposal").value = proposal.text;
            result.hidden = false;
            message(unchanged() ? `Vorschlag von ${proposal.provider} · ${proposal.model}. Bitte prüfen.`
                : "Vorschlag angekommen; Ausgangstext inzwischen verändert. Keine Übernahme möglich.", !unchanged());
        } catch (error) {
            message(`KI-Auftrag fehlgeschlagen: ${error.message}`, true);
        } finally { pending(false); }
    });
    get("ai-accept").addEventListener("click", async () => {
        if (!proposal || !unchanged()) {
            message("Ausgangstext inzwischen verändert. Vorschlag manuell vergleichen oder neu erstellen.", true);
            return;
        }
        if (!confirm("Vorschlag übernehmen und speichern? Dein bisheriger Text bleibt als Sicherung erhalten.")) return;
        const payload = data();
        payload.set("text", get("ai-proposal").value);
        pending(true);
        try {
            const answer = await post(proposal.accept_url, payload);
            accepted = true;
            form.dispatchEvent(new CustomEvent("editor:saved"));
            window.location.assign(answer.url);
        } catch (error) {
            message(`Übernahme fehlgeschlagen: ${error.message}`, true);
        } finally { pending(false); }
    });
    get("ai-discard").addEventListener("click", async () => {
        if (!proposal) return;
        pending(true);
        try {
            await post(proposal.discard_url, new FormData(form));
            proposal = null;
            result.hidden = true;
            get("ai-proposal").value = "";
            message("Vorschlag verworfen. Dein Text wurde nicht verändert.");
        } catch (error) { message(`Verwerfen fehlgeschlagen: ${error.message}`, true); }
        finally { pending(false); }
    });
    for (const field of [body, title]) field.addEventListener("input", () => {
        if (target && !unchanged()) message("Ausgangstext verändert. Vorhandener Vorschlag bleibt zum Vergleich; Übernahme ist gesperrt.", true);
    });
    window.addEventListener("beforeunload", event => {
        if (!accepted && (busy || (proposal && get("ai-proposal").value !== proposal.text))) {
            event.preventDefault();
            event.returnValue = "";
        }
    });
    const saved = JSON.parse(get("editor-ai-pending").textContent);
    if (saved) {
        target = saved;
        proposal = saved;
        instruction.value = saved.instruction;
        context.value = saved.context;
        get("ai-original").value = Array.from(saved.body).slice(saved.start, saved.end).join("");
        get("ai-proposal").value = saved.text;
        get("ai-scope").textContent = `Frühere Textauswahl · ${saved.end - saved.start} Zeichen`;
        result.hidden = false;
        message(unchanged() ? "Dein letzter offener Vorschlag wurde wieder geladen. Bitte prüfen."
            : "Offener Vorschlag geladen; Ausgangstext weicht ab. Nur vergleichen oder verwerfen.", !unchanged());
    }
})();
