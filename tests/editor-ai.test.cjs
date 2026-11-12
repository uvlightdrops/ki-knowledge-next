"use strict";
const assert = require("node:assert/strict");
const {test} = require("node:test");
const {readFileSync} = require("node:fs");
const vm = require("node:vm");
const source = readFileSync("knext/content/static/content/editor-ai.js", "utf8");

class Element {
  constructor(value = "") {
    this.value = value;
    this.hidden = false;
    this.attributes = {};
    this.listeners = {};
    this.dataset = {};
    this.classList = {toggle: () => {}};
  }
  addEventListener(name, callback) { this.listeners[name] = callback; }
  setAttribute(name, value) { this.attributes[name] = value; }
  focus() { this.focused = true; }
  async fire(name, event = {}) { return this.listeners[name]?.(event); }
}
function setup({response, initial = "Intro 😀. Selected tail.", saved = null} = {}) {
  const ids = [
    "editor-ai", "toggle-ai", "editor-layout", "ai-generate", "editor-form",
    "ai-status", "ai-result", "ai-instruction", "ai-context", "ai-context-preset", "ai-add-context-preset", "ai-use-selection",
    "ai-use-whole", "ai-original", "ai-scope", "ai-task", "ai-proposal", "ai-accept", "ai-discard", "editor-ai-pending",
  ];
  const elements = Object.fromEntries(ids.map(id => [id, new Element()]));
  const body = new Element(initial), title = new Element("Title"), expected = new Element("1");
  body.selectionStart = initial.indexOf("Selected");
  body.selectionEnd = body.selectionStart + 8;
  elements["editor-ai"].hidden = true;
  elements["editor-ai"].dataset.proposeUrl = "/propose/";
  elements["ai-instruction"].value = "Improve.";
  elements["editor-ai-pending"].textContent = JSON.stringify(saved);
  elements["ai-context"].value = "Explicit context.";
  elements["ai-context"].maxLength = 30000;
  elements["editor-form"].querySelector = selector =>
    selector === "textarea" ? body : selector.includes("expected") ? expected : title;
  const events = [];
  elements["editor-form"].dispatchEvent = event => events.push(event.type);
  const requests = [], redirects = [], windowListeners = {};
  const context = {
    document: {getElementById: id => elements[id]},
    FormData: class {constructor() {this.values = {};} set(key, value) {this.values[key] = value;}},
    AbortSignal: {timeout: () => {}}, CustomEvent: class {constructor(type) {this.type = type;}},
    confirm: () => true,
    window: {
      location: {assign: url => redirects.push(url)},
      addEventListener: (name, callback) => { windowListeners[name] = callback; },
    },
    fetch: async (url, options) => {
      requests.push({url, data: options.body.values});
      return response ? response(url) : {ok: true, json: async () => ({
        id: "proposal", text: "Improved.", provider: "openai", model: "test",
        accept_url: "/accept/", discard_url: "/discard/", url: "/editor/",
      })};
    },
  };
  vm.runInNewContext(source, context);
  return {elements, body, title, expected, requests, redirects, events, context, windowListeners};
}

test("AI panel toggles without modifying the source or its selection", async () => {
  const ui = setup();
  await ui.elements["toggle-ai"].fire("click");
  assert.equal(ui.elements["editor-ai"].hidden, false);
  assert.equal(ui.body.selectionEnd - ui.body.selectionStart, 8);
  assert.equal(ui.body.value, "Intro 😀. Selected tail.");
});

test("selection sends Unicode codepoint offsets and explicit instruction and context", async () => {
  const ui = setup();
  await ui.elements["ai-use-selection"].fire("click");
  assert.equal(ui.elements["ai-original"].value, "Selected");
  await ui.elements["ai-generate"].fire("click");
  assert.equal(ui.requests[0].data.start, 9);
  assert.equal(ui.requests[0].data.end, 17);
  assert.equal(ui.requests[0].data.context, "Explicit context.");
  assert.equal(ui.body.value, "Intro 😀. Selected tail.");
  assert.equal(ui.elements["ai-proposal"].value, "Improved.");
  assert.equal(ui.elements["ai-result"].hidden, false);
});

test("context preset selection alone sends nothing and insertion preserves editable context", async () => {
  const ui = setup();
  ui.elements["ai-context-preset"].value = "Semantisch gliedern.";
  assert.equal(ui.requests.length, 0);
  assert.equal(ui.elements["ai-context"].value, "Explicit context.");
  await ui.elements["ai-add-context-preset"].fire("click");
  assert.equal(ui.elements["ai-context"].value, "Explicit context.\n\nSemantisch gliedern.");
  assert.equal(ui.elements["ai-context-preset"].value, "");
  assert.equal(ui.elements["ai-context"].focused, true);
  assert.equal(ui.requests.length, 0);
  ui.elements["ai-context"].value += " Meine Ergänzung.";
  await ui.elements["ai-use-whole"].fire("click");
  await ui.elements["ai-generate"].fire("click");
  assert.equal(ui.requests[0].data.context, "Explicit context.\n\nSemantisch gliedern. Meine Ergänzung.");
});

