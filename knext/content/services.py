"""Synchronous import pipeline and revision operations with conflict detection."""

import hashlib
import logging
import tempfile
from pathlib import Path

from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .importers.base import ImportFailure, MAX_UPLOAD_BYTES
from .importers.registry import PIPELINE_VERSION, DocumentImporterRegistry
from .models import ContentDocument, ContentRevision, ImportRun, SourceAsset

logger = logging.getLogger(__name__)


class RevisionConflict(ValueError):
    """The submitted revision is no longer the current revision."""


def import_upload(upload, domain: str, user) -> tuple[ImportRun, bool]:
    """Register original bytes once per domain and process with a versioned adapter."""
    registry = DocumentImporterRegistry()
    filename = Path(upload.name).name
    importer = registry.find_importer(filename)
    if not domain or len(domain) > 150:
        raise ImportFailure("Bitte eine gültige Domäne auswählen.")
    if upload.size > MAX_UPLOAD_BYTES:
        raise ImportFailure("Datei überschreitet 10 MiB. Bitte aufteilen.")
    data = upload.read(MAX_UPLOAD_BYTES + 1)
    if not data or len(data) > MAX_UPLOAD_BYTES:
        raise ImportFailure("Datei muss zwischen 1 Byte und 10 MiB groß sein.")
    source, _ = SourceAsset.objects.get_or_create(
        domain=domain, sha256=hashlib.sha256(data).hexdigest(),
        defaults={"filename": filename, "data": data, "size": len(data), "uploaded_by": user},
    )
    run, created = ImportRun.objects.get_or_create(
        source=source, pipeline_version=PIPELINE_VERSION, defaults={"adapter": importer.name},
    )
    if created:
        process_run(run, user)
    return run, created


def process_run(run: ImportRun, user) -> None:
    """Claim a pending/failed run; extraction failure never creates partial drafts."""
    claimed = ImportRun.objects.filter(
        pk=run.pk, status__in=[ImportRun.Status.PENDING, ImportRun.Status.FAILED],
    ).update(status=ImportRun.Status.PROCESSING, attempts=F("attempts") + 1, error="", finished_at=None)
    if not claimed:
        raise RevisionConflict("Dieser Import läuft bereits oder ist abgeschlossen.")
    try:
        with tempfile.TemporaryDirectory(prefix="ki-next-import-") as directory:
            path = Path(directory) / Path(run.source.filename).name
            path.write_bytes(bytes(run.source.data))
            result = DocumentImporterRegistry().extract(path)
    except (ImportFailure, OSError) as error:
        logger.warning("Import %s failed: %s", run.pk, error)
        ImportRun.objects.filter(pk=run.pk).update(
            status=ImportRun.Status.FAILED, error=str(error), finished_at=timezone.now(),
        )
    else:
        with transaction.atomic():
            for item in result.documents:
                document = ContentDocument.objects.create(
                    run=run, title=item.title, source_locator=item.locator, revision_number=1,
                )
                ContentRevision.objects.create(
                    document=document, number=1, title=item.title, body=item.body,
                    metadata=item.metadata, created_by=user,
                )
            ImportRun.objects.filter(pk=run.pk).update(
                status=ImportRun.Status.SUCCEEDED, warnings=result.warnings, finished_at=timezone.now(),
            )
    run.refresh_from_db()


@transaction.atomic
def revise(document: ContentDocument, *, expected: int, title: str, body: str, user) -> ContentRevision:
    changed = ContentDocument.objects.filter(pk=document.pk, revision_number=expected).update(
        revision_number=F("revision_number") + 1, title=title,
    )
    if not changed:
        raise RevisionConflict("Inhalt wurde inzwischen geändert. Bitte neu laden und Änderungen vergleichen.")
    previous = document.revisions.get(number=expected)
    revision = ContentRevision.objects.create(
        document=document, number=expected + 1, title=title, body=body,
        metadata=previous.metadata, created_by=user,
    )
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
