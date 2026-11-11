"use strict";
const assert = require("node:assert/strict");
const {test} = require("node:test");
const {readFileSync} = require("node:fs");
const vm = require("node:vm");
const source = readFileSync("knext/content/static/knext/batch.js", "utf8");

function element(extra = {}) {
  return {
    checked: false, listeners: {}, attributes: {},
    addEventListener(name, handler) { this.listeners[name] = handler; },
    setAttribute(name, value) { this.attributes[name] = value; },
    focus() { this.focused = true; },
    ...extra,
  };
}
function setup(count = 2) {
  const groups = ["file-batch", "source-batch"].map(id => {
    const status = element();
    const form = element({id, querySelector: () => status});
    const header = element();
    const boxes = Array.from({length: count}, () => element({form}));
    return {form, header, boxes, status};
  });
  vm.runInNewContext(source, {
    document: {
      querySelector: selector => groups.find(group => selector.includes(group.form.id)).header,
      querySelectorAll: selector => selector === "[data-batch-form]" ?
        groups.map(group => group.form) : groups.flatMap(group => [group.header, ...group.boxes]),
    },
  });
  return groups;
}

test("header selects only its own table and tracks partial selection", () => {
  const [files, sources] = setup();
  files.header.checked = true;
  files.header.listeners.change();
  assert.ok(files.boxes.every(box => box.checked));
  assert.ok(sources.boxes.every(box => !box.checked));
  files.boxes[0].checked = false;
  files.boxes[0].listeners.change();
  assert.equal(files.header.checked, false);
  assert.equal(files.header.indeterminate, true);
  assert.match(files.status.textContent, /1 von 2/);
  files.header.checked = false;
  files.header.listeners.change();
  assert.ok(files.boxes.every(box => !box.checked));
});

test("wrong-table submission stays on page with actionable feedback", () => {
  const [files, sources] = setup();
  files.boxes[0].checked = true;
  let prevented = false;
  sources.form.listeners.submit({preventDefault: () => { prevented = true; }});
  assert.equal(prevented, true);
  assert.match(sources.status.textContent, /zugehörigen Tabelle/);
  assert.equal(sources.status.attributes.role, "alert");
  assert.equal(sources.boxes[0].focused, true);
  prevented = false;
  files.form.listeners.submit({preventDefault: () => { prevented = true; }});
  assert.equal(prevented, false);
});

test("empty tables disable their header checkbox", () => {
  for (const group of setup(0)) {
    assert.equal(group.header.disabled, true);
    assert.equal(group.header.checked, false);
  }
});
