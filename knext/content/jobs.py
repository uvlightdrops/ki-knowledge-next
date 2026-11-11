"""Durable import jobs with serial, process-locked execution and explicit recovery."""

import fcntl
import hashlib
import logging
import os
import socket
import uuid
from contextlib import contextmanager

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .artifacts import materialize_run, materialize_source
from .importers.base import ImportFailure
from .importers.registry import PIPELINE_VERSION, DocumentImporterRegistry
from .inventory import _read_original, _relative, register_provisioned
from .models import ImportBatch, ImportJob, ImportRun, JobAttempt
from .services import RevisionConflict, process_run

logger = logging.getLogger(__name__)
MAX_BATCH = 100


def worker_running() -> bool:
    """Check the live OS lock, not the presence of a leftover lock file."""
    path = settings.VAR_DIR / "content-worker.lock"
    try:
        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
    except FileNotFoundError:
        return False
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_SH | fcntl.LOCK_NB)
        except BlockingIOError:
            return True
        return False
    finally:
        os.close(descriptor)


@transaction.atomic
def enqueue_paths(paths: list[str], kind: str, user) -> ImportBatch:
    paths = list(dict.fromkeys(paths))
    if kind not in {ImportJob.Kind.REGISTER, ImportJob.Kind.IMPORT} or not 0 < len(paths) <= MAX_BATCH:
        raise ImportFailure("Bitte 1 bis 100 Dateien und eine gültige Importaktion auswählen.")
    pinned = []
    for path in paths:
        relative = _relative(path)
        if "_extractions" in relative.parts:
            raise ImportFailure("Erzeugte Extraktionen sind keine neuen Importquellen.")
        raw = _read_original(relative)
        pinned.append((path, relative.parts[0], hashlib.sha256(raw).hexdigest()))
    batch = ImportBatch.objects.create(created_by=user, label=ImportJob.Kind(kind).label)
    for path, domain, digest in pinned:
        ImportJob.objects.create(
            batch=batch, kind=kind, domain=domain, relative_path=path,
            expected_sha256=digest, pipeline_version=PIPELINE_VERSION,
        )
    return batch


@transaction.atomic
def enqueue_sources(sources, kind: str, user) -> ImportBatch:
    sources = list(sources)
    if kind not in {ImportJob.Kind.EXTRACT, ImportJob.Kind.MATERIALIZE} or not 0 < len(sources) <= MAX_BATCH:
        raise ImportFailure("Bitte 1 bis 100 Quellen und eine gültige Verarbeitung auswählen.")
    batch = ImportBatch.objects.create(created_by=user, label=ImportJob.Kind(kind).label)
    for source in sources:
        ImportJob.objects.create(
            batch=batch, kind=kind, domain=source.domain, source=source,
            expected_sha256=source.sha256, pipeline_version=PIPELINE_VERSION,
        )
    return batch


@transaction.atomic
def enqueue_run(run: ImportRun, user) -> ImportBatch:
    batch = enqueue_sources([run.source], ImportJob.Kind.MATERIALIZE, user)
    batch.jobs.update(run=run, pipeline_version=run.pipeline_version)
    return batch


@contextmanager
def worker_lock():
    path = settings.VAR_DIR / "content-worker.lock"
    descriptor = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
    try:
        try:
            fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise ImportFailure("Ein Importworker läuft bereits. Nur einen Worker pro Datenbank starten.") from error
        yield
    finally:
        os.close(descriptor)


@transaction.atomic
def recover_interrupted() -> int:
    """Only call under the worker lock; never steal a live or synchronous import."""
    count = 0
    for job in ImportJob.objects.filter(status=ImportJob.Status.RUNNING):
        message = "Worker wurde unterbrochen. Wirkung prüfen und Auftrag ausdrücklich erneut starten."
        ImportRun.objects.filter(processing_job=job, status=ImportRun.Status.PROCESSING).update(
            status=ImportRun.Status.FAILED, error=message, processing_job=None, finished_at=timezone.now(),
        )
        job.history.filter(status="running").update(status="interrupted", error=message, finished_at=timezone.now())
        ImportJob.objects.filter(pk=job.pk).update(
            status=ImportJob.Status.FAILED, error=message, finished_at=timezone.now(),
        )
        logger.warning("Recovered interrupted import job %s.", job.pk)
        count += 1
    return count


@transaction.atomic
def claim_job(job_id=None):
    query = ImportJob.objects.filter(status=ImportJob.Status.QUEUED)
    if job_id:
        query = query.filter(pk=job_id)
    job = query.first()
    if job is None:
        return None
    if not ImportJob.objects.filter(pk=job.pk, status=ImportJob.Status.QUEUED).update(
        status=ImportJob.Status.RUNNING, attempts=F("attempts") + 1, error="", finished_at=None,
    ):
        return None
    job.refresh_from_db()
    JobAttempt.objects.create(job=job, number=job.attempts, worker=f"{socket.gethostname()}:{os.getpid()}")
    return job


