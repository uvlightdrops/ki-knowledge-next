"""Source-preserving heading extraction for document-level Markdown outlines."""

import re
from dataclasses import dataclass

from .importers.base import ImportFailure


@dataclass(frozen=True)
class HeadingBlock:
    title: str
    explicit_id: str
    level: int
    start_line: int
    end_line: int
    body: str
    parent: int | None


def _headings(lines: list[str]) -> list[tuple[int, int, str]]:
    headings = []
    fence = None
    html_end = None
    text_lines = set()
    in_list = False
    for index, line in enumerate(lines):
        value = line.rstrip("\r\n")
        if html_end:
            if html_end.search(value):
                html_end = None
            continue
        if fence:
            if re.fullmatch(r" {0,3}" + re.escape(fence[0]) + "{" + str(len(fence)) + r",}[ \t]*", value):
                fence = None
            continue
        if in_list and (not value.strip() or value.startswith((" ", "\t"))):
            continue
        in_list = bool(re.match(r" {0,3}(?:[-+*]|\d+[.)])[ \t]+", value))
        if in_list:
            continue
        opening = re.match(r" {0,3}(`{3,}|~{3,})(.*)$", value)
        if opening and not (opening[1][0] == "`" and "`" in opening[2]):
            fence = opening[1]
            continue
        html = re.match(
            r" {0,3}(<!--|<(script|style|pre|div|table|section|details|article|ul|ol)(?:\s|>))",
            value, re.I,
        )
        if html:
            ending = re.compile("-->" if html[1] == "<!--" else rf"</{html[2]}\s*>", re.I)
            if not ending.search(value, html.end()):
                html_end = ending
            continue
        atx = re.match(r" {0,3}(#{1,6})(?:[ \t]+(.*?)|[ \t]*)$", value)
        if atx:
            title = re.sub(r"[ \t]+#+[ \t]*$", "", atx[2] or "").strip()
            headings.append((index, len(atx[1]), title))
        elif index - 1 in text_lines and re.fullmatch(r" {0,3}(=+|-+)[ \t]*", value):
            previous = lines[index - 1].rstrip("\r\n")
            headings.append((index - 1, 1 if value.lstrip().startswith("=") else 2, previous.strip()))
        elif value.strip() and not re.match(r"(?: {4}|\t| {0,3}[>#`~*-])", value):
            text_lines.add(index)
    return headings


def parse_outline(body: str) -> tuple[str, list[HeadingBlock]]:
    """Return intro and direct section slices; ignore fenced/indented code."""
    lines = body.splitlines(keepends=True)
    headings = _headings(lines)
    # A leading H1 is the document title, not a second resource for the document.
    if headings and headings[0][1] == 1 and not "".join(lines[:headings[0][0]]).strip():
        headings = headings[1:]
    if len(headings) > 5000:
        raise ImportFailure("Mehr als 5000 Abschnitte; bitte das Dokument vor dem Indexieren aufteilen.")
    intro = "".join(lines[:headings[0][0]]) if headings else body
    blocks, parents, ids = [], [], set()
    for index, (start, level, title) in enumerate(headings):
        match = re.search(r"\s+\[([A-Za-z0-9][A-Za-z0-9_-]*)\]\s*$", title)
        explicit_id = match[1] if match else ""
        if explicit_id and explicit_id in ids:
            raise ImportFailure(f"Doppelte Block-ID [{explicit_id}]; bitte innerhalb des Dokuments eindeutig machen.")
        if explicit_id:
            ids.add(explicit_id)
            title = title[:match.start()].strip()
        if len(title) > 255 or len(explicit_id) > 255:
            raise ImportFailure("Abschnittstitel oder Block-ID überschreitet 255 Zeichen.")
        while parents and blocks[parents[-1]].level >= level:
            parents.pop()
        end = headings[index + 1][0] if index + 1 < len(headings) else len(lines)
        blocks.append(HeadingBlock(
            title, explicit_id, level, start + 1, end, "".join(lines[start:end]),
            parents[-1] if parents else None,
        ))
        parents.append(index)
    return intro, blocks
