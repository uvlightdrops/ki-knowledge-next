"""Synchronous import pipeline and revision operations with conflict detection."""

import hashlib
import logging
import tempfile
from pathlib import Path

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .importers.base import ImportFailure, MAX_UPLOAD_BYTES
from .importers.registry import PIPELINE_VERSION, DocumentImporterRegistry
from .markdown_document import split_markdown
from .models import ContentDocument, ContentRevision, ExtractionSnapshot, ImportRun, SourceAsset

logger = logging.getLogger(__name__)


class RevisionConflict(ValueError):
    """The submitted revision is no longer the current revision."""


def import_upload(upload, domain: str, user) -> tuple[ImportRun, bool]:
    """Register original bytes once per domain and process with a versioned adapter."""
    filename = Path(upload.name).name
    DocumentImporterRegistry().find_importer(filename)
    if not domain or len(domain) > 150:
        raise ImportFailure("Bitte eine gültige Domäne auswählen.")
    if upload.size > MAX_UPLOAD_BYTES:
        raise ImportFailure("Datei überschreitet 10 MiB. Bitte aufteilen.")
    data = upload.read(MAX_UPLOAD_BYTES + 1)
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise ImportFailure("Datei muss zwischen 1 Byte und 10 MiB groß sein.")
    source, _ = register_bytes(filename, data, domain, user)
    return extract_source(source, user)


def register_bytes(filename: str, data: bytes, domain: str, user) -> tuple[SourceAsset, bool]:
    """Capture original bytes without extracting or publishing anything."""
    DocumentImporterRegistry().find_importer(filename)
    if not domain or len(domain) > 150:
        raise ImportFailure("Bitte eine gültige Domäne auswählen.")
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise ImportFailure("Datei muss zwischen 1 Byte und 10 MiB groß sein.")
    return SourceAsset.objects.get_or_create(
        domain=domain, sha256=hashlib.sha256(data).hexdigest(), format=Path(filename).suffix.lower(),
        defaults={"filename": filename, "data": data, "size": len(data), "uploaded_by": user},
    )


def extract_source(source: SourceAsset, user) -> tuple[ImportRun, bool]:
    """Start this pipeline version once for an already registered source."""
    importer = DocumentImporterRegistry().find_importer(source.filename)
    run, created = ImportRun.objects.get_or_create(
        source=source, pipeline_version=PIPELINE_VERSION, defaults={"adapter": importer.name},
    )
    if created:
        process_run(run, user)
    return run, created


def process_run(run: ImportRun, user, *, job=None) -> None:
    """Claim a pending/failed run; extraction failure never creates partial drafts."""
    if run.pipeline_version != PIPELINE_VERSION:
        raise RevisionConflict(
            "Diese Pipeline-Version ist nicht mehr verfügbar. Die registrierte Quelle mit der aktuellen Pipeline zerlegen.",
        )
    claimed = ImportRun.objects.filter(
        pk=run.pk, status__in=[ImportRun.Status.PENDING, ImportRun.Status.FAILED],
    ).update(status=ImportRun.Status.PROCESSING, attempts=F("attempts") + 1, error="", finished_at=None,
             processing_job=job)
    if not claimed:
        raise RevisionConflict("Dieser Import läuft bereits oder ist abgeschlossen.")
    try:
        with tempfile.TemporaryDirectory(prefix="ki-next-import-") as directory:
            path = Path(directory) / Path(run.source.filename).name
            original = bytes(run.source.data)
            if len(original) != run.source.size or hashlib.sha256(original).hexdigest() != run.source.sha256:
                raise ImportFailure("Gespeicherte Originalquelle stimmt nicht mit ihrer Prüfsumme überein.")
            path.write_bytes(original)
            result = DocumentImporterRegistry().extract(path)
            for item in result.documents:
                # All adapters cross the same Markdown/header boundary before persistence.
                parsed = split_markdown(item.yaml_header + item.body)
                item.body, item.yaml_header = parsed.body, parsed.header
                if not item.body.strip():
                    raise ImportFailure("Extrahiertes Markdown enthält nur Metadaten, keinen Text.")
        with transaction.atomic():
            for item in result.documents:
                document = ContentDocument.objects.create(
                    run=run, title=item.title, source_locator=item.locator, revision_number=1,
                )
                ExtractionSnapshot.objects.create(
                    document=document, title=item.title, markdown=item.yaml_header + item.body,
                    metadata=item.metadata,
                )
                revision = ContentRevision.objects.create(
                    document=document, number=1, title=item.title, body=item.body,
                    yaml_header=item.yaml_header, cause="extraction",
                    metadata=item.metadata, created_by=user,
                )
                from .graph_services import index_revision
                index_revision(revision)
            ImportRun.objects.filter(pk=run.pk).update(
                status=ImportRun.Status.SUCCEEDED, warnings=result.warnings, finished_at=timezone.now(),
                processing_job=None,
            )
    except (ImportFailure, OSError, ValidationError) as error:
        logger.warning("Import %s failed: %s", run.pk, error)
        ImportRun.objects.filter(pk=run.pk).update(
            status=ImportRun.Status.FAILED, error=str(error), finished_at=timezone.now(),
            processing_job=None,
        )
    run.refresh_from_db()
    if job is None and run.status == ImportRun.Status.SUCCEEDED:
        from .jobs import enqueue_run
        enqueue_run(run, user)


