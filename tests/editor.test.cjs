"use strict";
const assert = require("node:assert/strict");
const {test} = require("node:test");
const {readFileSync} = require("node:fs");
const vm = require("node:vm");
const source = readFileSync("knext/content/static/content/editor.js", "utf8");

class Element {
    constructor(value = "") {
        this.value = value;
        this.children = [];
        this.listeners = {};
        this.attributes = {};
        this.hidden = false;
        this.classList = {toggle: (name, enabled) => { this.attributes[name] = enabled; }};
    }
    append(...children) { this.children.push(...children); }
    add(child) { this.append(child); }
    replaceChildren(...children) { this.children = children; }
    setAttribute(name, value) { this.attributes[name] = value; }
    addEventListener(name, callback) { this.listeners[name] = callback; }
    focus() { this.focused = true; }
    setSelectionRange(start, end) { this.range = [start, end]; }
    async fire(name, event = {}) {
        event.defaultPrevented = false;
        event.preventDefault = () => { event.defaultPrevented = true; };
        await this.listeners[name]?.(event);
        return event;
    }
}
function setup({body = "## One\n\n😀 Text.\n\n### Two\nDetail.", saved = body, outline,
    fetch = async () => ({ok: true, json: async () => ({html: "<p>Preview</p>", outline: []})}),
    confirm = () => true} = {}) {
    const ids = [
        "editor-form", "editor-layout", "editor-network", "editor-status", "outline-select",
        "outline-search", "refresh-preview", "editor-outline-data", "editor-saved-data",
        "toggle-network", "toggle-preview", "editor-preview", "editor-bubbles",
        "preview-state", "editor-preview-body",
    ];
    const elements = Object.fromEntries(ids.map(id => [id, new Element()]));
    const textarea = new Element(body), title = new Element("Title"), leave = new Element();
    elements["editor-form"].querySelector = selector =>
        selector === "textarea" ? textarea : title;
    elements["editor-form"].dataset = {previewUrl: "/preview/"};
    elements["editor-network"].hidden = true;
    elements["editor-outline-data"].textContent = JSON.stringify(outline || [
        {title: "One", level: 2, start: 1, end: 4, parent: null},
        {title: "Two", level: 3, start: 5, end: 6, parent: 0},
    ]);
    elements["editor-saved-data"].textContent = JSON.stringify({body: saved, title: "Title"});
    const window = new Element();
    const context = vm.createContext({
        document: {
            getElementById: id => elements[id],
            createElement: () => new Element(),
            createElementNS: () => new Element(),
            querySelectorAll: () => [leave],
        },
        Option: class extends Element {
            constructor(label, value) { super(value); this.textContent = label; }
        },
        FormData: class {}, window, fetch, confirm,
    });
    vm.runInContext(source, context);
    return {elements, textarea, title, leave, window};
}

test("panels toggle without replacing the editor or losing selection", async () => {
    const {elements, textarea} = setup();
    textarea.setSelectionRange(3, 8);
    await elements["toggle-network"].fire("click");
    assert.equal(elements["editor-network"].hidden, false);
    assert.equal(elements["toggle-network"].attributes["aria-expanded"], "true");
    await elements["toggle-preview"].fire("click");
    assert.equal(elements["editor-preview"].hidden, true);
    assert.deepEqual(textarea.range, [3, 8]);
});

test("bubble navigation handles Unicode and preserves complete section ranges", async () => {
    const {elements, textarea} = setup();
    elements["outline-select"].value = "1";
    await elements["outline-select"].fire("change");
    assert.equal(textarea.value.slice(...textarea.range), "### Two\nDetail.");
    assert.equal(textarea.focused, true);
});

test("Python line separators and browser-normalized CRLF retain correct offsets", async () => {
    const body = "## One\u2028😀 Text\u2028### Two\u2028Detail";
    const outline = [
        {title: "One", level: 2, start: 1, end: 2, parent: null},
        {title: "Two", level: 3, start: 3, end: 4, parent: 0},
    ];
    const {elements, textarea} = setup({body, outline});
    elements["outline-select"].value = "1";
    await elements["outline-select"].fire("change");
    assert.equal(textarea.value.slice(...textarea.range), "### Two\u2028Detail");
    const normalized = setup({body: "## One\nText", saved: "## One\r\nText", outline: []});
    assert.equal((await normalized.window.fire("beforeunload")).defaultPrevented, false);
});

test("stale outline cannot select wrong text; refresh updates unsaved content without saving", async () => {
    const {elements, textarea} = setup({fetch: async () => ({
        ok: true, json: async () => ({html: "<h2>New</h2>", outline: [
            {title: "New", level: 2, start: 1, end: 2, parent: null},
        ]}),
    })});
    textarea.value = "## New\nText";
    await textarea.fire("input");
    elements["outline-select"].value = "0";
    await elements["outline-select"].fire("change");
    assert.equal(textarea.range, undefined);
    assert.match(elements["editor-status"].textContent, /Vorschau aktualisieren/);
    await elements["refresh-preview"].fire("click");
    assert.equal(elements["editor-preview-body"].innerHTML, "<h2>New</h2>");
    await elements["outline-select"].fire("change");
    assert.equal(textarea.value.slice(...textarea.range), "## New\nText");
    assert.match(elements["editor-status"].textContent, /New/);
    assert.equal((await setup({body: "Changed", saved: "Original"}).window.fire("beforeunload")).defaultPrevented, true);
});

test("late preview response cannot overwrite a newer buffer", async () => {
    let resolve;
    const pending = new Promise(done => { resolve = done; });
    const {elements, textarea} = setup({fetch: () => pending});
    const request = elements["refresh-preview"].fire("click");
    textarea.value = "Newer edit";
    resolve({ok: true, json: async () => ({html: "<p>Old</p>", outline: []})});
    await request;
    assert.equal(elements["editor-preview-body"].innerHTML, undefined);
    assert.match(elements["editor-status"].textContent, /inzwischen geändert/);
});

test("restore cancellation preserves dirty buffer; confirmed save does not prompt twice", async () => {
    const {elements, textarea, window} = setup({confirm: () => false});
    textarea.value = "Unsaved";
    const denied = await elements["editor-form"].fire("submit", {submitter: {id: "restore-backup"}});
    assert.equal(denied.defaultPrevented, true);
    assert.equal((await window.fire("beforeunload")).defaultPrevented, true);
    await elements["editor-form"].fire("submit", {submitter: {id: "save"}});
    assert.equal((await window.fire("beforeunload")).defaultPrevented, false);
});

test("all headings remain selectable while the bounded bubble view states its limit", () => {
    const outline = Array.from({length: 121}, (_, index) =>
        ({title: `Block ${index}`, start: 1, end: 1, level: 2, parent: null}));
    const {elements} = setup({outline});
    assert.equal(elements["outline-select"].children.length, 122);
    assert.match(elements["editor-bubbles"].children[1].textContent, /ersten 120/);
});

test("preview failures surface their messages instead of showing success", async () => {
    const {elements} = setup({fetch: async () => ({
        ok: false, json: async () => ({errors: {body: [{message: "Invalid Markdown"}]}}),
    })});
    await elements["refresh-preview"].fire("click");
    assert.match(elements["editor-status"].textContent, /fehlgeschlagen: Invalid Markdown/);
    assert.equal(elements["refresh-preview"].disabled, false);
});
