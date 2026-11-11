"""Read-only provisioned files and explicit immutable source registration."""

import logging
import os
import stat
from contextlib import ExitStack
from dataclasses import dataclass
from itertools import islice
from pathlib import Path, PurePosixPath

from django.conf import settings
from django.db import transaction

from .importers.base import ImportFailure, MAX_UPLOAD_BYTES
from .importers.registry import DocumentImporterRegistry
from .models import SourceRegistration
from .services import register_bytes

logger = logging.getLogger(__name__)
MAX_ENTRIES = 5000


@dataclass(frozen=True)
class ProvisionedFile:
    relative_path: str
    domain: str
    format: str
    size: int
    registration: SourceRegistration | None = None


def data_root() -> Path:
    return Path(settings.WISSENSWIKI["MARKDOWN_DATA"]["root"]).expanduser()


def _relative(value: str) -> PurePosixPath:
    parts = value.split("/")
    if (
        len(parts) < 3 or len(value) > 1000 or len(parts[0]) > 150
        or any(not part or part.startswith(".") or "\\" in part or "\x00" in part for part in parts)
    ):
        raise ImportFailure("Quelle muss unter DOMAIN/FILEFORMAT/DATEI liegen; keine versteckten oder relativen Pfade.")
    path = PurePosixPath(value)
    DocumentImporterRegistry().find_importer(path.name)
    aliases = {"markdown": "md", "htm": "html", "yml": "yaml"}
    suffix = aliases.get(path.suffix.lower()[1:], path.suffix.lower()[1:])
    if aliases.get(parts[1].lower(), parts[1].lower()) != suffix:
        raise ImportFailure("Dateiendung und FILEFORMAT-Verzeichnis passen nicht zusammen.")
    return path


def provisioned_files() -> list[ProvisionedFile]:
    """Inspect names and sizes only; GET never registers files or reads original bytes."""
    root = data_root()
    if root.is_symlink():
        raise ImportFailure("Datenwurzel darf kein Symlink sein; bitte das tatsächliche Verzeichnis konfigurieren.")
    if not root.exists():
        return []
    registrations = {}
    for item in SourceRegistration.objects.select_related("source").defer("source__data").order_by("registered_at"):
        registrations[item.relative_path] = item
    result = []
    pending = [(root, "")]
    count = 0
    formats = {suffix[1:] for suffix in DocumentImporterRegistry().extensions}
    try:
        while pending:
            directory, prefix = pending.pop()
            with os.scandir(directory) as stream:
                entries = list(islice(stream, MAX_ENTRIES + 1))
            count += len(entries)
            if count > MAX_ENTRIES:
                raise ImportFailure("Bereitstellung enthält mehr als 5000 Einträge; Datenwurzel bitte aufteilen.")
            for entry in sorted(entries, key=lambda item: item.name):
                if entry.name.startswith(".") or entry.is_symlink():
                    continue
                relative = prefix + entry.name
                if entry.is_dir(follow_symlinks=False):
                    depth = len(PurePosixPath(relative).parts)
                    if depth == 3 and entry.name == "_extractions":
                        continue
                    if depth == 2 and entry.name.lower() not in formats:
                        continue
                    if depth > 20:
                        raise ImportFailure("Bereitstellungsbaum ist zu tief (maximal 20 Verzeichnisse).")
                    pending.append((Path(entry.path), relative + "/"))
                elif entry.is_file(follow_symlinks=False):
                    try:
                        path = _relative(relative)
                    except ImportFailure:
                        continue
                    result.append(ProvisionedFile(
                        relative, path.parts[0], path.parts[1],
                        entry.stat(follow_symlinks=False).st_size, registrations.get(relative),
                    ))
    except OSError as error:
        logger.warning("Cannot inspect provisioned sources (%s).", type(error).__name__)
        raise ImportFailure("Bereitgestellte Quellen sind nicht lesbar; Dateirechte prüfen.") from error
    return sorted(result, key=lambda item: item.relative_path)


def _read_original(relative: PurePosixPath) -> bytes:
    """Use directory descriptors so symlinks cannot redirect a registration."""
    try:
        with ExitStack() as stack:
            directory = os.open(data_root(), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            stack.callback(os.close, directory)
            for part in relative.parts[:-1]:
                directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
                stack.callback(os.close, directory)
            descriptor = os.open(
                relative.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory,
            )
            with os.fdopen(descriptor, "rb") as stream:
                before = os.fstat(stream.fileno())
                if not stat.S_ISREG(before.st_mode) or not 0 < before.st_size <= MAX_UPLOAD_BYTES:
                    raise ImportFailure("Quelle muss eine reguläre Datei mit 1 Byte bis 10 MiB sein.")
                raw = stream.read(MAX_UPLOAD_BYTES + 1)
                after = os.fstat(stream.fileno())
                current = os.stat(relative.name, dir_fd=directory, follow_symlinks=False)
                signature = lambda info: (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
                if signature(before) != signature(after) or signature(after) != signature(current):
                    raise ImportFailure("Quelle wurde während der Registrierung geändert; bitte erneut versuchen.")
                return raw
    except OSError as error:
        logger.warning("Cannot register provisioned source (%s).", type(error).__name__)
        raise ImportFailure("Quelle nicht lesbar oder Symlink; nur reguläre Dateien innerhalb der Datenwurzel erlaubt.") from error


@transaction.atomic
def register_provisioned(relative_path: str, user):
    """Pin these bytes, not a mutable filesystem location, as the imported source."""
    relative = _relative(relative_path)
    if "_extractions" in relative.parts:
        raise ImportFailure("Unveränderliche Extraktionen dürfen nicht erneut als bereitgestellte Quellen registriert werden.")
    raw = _read_original(relative)
    source, created = register_bytes(relative.name, raw, relative.parts[0], user)
    SourceRegistration.objects.get_or_create(
        source=source, relative_path=relative_path, defaults={"registered_by": user},
    )
    return source, created