@transaction.atomic
def revise(document: ContentDocument, *, expected: int, title: str, body: str, user) -> ContentRevision:
    if split_markdown(body).header:
        raise ImportFailure("YAML-Header sind Dokumentmetadaten und gehören nicht in den Texteditor.")
    if not title.strip() or len(title) > 255 or not body.strip() or len(body) > 2_000_000:
        raise ImportFailure("Titel und Markdown müssen ausgefüllt sein und innerhalb der Importgrenzen liegen.")
    changed = ContentDocument.objects.filter(pk=document.pk, revision_number=expected).update(
        revision_number=F("revision_number") + 1, title=title,
    )
    if not changed:
        raise RevisionConflict("Inhalt wurde inzwischen geändert. Bitte neu laden und Änderungen vergleichen.")
    previous = document.revisions.get(number=expected)
    revision = ContentRevision.objects.create(
        document=document, number=expected + 1, title=title, body=body,
        yaml_header=previous.yaml_header, metadata=previous.metadata, parent=previous,
        cause="edit", created_by=user,
    )
    from .graph_services import index_revision
    index_revision(revision)
    document.refresh_from_db()
    return revision


@transaction.atomic
def restore(document: ContentDocument, *, expected: int, number: int, user) -> ContentRevision:
    """Append a historical state; never move the head backwards or change approval."""
    historical = document.revisions.filter(number=number).first()
    if historical is None:
        raise RevisionConflict("Diese Revision existiert nicht.")
    changed = ContentDocument.objects.filter(pk=document.pk, revision_number=expected).update(
        revision_number=F("revision_number") + 1, title=historical.title,
    )
    if not changed:
        raise RevisionConflict("Inhalt wurde inzwischen geändert. Bitte neu laden und vergleichen.")
    previous = document.revisions.get(number=expected)
    revision = ContentRevision.objects.create(
        document=document, number=expected + 1, title=historical.title, body=historical.body,
        yaml_header=historical.yaml_header, metadata=historical.metadata, parent=previous,
        restored_from=historical, cause="restore", created_by=user,
    )
    from .graph_services import index_revision
    index_revision(revision)
    document.refresh_from_db()
    return revision


@transaction.atomic
def approve(document: ContentDocument, *, expected: int, user) -> None:
    if not user.has_perm("content.publish_content"):
        raise PermissionDenied("Keine Berechtigung zur Freigabe.")
    revision = document.revisions.filter(number=expected).first()
    if revision is None:
        raise RevisionConflict("Diese Revision existiert nicht.")
    changed = ContentDocument.objects.filter(pk=document.pk, revision_number=expected).update(
        approved_revision=revision, approved_by=user, approved_at=timezone.now(),
    )
    if not changed:
        raise RevisionConflict("Nur die aktuelle Revision kann freigegeben werden. Bitte neu laden.")
    document.refresh_from_db()