def _source(job: ImportJob):
    if job.source_id:
        if job.source.sha256 != job.expected_sha256:
            raise ImportFailure("Registrierte Quellidentität stimmt nicht mit dem Jobfingerabdruck überein.")
        return job.source
    raw = _read_original(_relative(job.relative_path))
    if hashlib.sha256(raw).hexdigest() != job.expected_sha256:
        raise ImportFailure("Bereitgestellte Datei wurde seit Batch-Auswahl geändert; neu auswählen statt alte Bytes importieren.")
    # Registration checks the pinned hash again inside its own DB transaction.
    with transaction.atomic():
        source, _ = register_provisioned(job.relative_path, job.batch.created_by)
        if source.sha256 != job.expected_sha256:
            raise ImportFailure("Quelle wurde während der Jobregistrierung geändert; neue Auswahl erforderlich.")
        ImportJob.objects.filter(pk=job.pk).update(source=source)
    job.source = source
    return source


def execute_job(job: ImportJob) -> None:
    try:
        source = _source(job)
        original = materialize_source(source)
        if job.kind in {ImportJob.Kind.IMPORT, ImportJob.Kind.EXTRACT}:
            if job.pipeline_version != PIPELINE_VERSION:
                raise ImportFailure("Job verwendet eine nicht mehr verfügbare Pipeline; neuen Auftrag anlegen.")
            importer = DocumentImporterRegistry().find_importer(source.filename)
            run, _ = ImportRun.objects.get_or_create(
                source=source, pipeline_version=job.pipeline_version, defaults={"adapter": importer.name},
            )
            ImportJob.objects.filter(pk=job.pk).update(run=run)
            job.run = run
            if run.status != ImportRun.Status.SUCCEEDED:
                process_run(run, job.batch.created_by, job=job)
            if run.status != ImportRun.Status.SUCCEEDED:
                raise ImportFailure(run.error)
            paths = materialize_run(run)
        elif job.kind == ImportJob.Kind.REGISTER:
            paths = [original.relative_path]
        elif job.kind == ImportJob.Kind.MATERIALIZE:
            if job.run_id:
                paths = materialize_run(job.run)
            else:
                paths = [original.relative_path]
                for run in source.runs.filter(status=ImportRun.Status.SUCCEEDED):
                    paths += materialize_run(run)
        else:
            raise ImportFailure("Unbekannte Jobaktion.")
    except (ImportFailure, OSError, ValidationError, RevisionConflict) as error:
        logger.warning("Import job %s failed: %s", job.pk, error)
        _finish(job, ImportJob.Status.FAILED, str(error))
    else:
        _finish(job, ImportJob.Status.SUCCEEDED, result={"paths": sorted(set(paths))})


@transaction.atomic
def _finish(job: ImportJob, status: str, error: str = "", result=None) -> None:
    now = timezone.now()
    ImportJob.objects.filter(pk=job.pk, status=ImportJob.Status.RUNNING).update(
        status=status, error=error, result=result or {}, finished_at=now,
    )
    job.history.filter(number=job.attempts, status="running").update(status=status, error=error, finished_at=now)


def retry_job(job: ImportJob) -> None:
    if not ImportJob.objects.filter(pk=job.pk, status=ImportJob.Status.FAILED).update(
        status=ImportJob.Status.QUEUED, error="", finished_at=None,
    ):
        raise RevisionConflict("Nur fehlgeschlagene Jobs dürfen erneut eingereiht werden.")


def cancel_job(job: ImportJob) -> None:
    if not ImportJob.objects.filter(pk=job.pk, status=ImportJob.Status.QUEUED).update(
        status=ImportJob.Status.CANCELLED, finished_at=timezone.now(),
    ):
        raise RevisionConflict("Nur wartende Jobs können abgebrochen werden; laufende Wirkungen werden nicht zurückgerollt.")


@transaction.atomic
def cancel_jobs(ids: list[uuid.UUID], user, *, batch_id=None) -> int:
    """Cancel an explicit selection atomically, retaining job history."""
    query = ImportJob.objects.filter(pk__in=ids)
    if batch_id:
        query = query.filter(batch_id=batch_id)
    if query.count() != len(ids):
        raise ImportFailure("Mindestens ein ausgewählter Job existiert nicht oder gehört nicht zum Batch.")
    if not user.is_staff and query.exclude(batch__created_by=user).exists():
        raise PermissionError("Nur Auftraggeber oder Administratoren dürfen Jobs abbrechen.")
    count = query.filter(status=ImportJob.Status.QUEUED).update(
        status=ImportJob.Status.CANCELLED, finished_at=timezone.now(),
    )
    if count != len(ids):
        raise RevisionConflict("Mindestens ein Job ist nicht mehr wartend. Auswahl aktualisieren; es wurde nichts abgebrochen.")
    return count
