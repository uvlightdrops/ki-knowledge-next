"""PDF, Word, spreadsheet and EPUB adapters with explicit extraction limits."""

import json
from pathlib import Path

from docx import Document
from openpyxl import load_workbook
from pypdf import PdfReader

from .base import ExtractedDocument, Extraction, ImportFailure, MAX_TEXT_CHARS
from .epub_parser import parse_epub


class PdfImporter:
    name = "pdf-text-v1"
    suffixes = (".pdf",)

    def extract(self, path: Path) -> Extraction:
        reader = PdfReader(path)
        if reader.is_encrypted:
            raise ImportFailure("Verschlüsselte PDFs bitte vor dem Import entschlüsseln.")
        if len(reader.pages) > 200:
            raise ImportFailure("PDF hat mehr als 200 Seiten. Bitte aufteilen.")
        parts, empty, size = [], [], 0
        for number, page in enumerate(reader.pages, 1):
            text = page.extract_text() or ""
            size += len(text)
            if size > MAX_TEXT_CHARS:
                raise ImportFailure("PDF-Text überschreitet das Extraktionslimit.")
            if text.strip():
                parts.append(f"## Seite {number}\n\n{text.strip()}")
            else:
                empty.append(number)
        if not parts:
            raise ImportFailure("PDF enthält keinen extrahierbaren Text. OCR ist noch nicht angebunden.")
        warnings = ["PDF-Layout und Lesereihenfolge müssen manuell geprüft werden; keine OCR."]
        if empty:
            warnings.append("Seiten ohne Text: " + ", ".join(map(str, empty)))
        return Extraction([ExtractedDocument(path.stem, "\n\n".join(parts),
                                            metadata={"pages": len(reader.pages)})], warnings)


class DocxImporter:
    name = "docx-v1"
    suffixes = (".docx",)

    def extract(self, path: Path) -> Extraction:
        document = Document(path)
        parts = []
        for paragraph in document.paragraphs:
            style = paragraph.style.name if paragraph.style else ""
            prefix = ""
            if style.startswith("Heading ") and style[8:].isdigit():
                prefix = "#" * min(int(style[8:]), 6) + " "
            if paragraph.text.strip():
                parts.append(prefix + paragraph.text)
        for index, table in enumerate(document.tables, 1):
            rows = [json.dumps([cell.text for cell in row.cells], ensure_ascii=False) for row in table.rows]
            parts.append(f"## Tabelle {index}\n\n```text\n" + "\n".join(rows) + "\n```")
        title = document.core_properties.title or path.stem
        return Extraction([ExtractedDocument(title[:255], "\n\n".join(parts))],
                          ["DOCX: Bilder, Kommentare und Layout fehlen; Tabellen folgen nach dem Absatztext."])


class SpreadsheetImporter:
    name = "xlsx-v1"
    suffixes = (".xlsx",)

    def extract(self, path: Path) -> Extraction:
        book = load_workbook(path, read_only=True, data_only=True, keep_links=False)
        parts, count, size = [], 0, 0
        try:
            for sheet in book:
                rows = []
                if sheet.max_column and sheet.max_column > 100:
                    raise ImportFailure("XLSX: höchstens 100 Spalten pro Blatt.")
                for row in sheet.iter_rows(values_only=True):
                    count += 1
                    if count > 10_000:
                        raise ImportFailure("XLSX: höchstens 10.000 Zeilen insgesamt.")
                    line = json.dumps(list(row), ensure_ascii=False, default=str)
                    size += len(line)
                    if size > MAX_TEXT_CHARS:
                        raise ImportFailure("XLSX-Inhalt überschreitet das Extraktionslimit.")
                    rows.append(line)
                parts.append(ExtractedDocument(sheet.title, "```text\n" + "\n".join(rows) + "\n```",
                                               locator=sheet.title, metadata={"rows": len(rows)}))
        finally:
            book.close()
        return Extraction(parts, ["XLSX: gespeicherte Zellwerte; Formeln werden nicht berechnet, Layout fehlt."])


class EpubImporter:
    name = "epub-markdown-v1"
    suffixes = (".epub",)

    def extract(self, path: Path) -> Extraction:
        book = parse_epub(path)
        return Extraction([
            ExtractedDocument(chapter.title[:255], chapter.markdown, chapter.href, {
                "book_title": book.title, "authors": book.authors,
                "language": book.language, "chapter": index,
            }) for index, chapter in enumerate(book.chapters, 1)
        ], [*book.warnings,
            "EPUB: Kapitel einzeln übernommen. Kapitelübergreifende Links werden in der Vorschau nicht aufgelöst."])
