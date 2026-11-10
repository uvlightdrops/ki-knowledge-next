"""Strategy registry adapted from the legacy infosite importer."""

from pathlib import Path
from xml.etree.ElementTree import ParseError
from zipfile import BadZipFile

from defusedxml.common import DefusedXmlException
from docx.opc.exceptions import PackageNotFoundError
from lxml.etree import XMLSyntaxError
from openpyxl.utils.exceptions import InvalidFileException
from pypdf.errors import PyPdfError

from .base import DocumentImporter, Extraction, ImportFailure, MAX_DOCUMENTS, MAX_TEXT_CHARS, validate_archive
from .office import DocxImporter, EpubImporter, PdfImporter, SpreadsheetImporter
from .text import HtmlImporter, StructuredImporter, TextImporter

PIPELINE_VERSION = "content-import-v1"


class DocumentImporterRegistry:
    def __init__(self) -> None:
        self.importers = (
            TextImporter(), HtmlImporter(), StructuredImporter(), PdfImporter(),
            DocxImporter(), SpreadsheetImporter(), EpubImporter(),
        )

    @property
    def extensions(self) -> tuple[str, ...]:
        return tuple(suffix for importer in self.importers for suffix in importer.suffixes)

    def find_importer(self, filename: str) -> DocumentImporter:
        suffix = Path(filename).suffix.lower()
        for importer in self.importers:
            if suffix in importer.suffixes:
                return importer
        raise ImportFailure(f"Format {suffix or '(ohne Endung)'} nicht unterstützt.")

    def extract(self, path: Path) -> Extraction:
        importer = self.find_importer(path.name)
        try:
            if path.suffix.lower() in {".docx", ".xlsx", ".epub"}:
                validate_archive(path)
            result = importer.extract(path)
        except ImportFailure:
            raise
        except (PyPdfError, BadZipFile, ParseError, XMLSyntaxError, DefusedXmlException,
                PackageNotFoundError, InvalidFileException, OSError, ValueError, KeyError,
                RecursionError, NotImplementedError) as error:
            raise ImportFailure(f"{importer.name}: Datei beschädigt oder nicht unterstützt ({error}).") from error
        if not result.documents or len(result.documents) > MAX_DOCUMENTS:
            raise ImportFailure(f"Ergebnis muss 1 bis {MAX_DOCUMENTS} Dokumente enthalten.")
        if sum(len(item.body) for item in result.documents) > MAX_TEXT_CHARS:
            raise ImportFailure("Extrahierter Text überschreitet 2 Millionen Zeichen. Bitte Quelle aufteilen.")
        if any(not item.body.strip() for item in result.documents):
            raise ImportFailure("Mindestens ein Dokument enthält keinen Text.")
        return result
