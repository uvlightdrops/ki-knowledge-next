"""Text, Markdown, HTML and structured-data importers."""

import csv
import io
import json
import re
from pathlib import Path

import yaml
from bs4 import BeautifulSoup

from .base import ExtractedDocument, Extraction, ImportFailure, decode_text


class TextImporter:
    name = "text-v1"
    suffixes = (".md", ".markdown", ".txt")

    def extract(self, path: Path) -> Extraction:
        text = decode_text(path)
        metadata = {}
        if path.suffix.lower() in {".md", ".markdown"} and text.startswith("---\n"):
            match = re.match(r"\A---\n(.*?)\n---(?:\n|$)", text, re.DOTALL)
            if not match:
                raise ImportFailure("YAML-Header ist nicht mit --- abgeschlossen.")
            try:
                metadata = yaml.safe_load(match.group(1))
                if metadata is None:
                    metadata = {}
                if not isinstance(metadata, dict):
                    raise ImportFailure("Der YAML-Header muss ein Mapping sein.")
                metadata = json.loads(json.dumps(metadata, default=str, allow_nan=False))
            except (yaml.YAMLError, ValueError, TypeError, RecursionError) as error:
                raise ImportFailure("Ungültiger YAML-Header; bitte Struktur prüfen.") from error
            text = text[match.end():]
        if not text.strip():
            raise ImportFailure("Die Datei enthält keinen Inhalt.")
        heading = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        title = heading.group(1).strip() if heading else path.stem
        if path.suffix.lower() == ".txt":
            # A text file is not Markdown: keep literal headings, tags and links inert.
            longest = max((len(item) for item in re.findall(r"`+", text)), default=0)
            fence = "`" * max(3, longest + 1)
            text = f"{fence}\n{text}\n{fence}"
        return Extraction([ExtractedDocument(title[:255], text, metadata=metadata)])


class HtmlImporter:
    name = "html-v1"
    suffixes = (".html", ".htm")

    def extract(self, path: Path) -> Extraction:
        soup = BeautifulSoup(decode_text(path), "html.parser")
        title = soup.title.get_text(" ", strip=True) if soup.title else path.stem
        for node in soup.select("script, style, nav, header, footer, iframe, object, template"):
            node.decompose()
        container = soup.find("main") or soup.find("article") or soup.body or soup
        body = container.get_text("\n", strip=True)
        if not body:
            raise ImportFailure("HTML enthält keinen lesbaren Inhalt.")
        # HTML extraction is intentionally plain text; do not activate Markdown in it.
        fence = "`" * max(3, max((len(item) for item in re.findall(r"`+", body)), default=0) + 1)
        return Extraction([ExtractedDocument(title[:255], f"{fence}\n{body}\n{fence}")],
                          ["HTML-Layout, aktive Inhalte und eingebettete Medien wurden nicht übernommen."])


class StructuredImporter:
    name = "structured-v1"
    suffixes = (".csv", ".tsv", ".json", ".yaml", ".yml")

    def extract(self, path: Path) -> Extraction:
        text = decode_text(path)
        suffix = path.suffix.lower()
        if suffix in {".csv", ".tsv"}:
            return self._csv(path, text)
        try:
            value = json.loads(text) if suffix == ".json" else yaml.safe_load(text)
            body = json.dumps(value, ensure_ascii=False, indent=2, default=str, allow_nan=False)
        except (ValueError, TypeError, yaml.YAMLError, RecursionError) as error:
            raise ImportFailure("JSON/YAML konnte nicht gelesen werden; bitte Syntax prüfen.") from error
        return Extraction([ExtractedDocument(path.stem, f"```json\n{body}\n```")])

    def _csv(self, path: Path, text: str) -> Extraction:
        try:
            delimiter = "\t" if path.suffix.lower() == ".tsv" else csv.Sniffer().sniff(
                text[:8192], delimiters=",;\t|",
            ).delimiter
        except csv.Error:
            delimiter = ","
        try:
            rows = list(csv.reader(io.StringIO(text), delimiter=delimiter, strict=True))
        except csv.Error as error:
            raise ImportFailure("Die CSV-Tabelle ist ungültig.") from error
        if not rows or len(rows) > 10_000 or max(map(len, rows), default=0) > 100:
            raise ImportFailure("CSV muss 1 bis 10.000 Zeilen und höchstens 100 Spalten enthalten.")
        rendered = [json.dumps(row, ensure_ascii=False) for row in rows]
        return Extraction([ExtractedDocument(path.stem, "```text\n" + "\n".join(rendered) + "\n```",
                                            metadata={"rows": len(rows), "delimiter": delimiter})],
                          ["Tabellen werden als Zeilen mit geordneten Zellwerten übernommen, nicht semantisch aufgeteilt."])
