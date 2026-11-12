"use strict";
const assert = require("node:assert/strict");
const {test} = require("node:test");
const {readFileSync} = require("node:fs");
const css = readFileSync("knext/content/static/content/editor.css", "utf8");
const wide = css.slice(css.indexOf(".editor-wide{"));
const [base, tablet, desktop] = wide.split(/@media\(min-width:(?:751|1500)px\)\{/);

function declarations(source, selector) {
    const escaped = selector.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    const match = source.match(new RegExp(`${escaped}\\{([^}]+)\\}`));
    return Object.fromEntries((match?.[1] || "").split(";").filter(Boolean).map(item => {
        const [key, ...value] = item.split(":");
        return [key, value.join(":")];
    }));
}

function layout(width, network, preview, ai) {
    const root = ".editor-wide .editor-layout";
    const suffixes = ["", network ? ".network-open" : "", preview ? "" : ".preview-closed",
        ai ? ".ai-open" : "", ai && network ? ".ai-open.network-open" : "",
        ai && !preview ? ".ai-open.preview-closed" : "",
        network && !preview ? ".network-open.preview-closed" : "",
        ai && network && !preview ? ".ai-open.network-open.preview-closed" : ""];
    const values = {};
    for (const source of [base, ...(width >= 751 ? [tablet] : []), ...(width >= 1500 ? [desktop] : [])]) {
        // Declarations have equal specificity only for the same state selector.
        // Evaluate matching rules in their actual stylesheet order.
        const matching = [...new Set(suffixes)].map(suffix => root + suffix);
        const rules = [...source.matchAll(/([^{}]+)\{([^{}]+)\}/g)]
            .filter(rule => matching.includes(rule[1].trim()));
        for (const rule of rules) Object.assign(values, declarations(source, rule[1].trim()));
    }
    return {
        rows: [...values["grid-template-areas"].matchAll(/"([^"]+)"/g)].map(match => match[1].split(" ")),
        weights: [...values["--wide-columns"].matchAll(/minmax\(0,([\d.]+)fr\)/g)]
            .map(match => Number(match[1])),
    };
}

for (const width of [600, 750, 751, 1150, 1499, 1500, 1920, 2560]) {
    test(`wide editor places preview according to KI visibility at ${width}px for every panel state`, () => {
        for (const network of [false, true]) for (const preview of [false, true]) for (const ai of [false, true]) {
            const grid = layout(width, network, preview, ai);
            assert.ok(grid.rows.every(row => row.length === grid.weights.length));
            const cells = grid.rows.flat();
            assert.equal(cells.includes("network"), network);
            assert.equal(cells.includes("preview"), preview);
            assert.equal(cells.includes("ai"), ai);
            const writingRow = grid.rows.findIndex(row => row.includes("writing"));
            const column = grid.rows[writingRow].indexOf("writing");
            if (preview) {
                if (ai || width <= 750) {
                    assert.equal(grid.rows[writingRow + 1][column], "preview");
                    assert.equal(grid.rows[writingRow + 1].filter(cell => cell === "preview").length, 1);
                } else {
                    assert.equal(grid.rows[writingRow][column + 1], "preview");
                }
            }
            if (ai && width >= 751) {
                assert.equal(grid.rows[writingRow].indexOf("ai"), column + 1);
            }
        }
    });
}

test("original review gains at least 50 percent desktop width compared to the four-panel design", () => {
    assert.match(wide, /\.editor-wide #editor-layout\{grid-template-columns:var\(--wide-columns\)\}/);
    for (const width of [1500, 1920, 2560]) for (const network of [false, true]) {
        const grid = layout(width, network, true, true);
        const oldWeights = network ? [.7, 1.3, 1, 1.1] : [1.3, 1, 1.1];
        const available = width - 64; // Main horizontal padding: 2rem on each side.
        const contentWidth = weights => (
            (available - (weights.length - 1) * 16) * weights.at(-1)
            / weights.reduce((sum, weight) => sum + weight, 0) - 44
        ); // Panel horizontal padding and borders.
        assert.ok(contentWidth(grid.weights) >= contentWidth(oldWeights) * 1.5);
    }
    assert.match(wide, /\.editor-wide #ai-original\{white-space:pre-wrap;overflow-wrap:anywhere;overflow-x:hidden;max-height:37\.5vh\}/);
});