test("context presets fill empty context and reject missing choices or overlong insertions", async () => {
  const ui = setup();
  await ui.elements["ai-add-context-preset"].fire("click");
  assert.match(ui.elements["ai-status"].textContent, /Kontextvorlage wählen/);
  ui.elements["ai-context"].value = "";
  ui.elements["ai-context-preset"].value = "Vorlage";
  await ui.elements["ai-add-context-preset"].fire("click");
  assert.equal(ui.elements["ai-context"].value, "Vorlage");
  ui.elements["ai-context"].value = "x".repeat(29999);
  ui.elements["ai-context-preset"].value = "Vorlage";
  await ui.elements["ai-add-context-preset"].fire("click");
  assert.equal(ui.elements["ai-context"].value.length, 29999);
  assert.match(ui.elements["ai-status"].textContent, /zu lang/);
  assert.equal(ui.elements["ai-context-preset"].value, "Vorlage");
  assert.equal(ui.requests.length, 0);
});

test("stale buffers block acceptance even when a late answer arrives", async () => {
  let release;
  const ready = new Promise(resolve => { release = resolve; });
  const ui = setup({response: async () => {
    await ready;
    return {ok: true, json: async () => ({
      text: "Improved.", provider: "openai", model: "test", accept_url: "/accept/",
    })};
  }});
  await ui.elements["ai-use-whole"].fire("click");
  const generating = ui.elements["ai-generate"].fire("click");
  ui.body.value += "Changed";
  release();
  await generating;
  await ui.elements["ai-accept"].fire("click");
  assert.equal(ui.requests.length, 1);
  assert.match(ui.elements["ai-status"].textContent, /inzwischen verändert/);
  assert.equal(ui.redirects.length, 0);
});

test("accept sends reviewed replacement and reloads only after persistence succeeds", async () => {
  const ui = setup();
  await ui.elements["ai-use-whole"].fire("click");
  await ui.elements["ai-generate"].fire("click");
  ui.elements["ai-proposal"].value = "Reviewed.";
  await ui.elements["ai-accept"].fire("click");
  assert.equal(ui.requests[1].data.text, "Reviewed.");
  assert.deepEqual(ui.events, ["editor:saved"]);
  assert.deepEqual(ui.redirects, ["/editor/"]);
});

test("failed requests keep the original and display errors", async () => {
  const ui = setup({response: () => ({ok: false, json: async () => ({error: "Provider unavailable"})})});
  await ui.elements["ai-use-whole"].fire("click");
  await ui.elements["ai-generate"].fire("click");
  assert.equal(ui.body.value, "Intro 😀. Selected tail.");
  assert.match(ui.elements["ai-status"].textContent, /Provider unavailable/);
  assert.equal(ui.elements["ai-status"].attributes.role, "alert");
  assert.equal(ui.elements["ai-generate"].disabled, false);
});

test("discard persists the decision and leaves the working buffer alone", async () => {
  const ui = setup();
  await ui.elements["ai-use-whole"].fire("click");
  await ui.elements["ai-generate"].fire("click");
  await ui.elements["ai-discard"].fire("click");
  assert.equal(ui.requests[1].url, "/discard/");
  assert.equal(ui.elements["ai-result"].hidden, true);
  assert.equal(ui.body.value, "Intro 😀. Selected tail.");
});

test("saved proposals recover their Unicode selection without another provider request", async () => {
  const saved = {
    body: "Intro 😀. Selected tail.", title: "Title", expected: "1",
    start: 9, end: 17, text: "Recovered.", instruction: "Improve.", context: "",
    accept_url: "/saved/accept/", discard_url: "/saved/discard/",
  };
  const ui = setup({saved});
  assert.equal(ui.elements["ai-original"].value, "Selected");
  assert.equal(ui.elements["ai-proposal"].value, "Recovered.");
  assert.equal(ui.requests.length, 0);
  await ui.elements["ai-accept"].fire("click");
  assert.equal(ui.requests[0].url, "/saved/accept/");
  assert.equal(ui.requests[0].data.text, "Recovered.");
});

test("saved proposals with changed source remain visible but cannot be accepted", async () => {
  const ui = setup({saved: {
    body: "An older working buffer.", title: "Title", expected: "1",
    start: 0, end: 2, text: "Recovered.", instruction: "Improve.", context: "",
    accept_url: "/saved/accept/",
  }});
  assert.equal(ui.elements["ai-result"].hidden, false);
  assert.match(ui.elements["ai-status"].textContent, /Ausgangstext weicht ab/);
  await ui.elements["ai-accept"].fire("click");
  assert.equal(ui.requests.length, 0);
});

test("leaving warns about manually edited proposals until acceptance has persisted", async () => {
  const ui = setup();
  await ui.elements["ai-use-whole"].fire("click");
  await ui.elements["ai-generate"].fire("click");
  let warnings = 0;
  const event = {preventDefault: () => { warnings++; }};
  ui.windowListeners.beforeunload(event);
  assert.equal(warnings, 0);
  ui.elements["ai-proposal"].value = "Reviewed.";
  ui.windowListeners.beforeunload(event);
  assert.equal(warnings, 1);
  await ui.elements["ai-accept"].fire("click");
  ui.windowListeners.beforeunload(event);
  assert.equal(warnings, 1);
});
