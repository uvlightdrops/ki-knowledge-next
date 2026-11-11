"""Bounded file-count inventory; never follows symlinks or reads source contents."""

import logging
import os
from collections import defaultdict
from dataclasses import dataclass
from itertools import islice

from .importers.base import ImportFailure
from .importers.registry import DocumentImporterRegistry
from .inventory import MAX_ENTRIES, data_root
from .models import FilesystemArtifact

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class CatalogFile:
    relative_path: str
    domain: str
    format: str
    area: str
    size: int
    artifact: FilesystemArtifact | None


def file_catalog() -> tuple[list[CatalogFile], list[str], list[dict]]:
    root = data_root()
    if root.is_symlink() or not root.is_dir():
        raise ImportFailure("Datenwurzel fehlt oder ist ein Symlink; Konfiguration prüfen.")
    artifacts = {item.relative_path: item for item in FilesystemArtifact.objects.select_related("source", "run")}
    formats = {suffix[1:] for suffix in DocumentImporterRegistry().extensions} | {"orig"}
    files, errors = [], []
    domains = set()
    counts = defaultdict(lambda: {"files": 0, "bytes": 0})
    pending = [(root, ())]
    visited = 0
    while pending:
        directory, parts = pending.pop()
        try:
            with os.scandir(directory) as stream:
                entries = list(islice(stream, MAX_ENTRIES + 1))
            visited += len(entries)
            if visited > MAX_ENTRIES:
                raise ImportFailure("Dateibestand enthält mehr als 5000 Einträge; Datenwurzel bitte aufteilen.")
            for entry in entries:
                if entry.name.startswith(".") or entry.is_symlink():
                    continue
                path = parts + (entry.name,)
                if entry.is_dir(follow_symlinks=False):
                    if len(path) == 1:
                        domains.add(path[0])
                    if len(path) == 2 and entry.name.lower() not in formats:
                        continue
                    if len(path) > 20:
                        raise ImportFailure("Dateibestand ist tiefer als 20 Verzeichnisse.")
                    pending.append((entry.path, path))
                elif len(path) >= 3 and entry.is_file(follow_symlinks=False):
                    area = "original" if path[1] == "orig" else (
                        "extraction" if len(path) > 3 and path[1:3] == ("md", "_extractions") else "provisioned"
                    )
                    relative = "/".join(path)
                    size = entry.stat(follow_symlinks=False).st_size
                    files.append(CatalogFile(relative, path[0], path[1], area, size, artifacts.get(relative)))
                    key = (path[0], area, path[1])
                    counts[key]["files"] += 1
                    counts[key]["bytes"] += size
        except OSError as error:
            logger.warning("File inventory incomplete at %s (%s).", "/".join(parts), type(error).__name__)
            errors.append(f"{'/'.join(parts) or 'Datenwurzel'} nicht vollständig lesbar; Dateirechte prüfen.")
    summary = [
        {"domain": domain, "area": area, "format": format_name, **value}
        for (domain, area, format_name), value in sorted(counts.items())
    ]
    summary += [
        {"domain": domain, "area": "provisioned", "format": "-", "files": 0, "bytes": 0}
        for domain in sorted(domains - {row["domain"] for row in summary})
    ]
    return sorted(files, key=lambda file: file.relative_path), errors, summary
