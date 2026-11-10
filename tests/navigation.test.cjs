"use strict";
const assert = require("node:assert/strict");
const {test} = require("node:test");
const {readFileSync} = require("node:fs");
const {join} = require("node:path");
const vm = require("node:vm");

test("Escape closes the menu and restores focus; outside clicks close without stealing focus", () => {
    const listeners = {};
    let focused = 0;
    const inside = {};
    const menu = {
        open: true,
        contains: target => target === inside,
        querySelector: () => ({focus: () => { focused++; }})
    };
    vm.runInNewContext(readFileSync(join(__dirname,
        "../knext/content/static/knext/navigation.js"), "utf8"), {
        document: {querySelector: () => menu, addEventListener: (name, callback) => { listeners[name] = callback; }}
    });
    listeners.click({target: inside});
    assert.equal(menu.open, true);
    listeners.keydown({key: "Enter"});
    assert.equal(menu.open, true);
    listeners.keydown({key: "Escape"});
    assert.equal(menu.open, false);
    assert.equal(focused, 1);
    menu.open = true;
    listeners.click({target: {}});
    assert.equal(menu.open, false);
    assert.equal(focused, 1);
    listeners.keydown({key: "Escape"});
    assert.equal(focused, 1);
});
