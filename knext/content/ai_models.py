"""Reviewable, user-owned text proposals bound to an exact editor buffer."""

import uuid

from django.conf import settings
from django.db import models


class TextProposal(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey("ContentDocument", on_delete=models.CASCADE, related_name="ai_proposals")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    expected = models.PositiveIntegerField()
    title = models.CharField(max_length=255)
    base_body = models.TextField()
    start = models.PositiveIntegerField()
    end = models.PositiveIntegerField()
    instruction = models.TextField()
    context = models.TextField(blank=True)
    provider = models.CharField(max_length=30)
    model = models.CharField(max_length=255)
    prompt_version = models.CharField(max_length=30, default="text-v1")
    text = models.TextField(blank=True)
    error = models.TextField(blank=True)
    status = models.CharField(max_length=20, default="generating", choices=[
        ("generating", "Wird erstellt"), ("ready", "Vorschlag"), ("failed", "Fehlgeschlagen"),
        ("accepted", "Übernommen"), ("discarded", "Verworfen"),
    ])
    accepted_revision = models.ForeignKey(
        "ContentRevision", on_delete=models.PROTECT, null=True, blank=True,
    )
    accepted_text = models.TextField(blank=True)

    class Meta:
        ordering = ["-created_at"]
