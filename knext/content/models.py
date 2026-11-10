"""Original sources, processing provenance and independently approved revisions."""

import uuid

from django.conf import settings
from django.db import models


class SourceAsset(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    domain = models.CharField("Domäne", max_length=150, db_index=True)
    filename = models.CharField("Originaldatei", max_length=255)
    sha256 = models.CharField(max_length=64)
    data = models.BinaryField()
    size = models.PositiveIntegerField()
    uploaded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["domain", "sha256"], name="unique_source_in_domain"),
        ]

    def __str__(self) -> str:
        return self.filename


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

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "pipeline_version"], name="unique_source_pipeline"),
        ]
        ordering = ["-created_at"]


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


class ContentRevision(models.Model):
    document = models.ForeignKey(ContentDocument, on_delete=models.PROTECT, related_name="revisions")
    number = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    body = models.TextField()
    metadata = models.JSONField(default=dict)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["document", "number"], name="unique_document_revision"),
        ]
        ordering = ["-number"]
