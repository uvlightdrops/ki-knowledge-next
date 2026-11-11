"""Original sources, processing provenance and independently approved revisions."""

import hashlib
import uuid
from pathlib import Path

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .immutable import ImmutableModel
from .markdown_document import revision_digest, split_markdown


class ManagedDomain(models.Model):
    name = models.CharField("Domänenname", max_length=150, unique=True)
    folder = models.CharField("Verzeichnis", max_length=100, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class ActiveDomain(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField("Persönlich aktive Domäne", max_length=250, blank=True)


class SourceAsset(ImmutableModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.CharField("Domäne", max_length=150, db_index=True)
    filename = models.CharField("Originaldatei", max_length=255)
    format = models.CharField(max_length=20, default="")
    sha256 = models.CharField(max_length=64)
    data = models.BinaryField()
    size = models.PositiveIntegerField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["domain", "sha256", "format"], name="unique_source_format_in_domain"),
        ]

    def prepare_snapshot(self) -> None:
        self.format = Path(self.filename).suffix.lower()
        if self.size != len(self.data) or self.sha256 != hashlib.sha256(bytes(self.data)).hexdigest():
            raise ValidationError("Originalbytes, Größe und Prüfsumme stimmen nicht überein.")

    def __str__(self) -> str:
        return self.filename


class SourceRegistration(ImmutableModel):
    source = models.ForeignKey(SourceAsset, on_delete=models.PROTECT, related_name="registrations")
    relative_path = models.CharField(max_length=1000)
    registered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    registered_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "relative_path"], name="unique_source_registration"),
        ]


class ImportRun(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Bereit"
        PROCESSING = "processing", "Wird verarbeitet"
        SUCCEEDED = "succeeded", "Extrahiert"
        FAILED = "failed", "Fehlgeschlagen"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    source = models.ForeignKey(SourceAsset, on_delete=models.PROTECT, related_name="runs")
    pipeline_version = models.CharField(max_length=80)
    adapter = models.CharField(max_length=80)
    status = models.CharField(max_length=20, choices=Status, default=Status.PENDING)
    attempts = models.PositiveIntegerField(default=0)
    warnings = models.JSONField(default=list)
    error = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    processing_job = models.ForeignKey("ImportJob", on_delete=models.PROTECT, null=True, blank=True, related_name="+")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "pipeline_version"], name="unique_source_pipeline"),
        ]
        ordering = ["-created_at"]


class ImportBatch(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    label = models.CharField(max_length=255)

    class Meta:
        ordering = ["-created_at"]


class ImportJob(models.Model):
    class Kind(models.TextChoices):
        REGISTER = "register", "Original registrieren"
        IMPORT = "import", "Registrieren, zerlegen und ablegen"
        EXTRACT = "extract", "Quelle zerlegen und ablegen"
        MATERIALIZE = "materialize", "Dateisystem-Abbild sichern"

    class Status(models.TextChoices):
        QUEUED = "queued", "Wartend"
        RUNNING = "running", "Läuft"
        SUCCEEDED = "succeeded", "Abgeschlossen"
        FAILED = "failed", "Fehlgeschlagen"
        CANCELLED = "cancelled", "Abgebrochen"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    batch = models.ForeignKey(ImportBatch, on_delete=models.PROTECT, related_name="jobs")
    kind = models.CharField(max_length=20, choices=Kind)
    domain = models.CharField(max_length=150, db_index=True)
    relative_path = models.CharField(max_length=1000, blank=True)
    expected_sha256 = models.CharField(max_length=64, blank=True)
    source = models.ForeignKey(SourceAsset, on_delete=models.PROTECT, null=True, blank=True)
    run = models.ForeignKey(ImportRun, on_delete=models.PROTECT, null=True, blank=True)
    pipeline_version = models.CharField(max_length=80)
    status = models.CharField(max_length=20, choices=Status, default=Status.QUEUED, db_index=True)
    attempts = models.PositiveIntegerField(default=0)
    error = models.TextField(blank=True)
    result = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["created_at", "id"]


class JobAttempt(models.Model):
    job = models.ForeignKey(ImportJob, on_delete=models.PROTECT, related_name="history")
    number = models.PositiveIntegerField()
    worker = models.CharField(max_length=255)
    status = models.CharField(max_length=20, default="running")
    error = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["job", "number"], name="unique_job_attempt")]
        ordering = ["number"]


