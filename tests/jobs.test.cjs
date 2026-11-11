"use strict";
const assert = require("node:assert/strict");
const {test} = require("node:test");
const {readFileSync} = require("node:fs");
const vm = require("node:vm");
const source = readFileSync("knext/content/static/content/jobs.js", "utf8");

function setup({ok = true, redirected = false, missing = false, hidden = false, focused = false} = {}) {
  const status = {};
  const timers = [];
  const replaced = [];
  const requests = [];
  const listeners = {};
  const boxes = [{value: "first", checked: true}, {value: "second", checked: false}];
  const newBoxes = boxes.map(box => ({value: box.value, checked: false}));
  const blocks = ["job-progress", "job-results"].map(id => ({
    id, contains: () => focused && id === "job-results",
    replaceWith: node => replaced.push(node.id),
  }));
  const context = {
    document: {
      hidden, getElementById: () => status,
      addEventListener: (name, handler) => { listeners[name] = handler; },
      querySelectorAll: selector => selector === "[data-job-live]" ? blocks :
        selector.endsWith(":checked") ? boxes.filter(box => box.checked) : boxes,
    },
    window: {location: {href: "http://localhost/content/jobs/?status=queued"}, setTimeout: fn => timers.push(fn), confirm: () => true},
    fetch: async (url, options) => {
      requests.push({url, options});
      return {ok, redirected, text: async () => "<html>"};
    },
    DOMParser: class {parseFromString() {return {getElementById: id => missing ? null : {id, querySelectorAll: () => newBoxes}};}},
    AbortSignal: {timeout: () => "timeout"}, Date, console: {error: () => {}},
  };
  vm.runInNewContext(source, context);
  return {status, timers, replaced, requests, listeners, boxes, newBoxes, context};
}

test("polling preserves filters and refreshes progress and results", async () => {
  const ui = setup();
  await ui.timers.shift()();
  assert.deepEqual(ui.replaced, ["job-progress", "job-results"]);
  assert.match(ui.requests[0].url, /\?status=queued$/);
  assert.equal(ui.requests[0].options.cache, "no-store");
  assert.match(ui.status.textContent, /automatisch aktualisiert/);
  assert.equal(ui.timers.length, 1);
  assert.equal(ui.newBoxes[0].checked, true);
  assert.equal(ui.newBoxes[1].checked, false);
});

for (const failure of [{ok: false}, {redirected: true}, {missing: true}]) {
  test("poll failures preserve last stand and show an error " + JSON.stringify(failure), async () => {
    const ui = setup(failure);
    await ui.timers.shift()();
    assert.deepEqual(ui.replaced, []);
    assert.match(ui.status.textContent, /fehlgeschlagen/);
    assert.equal(ui.timers.length, 1);
  });
}

test("hidden tabs defer requests and focused controls are preserved", async () => {
  const hidden = setup({hidden: true});
  await hidden.timers.shift()();
  assert.equal(hidden.requests.length, 0);
  const focused = setup({focused: true});
  await focused.timers.shift()();
  assert.deepEqual(focused.replaced, ["job-progress"]);
});

test("select-all toggles eligible boxes and empty or declined cancellations do not submit", () => {
  const ui = setup();
  const click = {target: {closest: () => true}};
  ui.listeners.click(click);
  assert.ok(ui.boxes.every(box => box.checked));
  ui.listeners.click(click);
  assert.ok(ui.boxes.every(box => !box.checked));
  let prevented = false;
  const submit = {target: {id: "job-cancel-form"}, preventDefault: () => { prevented = true; }};
  ui.listeners.submit(submit);
  assert.equal(prevented, true);
  assert.match(ui.status.textContent, /zuerst/);
  ui.boxes[0].checked = true;
  ui.context.window.confirm = () => false;
  prevented = false;
  ui.listeners.submit(submit);
  assert.equal(prevented, true);
  ui.context.window.confirm = () => true;
  prevented = false;
  ui.listeners.submit(submit);
  assert.equal(prevented, false);
});
