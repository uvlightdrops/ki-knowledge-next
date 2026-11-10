"""Synthetic format fixtures; no third-party document contents."""

import io
from zipfile import ZipFile

import pytest
from docx import Document
from openpyxl import Workbook
from pypdf import PdfWriter

from knext.content.importers.base import ImportFailure
from knext.content.importers.registry import DocumentImporterRegistry
from knext.content.rendering import render_markdown


def extract(tmp_path, name, data):
    path = tmp_path / name
    path.write_bytes(data.encode() if isinstance(data, str) else data)
    return DocumentImporterRegistry().extract(path)


def test_markdown_preserves_structure_and_document_metadata(tmp_path):
    result = extract(tmp_path, "notes.MD", "---\nproject: next\ncreated: 2026-11-10\n---\n# Topic\n\n## Part\n\nText.")
    document = result.documents[0]
    assert document.title == "Topic"
    assert document.metadata == {"project": "next", "created": "2026-11-10"}
    assert document.body.startswith("# Topic") and "## Part" in document.body


@pytest.mark.parametrize("name,data", [
    ("bad.md", "---\nproject: [\n---\ntext"), ("bad.md", "---\nproject: x"),
    ("bad.md", "---\n- a\n---\ntext"), ("bad.json", "{"), ("bad.yaml", "a: ["),
    ("bad.md", "---\n[]\n---\ntext"), ("bad.md", "---\nfalse\n---\ntext"),
    ("bad.txt", b"\xff"), ("bad.txt", b"\0binary"), ("empty.txt", " \n"),
    ("bad.pdf", b"broken"), ("bad.docx", b"broken"), ("bad.xlsx", b"broken"),
    ("bad.epub", b"broken"), ("bad.exe", b"binary"),
    ("empty.html", "<html><script>hidden</script></html>"),
])
def test_invalid_files_fail_explicitly(tmp_path, name, data):
    with pytest.raises(ImportFailure):
        extract(tmp_path, name, data)


def test_text_and_html_do_not_activate_markup(tmp_path):
    result = extract(tmp_path, "notes.txt", "```\n# Literal\n<script>no</script>")
    html = render_markdown(result.documents[0].body)
    assert "<h1>" not in html and "&lt;script&gt;" in html
    result = extract(tmp_path, "page.html", "<title>Page</title><nav>Nav</nav><main><h1>Heading</h1><p>Body</p><script>bad</script></main>")
    assert result.documents[0].title == "Page"
    assert "Body" in result.documents[0].body and "bad" not in result.documents[0].body
    assert "Nav" not in result.documents[0].body
    assert result.warnings


def test_csv_json_yaml_are_readable_and_preserve_values(tmp_path):
    result = extract(tmp_path, "table.csv", 'Name;Value\n"Alpha;Beta";0\n')
    assert result.documents[0].metadata["delimiter"] == ";"
    assert '["Alpha;Beta", "0"]' in result.documents[0].body
    result = extract(tmp_path, "table.tsv", "Name\tValue\nItem\t0\n")
    assert result.documents[0].metadata["rows"] == 2
    for name, value in [("object.json", '{"value": 0}'), ("object.yml", "value: 0")]:
        result = extract(tmp_path, name, value)
        assert '"value": 0' in result.documents[0].body


def test_docx_preserves_heading_and_tables_with_warning(tmp_path):
    document = Document()
    document.add_heading("Heading", 1)
    document.add_paragraph("Paragraph")
    table = document.add_table(rows=1, cols=2)
    table.cell(0, 0).text = "Item"
    table.cell(0, 1).text = "0"
    output = io.BytesIO()
    document.save(output)
    result = extract(tmp_path, "word.docx", output.getvalue())
    assert "# Heading" in result.documents[0].body
    assert '["Item", "0"]' in result.documents[0].body
    assert result.warnings


def test_xlsx_preserves_zero_false_and_sheet_provenance(tmp_path):
    book = Workbook()
    sheet = book.active
    sheet.title = "Data"
    sheet.append(["Name", "Value", "Enabled"])
    sheet.append(["Item", 0, False])
    book.create_sheet("Other").append(["Another"])
    output = io.BytesIO()
    book.save(output)
    result = extract(tmp_path, "data.xlsx", output.getvalue())
    assert len(result.documents) == 2
    assert result.documents[0].locator == "Data"
    assert '["Item", 0, false]' in result.documents[0].body
    assert result.warnings


def test_image_only_pdf_requires_ocr_instead_of_success(tmp_path):
    writer = PdfWriter()
    writer.add_blank_page(width=100, height=100)
    output = io.BytesIO()
    writer.write(output)
    with pytest.raises(ImportFailure, match="OCR"):
        extract(tmp_path, "scan.pdf", output.getvalue())


def test_pdf_text_keeps_page_locator(tmp_path):
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject

    writer = PdfWriter()
    page = writer.add_blank_page(width=400, height=400)
    font = DictionaryObject({
        NameObject("/Type"): NameObject("/Font"), NameObject("/Subtype"): NameObject("/Type1"),
        NameObject("/BaseFont"): NameObject("/Helvetica"),
    })
    page[NameObject("/Resources")] = DictionaryObject({
        NameObject("/Font"): DictionaryObject({NameObject("/F1"): writer._add_object(font)}),
    })
    stream = DecodedStreamObject()
    stream.set_data(b"BT /F1 14 Tf 50 350 Td (Synthetic PDF text) Tj ET")
    page[NameObject("/Contents")] = writer._add_object(stream)
    output = io.BytesIO()
    writer.write(output)
    result = extract(tmp_path, "text.pdf", output.getvalue())
    assert "Synthetic PDF text" in result.documents[0].body
    assert "## Seite 1" in result.documents[0].body
    assert result.documents[0].metadata["pages"] == 1


def test_archive_expansion_limit_is_enforced(tmp_path):
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("big.xml", b" " * (16 * 1024 * 1024 + 1))
    with pytest.raises(ImportFailure, match="16 MiB"):
        extract(tmp_path, "large.docx", output.getvalue())


def test_epub_keeps_reading_order_and_chapter_locations(tmp_path):
    output = io.BytesIO()
    with ZipFile(output, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr("META-INF/container.xml", '<container><rootfiles><rootfile full-path="book.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        archive.writestr("book.opf", '''<package version="3.0" unique-identifier="id">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Book</dc:title>
<dc:identifier id="id">synthetic</dc:identifier></metadata><manifest>
<item id="a" href="a.xhtml" media-type="application/xhtml+xml"/>
<item id="b" href="b.xhtml" media-type="application/xhtml+xml"/>
</manifest><spine><itemref idref="b"/><itemref idref="a"/></spine></package>''')
        for letter in ("a", "b"):
            archive.writestr(f"{letter}.xhtml", f"<html><body><h1>{letter}</h1><p>Text.</p></body></html>")
    result = extract(tmp_path, "book.epub", output.getvalue())
    assert [item.locator for item in result.documents] == ["b.xhtml", "a.xhtml"]
    assert result.documents[0].metadata["book_title"] == "Book"