class FilesystemArtifact(models.Model):
    source = models.ForeignKey(SourceAsset, on_delete=models.PROTECT, related_name="artifacts")
    run = models.ForeignKey(ImportRun, on_delete=models.PROTECT, null=True, blank=True, related_name="artifacts")
    relative_path = models.CharField(max_length=1000, unique=True)
    sha256 = models.CharField(max_length=64)
    size = models.PositiveIntegerField()
    kind = models.CharField(max_length=20)
    created_at = models.DateTimeField(auto_now_add=True)


class ContentDocument(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    run = models.ForeignKey(ImportRun, on_delete=models.PROTECT, related_name="documents")
    source_locator = models.CharField(max_length=1000, blank=True)
    title = models.CharField("Titel", max_length=255)
    revision_number = models.PositiveIntegerField(default=0)
    approved_revision = models.ForeignKey(
        "ContentRevision", on_delete=models.PROTECT, null=True, blank=True, related_name="+",
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name="+",
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]
        permissions = [("publish_content", "Darf Inhaltsrevisionen freigeben")]

    def __str__(self) -> str:
        return self.title


class ExtractionSnapshot(ImmutableModel):
    document = models.OneToOneField(ContentDocument, on_delete=models.PROTECT, related_name="extraction")
    title = models.CharField(max_length=255)
    markdown = models.TextField()
    metadata = models.JSONField(default=dict)
    sha256 = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    def prepare_snapshot(self) -> None:
        self.sha256 = hashlib.sha256(self.markdown.encode("utf-8")).hexdigest()


class ContentRevision(ImmutableModel):
    document = models.ForeignKey(ContentDocument, on_delete=models.PROTECT, related_name="revisions")
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    body = models.TextField()
    yaml_header = models.TextField(blank=True)
    frontmatter = models.JSONField(default=dict)
    content_sha256 = models.CharField(max_length=64, default="")
    parent = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="children",
    )
    restored_from = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True, related_name="+",
    )
    cause = models.CharField(max_length=20, choices=[
        ("extraction", "Extraktion"), ("edit", "Bearbeitung"),
        ("restore", "Wiederherstellung"), ("legacy", "Übernommene Revision"),
    ], default="edit")
    metadata = models.JSONField(default=dict)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    def prepare_snapshot(self) -> None:
        parsed = split_markdown(self.yaml_header + self.body)
        if parsed.body != self.body or parsed.header != self.yaml_header:
            raise ValidationError("YAML-Header und Editorinhalt müssen getrennt gespeichert werden.")
        self.frontmatter = parsed.frontmatter
        self.content_sha256 = revision_digest(self.title, self.body, self.yaml_header, self.metadata)
        if self.parent_id and (
            self.parent.document_id != self.document_id or self.parent.number != self.number - 1
        ):
            raise ValidationError("Die Vorgängerrevision muss zum selben Dokument gehören.")
        if self.number == 1 and self.parent_id:
            raise ValidationError("Die erste Revision darf keinen Vorgänger haben.")
        if self.number > 1 and not self.parent_id:
            raise ValidationError("Neue Revision benötigt einen eindeutigen Vorgänger.")
        if self.restored_from_id and self.restored_from.document_id != self.document_id:
            raise ValidationError("Wiederherstellung aus fremdem Dokument ist nicht erlaubt.")
        if self.restored_from_id and self.restored_from.number >= self.number:
            raise ValidationError("Wiederherstellung benötigt einen älteren Stand.")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["document", "number"], name="unique_document_revision"),
        ]
        ordering = ["-number"]


# Django discovers these models through this app's models module.
from .graph_models import (  # noqa: E402,F401
    BlockSnapshot, CollectionEntry, CollectionLink, ContentCollection, ContentResource,
    RelationType, ResourceRelation,
)
