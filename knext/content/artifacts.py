"""Verifiable filesystem mirrors; originals and extraction bytes remain DB-authoritative."""

import hashlib
import json
import os
import stat
import uuid
from contextlib import ExitStack
from pathlib import Path, PurePosixPath

from django.conf import settings
from wissenswiki.config import registry

from .importers.base import ImportFailure
from .inventory import data_root
from .models import FilesystemArtifact, ImportRun, SourceAsset


def domain_folder(source: SourceAsset) -> str:
    from knext.domains import domain_aliases, domain_registry

    for name in domain_registry().domains:
        aliases = domain_aliases(name)
        if source.domain in aliases and len(aliases) > 1:
            folder = aliases[-1]
            break
    else:
        folder = source.domain
    if not folder or folder.startswith(".") or any(c in folder for c in "/\\\x00:"):
        raise ImportFailure("Quellendomäne hat keinen sicheren Datenbaum-Verzeichnisnamen.")
    return folder


def _write(relative: str, raw: bytes) -> str:
    """Publish a complete read-only file without ever replacing an existing target."""
    path = PurePosixPath(relative)
    if path.is_absolute() or any(p.startswith(".") or "\\" in p or "\x00" in p for p in path.parts):
        raise ImportFailure("Ungültiger Artefaktpfad.")
    with ExitStack() as stack:
        directory = os.open(data_root(), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        stack.callback(os.close, directory)
        for part in path.parts[:-1]:
            try:
                os.mkdir(part, dir_fd=directory)
            except FileExistsError:
                pass
            directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            stack.callback(os.close, directory)
        temporary = ".knext-" + uuid.uuid4().hex
        descriptor = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600, dir_fd=directory)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(raw)
                stream.flush()
                os.fchmod(stream.fileno(), 0o444)
                os.fsync(stream.fileno())
            try:
                os.link(temporary, path.name, src_dir_fd=directory, dst_dir_fd=directory, follow_symlinks=False)
            except FileExistsError:
                existing = os.open(path.name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
                with os.fdopen(existing, "rb") as stream:
                    info = os.fstat(stream.fileno())
                    if not stat.S_ISREG(info.st_mode) or info.st_size != len(raw) or stream.read(len(raw) + 1) != raw:
                        raise ImportFailure(f"Artefakt {relative} wurde verändert; kein Überschreiben. Administrativ prüfen.")
            os.fsync(directory)
        finally:
            os.unlink(temporary, dir_fd=directory)
    return hashlib.sha256(raw).hexdigest()


def _record(source: SourceAsset, relative: str, raw: bytes, kind: str, run=None) -> FilesystemArtifact:
    digest = _write(relative, raw)
    artifact, _ = FilesystemArtifact.objects.get_or_create(
        relative_path=relative,
        defaults={"source": source, "run": run, "sha256": digest, "size": len(raw), "kind": kind},
    )
    if (
        artifact.sha256 != digest or artifact.size != len(raw) or artifact.kind != kind
        or artifact.source_id != source.pk or artifact.run_id != (run.pk if run else None)
    ):
        raise ImportFailure("Artefaktindex und gespeicherte Bytes widersprechen sich; bitte administrativ prüfen.")
    return artifact


def read_artifact(artifact: FilesystemArtifact) -> bytes:
    with ExitStack() as stack:
        directory = os.open(data_root(), os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        stack.callback(os.close, directory)
        path = PurePosixPath(artifact.relative_path)
        parts = path.parts
        if path.is_absolute() or any(part.startswith(".") or "\\" in part or "\x00" in part for part in parts):
            raise ImportFailure("Ungültiger Artefaktpfad.")
        for part in parts[:-1]:
            directory = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=directory)
            stack.callback(os.close, directory)
        descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
        with os.fdopen(descriptor, "rb") as stream:
            info = os.fstat(stream.fileno())
            if not stat.S_ISREG(info.st_mode) or info.st_size != artifact.size:
                raise ImportFailure("Artefaktgröße stimmt nicht mit dem Index überein; Ablagejob erneut prüfen.")
            raw = stream.read(artifact.size + 1)
    if hashlib.sha256(raw).hexdigest() != artifact.sha256:
        raise ImportFailure("Artefakt-Prüfsumme ungültig; Datei wurde verändert, bitte administrativ prüfen.")
    return raw


def materialize_source(source: SourceAsset) -> FilesystemArtifact:
    raw = bytes(source.data)
    if source.sha256 != hashlib.sha256(raw).hexdigest() or source.size != len(raw):
        raise ImportFailure("Originalquelle stimmt nicht mit der gespeicherten Prüfsumme überein.")
    filename = Path(source.filename).name
    if filename != source.filename or filename.startswith(".") or "\\" in filename:
        raise ImportFailure("Originaldateiname ist für die Ablage nicht zulässig.")
    return _record(source, f"{domain_folder(source)}/orig/{source.pk}/{filename}", raw, "original")


def materialize_run(run: ImportRun) -> list[str]:
    if run.status != ImportRun.Status.SUCCEEDED:
        raise ImportFailure("Nur erfolgreich zerlegte Läufe können als Markdown abgelegt werden.")
    source = run.source
    folder = domain_folder(source)
    original = materialize_source(source)
    base = f"{folder}/md/_extractions/{run.pk}"
    relations = Path(settings.WISSENSWIKI["MARKDOWN_DATA"]["relations"]).expanduser()
    relations.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(relations, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        try:
            os.mkdir(folder, dir_fd=descriptor)
        except FileExistsError:
            pass
        directory = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=descriptor)
        os.close(directory)
    finally:
        os.close(descriptor)
    documents = []
    paths = [original.relative_path]
    for document in run.documents.select_related("extraction"):
        snapshot = document.extraction
        raw = snapshot.markdown.encode("utf-8")
        if hashlib.sha256(raw).hexdigest() != snapshot.sha256:
            raise ImportFailure("Extraktionssnapshot wurde verändert; Prüfsumme ungültig.")
        relative = f"{base}/{document.pk}.md"
        artifact = _record(source, relative, raw, "markdown", run)
        paths.append(relative)
        documents.append({
            "document": str(document.pk), "title": snapshot.title, "path": relative,
            "sha256": artifact.sha256, "locator": document.source_locator, "metadata": snapshot.metadata,
        })
    if not documents:
        raise ImportFailure("Erfolgreicher Lauf hat keine Extraktionssnapshots.")
    manifest = {
        "schema": "knext-extraction-v1", "run": str(run.pk), "pipeline": run.pipeline_version,
        "source": str(source.pk), "source_sha256": source.sha256,
        "original": original.relative_path, "documents": documents,
    }
    raw = (json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode()
    paths.append(_record(source, base + "/manifest.json", raw, "manifest", run).relative_path)
    registry.cache_clear()
    return paths
