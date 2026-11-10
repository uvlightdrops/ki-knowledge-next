"""Common bounded extraction contract."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol
from zipfile import BadZipFile, ZipFile

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_TEXT_CHARS = 2_000_000
MAX_DOCUMENTS = 300


class ImportFailure(ValueError):
    """A source cannot be processed; no draft should be created."""


@dataclass
class ExtractedDocument:
    title: str
    body: str
    locator: str = ""
    metadata: dict = field(default_factory=dict)


@dataclass
class Extraction:
    documents: list[ExtractedDocument]
    warnings: list[str] = field(default_factory=list)


class DocumentImporter(Protocol):
    name: str
    suffixes: tuple[str, ...]

    def extract(self, path: Path) -> Extraction: ...


def decode_text(path: Path) -> str:
    try:
        text = path.read_text(encoding="utf-8-sig")
    except UnicodeDecodeError as error:
        raise ImportFailure("Text muss UTF-8-kodiert sein. Bitte vor dem Import konvertieren.") from error
    if "\x00" in text:
        raise ImportFailure("Die Datei enthält binäre Daten statt Text.")
    return text


def validate_archive(path: Path) -> None:
    """Bound Office/EPUB containers before handing them to an XML/ZIP parser."""
    try:
        with ZipFile(path) as archive:
            members = archive.infolist()
            if len(members) > 2000 or sum(item.file_size for item in members) > 32 * 1024 * 1024:
                raise ImportFailure("Archiv zu groß: maximal 2000 Einträge und 32 MiB entpackt.")
            for item in members:
                if item.flag_bits & 1:
                    raise ImportFailure("Verschlüsselte Archive werden nicht unterstützt.")
                if item.file_size > 16 * 1024 * 1024:
                    raise ImportFailure("Ein Archiveintrag überschreitet 16 MiB.")
                if item.file_size > max(1, item.compress_size) * 200:
                    raise ImportFailure("Zu hohes Kompressionsverhältnis im Archiv.")
    except BadZipFile as error:
        raise ImportFailure("Kein gültiges ZIP-basiertes Dokument.") from error
