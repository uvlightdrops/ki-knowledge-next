"""Resource identities, contextual placements and typed graph edges."""

import uuid

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .immutable import ImmutableModel


class ContentResource(models.Model):
    class Kind(models.TextChoices):
        DOCUMENT = "document", "Dokument"
        BLOCK = "block", "Block"
        FOLDER = "folder", "Ordner"
        COLLECTION = "collection", "Zusammenstellung"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kind = models.CharField(max_length=20, choices=Kind)
    domain = models.CharField(max_length=150, db_index=True)
    title = models.CharField(max_length=255)
    document = models.ForeignKey(
        "ContentDocument", on_delete=models.PROTECT, null=True, blank=True, related_name="resources",
    )
    local_key = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title", "id"]
        constraints = [
            models.UniqueConstraint(
                fields=["document", "local_key"], condition=models.Q(document__isnull=False),
                name="unique_document_resource_key",
            ),
            models.CheckConstraint(
                condition=(
                    models.Q(kind="document", document__isnull=False, local_key="")
                    | (models.Q(kind="block", document__isnull=False) & ~models.Q(local_key=""))
                    | models.Q(kind__in=["folder", "collection"], document__isnull=True, local_key="")
                ),
                name="resource_identity_matches_kind",
            ),
        ]

    def __str__(self) -> str:
        return f"{self.get_kind_display()}: {self.title} · {self.domain} · {self.pk}"


class BlockSnapshot(ImmutableModel):
    resource = models.ForeignKey(ContentResource, on_delete=models.PROTECT, related_name="snapshots")
    revision = models.ForeignKey("ContentRevision", on_delete=models.PROTECT, related_name="blocks")
    title = models.CharField(max_length=255)
    explicit_id = models.CharField(max_length=255, blank=True)
    level = models.PositiveSmallIntegerField()
    start_line = models.PositiveIntegerField()
    end_line = models.PositiveIntegerField()
    body = models.TextField()

    class Meta:
        ordering = ["start_line"]
        constraints = [
            models.UniqueConstraint(fields=["resource", "revision"], name="unique_block_revision"),
            models.CheckConstraint(
                condition=models.Q(level__gte=1, level__lte=6, start_line__gte=1)
                & models.Q(end_line__gte=models.F("start_line")),
                name="valid_block_source_span",
            ),
        ]

    def prepare_snapshot(self) -> None:
        if self.resource.kind != ContentResource.Kind.BLOCK or self.resource.document_id != self.revision.document_id:
            raise ValidationError("Block und Revision müssen zum selben Dokument gehören.")


class RelationType(models.Model):
    key = models.SlugField(primary_key=True, max_length=80)
    label = models.CharField(max_length=150)
    description = models.TextField("Definition und Begründung")
    catalog_managed = models.BooleanField(default=False, editable=False)

    def __str__(self) -> str:
        return f"{self.label} ({self.key})"


class ResourceRelation(models.Model):
    source = models.ForeignKey(ContentResource, on_delete=models.PROTECT, related_name="outgoing_relations")
    target = models.ForeignKey(ContentResource, on_delete=models.PROTECT, related_name="incoming_relations")
    relation_type = models.ForeignKey(RelationType, on_delete=models.PROTECT)
    reason = models.TextField(blank=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "target", "relation_type"], name="unique_resource_relation"),
        ]


class ContentCollection(models.Model):
    class Kind(models.TextChoices):
        SEQUENCE = "sequence", "Sequenz"
        HIERARCHY = "hierarchy", "Hierarchie"
        SET = "set", "Sammlung"
        NETWORK = "network", "Netz"

    resource = models.OneToOneField(
        ContentResource, on_delete=models.PROTECT, primary_key=True, related_name="collection",
    )
    kind = models.CharField(max_length=20, choices=Kind, default=Kind.HIERARCHY)
    description = models.TextField(blank=True)
    version = models.PositiveIntegerField(default=1)
    source_revision = models.OneToOneField(
        "ContentRevision", on_delete=models.PROTECT, null=True, blank=True, related_name="outline",
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]

    def __str__(self) -> str:
        return self.resource.title

    def clean(self) -> None:
        super().clean()
        if self.resource.kind != ContentResource.Kind.COLLECTION:
            raise ValidationError("Zusammenstellung benötigt eine Ressource vom Typ Zusammenstellung.")


class CollectionEntry(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    collection = models.ForeignKey(ContentCollection, on_delete=models.CASCADE, related_name="entries")
    key = models.SlugField(max_length=100)
    resource = models.ForeignKey(ContentResource, on_delete=models.PROTECT, related_name="placements")
    parent = models.ForeignKey("self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children")
    position = models.PositiveIntegerField(default=0)
    revision = models.ForeignKey("ContentRevision", on_delete=models.PROTECT, null=True, blank=True)

    class Meta:
        ordering = ["position", "key"]
        constraints = [
            models.UniqueConstraint(fields=["collection", "key"], name="unique_collection_entry_key"),
        ]

    def clean(self) -> None:
        super().clean()
        if self.parent_id and self.parent.collection_id != self.collection_id:
            raise ValidationError("Elterneintrag muss zur selben Zusammenstellung gehören.")
        if self.revision_id:
            if self.resource.document_id != self.revision.document_id:
                raise ValidationError("Revision gehört nicht zur ausgewählten Ressource.")
            if self.resource.kind == ContentResource.Kind.BLOCK and not BlockSnapshot.objects.filter(
                resource=self.resource, revision=self.revision,
            ).exists():
                raise ValidationError("Block ist in dieser Revision nicht vorhanden.")


class CollectionLink(models.Model):
    collection = models.ForeignKey(ContentCollection, on_delete=models.CASCADE, related_name="links")
    source = models.ForeignKey(CollectionEntry, on_delete=models.CASCADE, related_name="outgoing_links")
    target = models.ForeignKey(CollectionEntry, on_delete=models.CASCADE, related_name="incoming_links")
    relation_type = models.ForeignKey(RelationType, on_delete=models.PROTECT)
    reason = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["source", "target", "relation_type"], name="unique_collection_link"),
        ]

    def clean(self) -> None:
        super().clean()
        if self.source.collection_id != self.collection_id or self.target.collection_id != self.collection_id:
            raise ValidationError("Kanten müssen Einträge derselben Zusammenstellung verbinden.")
