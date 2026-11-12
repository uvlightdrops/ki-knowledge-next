"""Read-only provenance inspection; changes go through revision-aware views."""

from django.contrib import admin

from .ai_models import TextProposal
from .models import (
    ContentDocument, ContentRevision, ExtractionSnapshot, ImportRun, SourceAsset, SourceRegistration,
    ManagedDomain,
    FilesystemArtifact, ImportBatch, ImportJob, JobAttempt,
    BlockSnapshot, CollectionEntry, CollectionLink, ContentCollection, ContentResource,
    RelationType, ResourceRelation,
)


class ProvenanceAdmin(admin.ModelAdmin):
    def has_add_permission(self, request) -> bool:
        return False

    def has_change_permission(self, request, obj=None) -> bool:
        return False

    def has_delete_permission(self, request, obj=None) -> bool:
        return False


@admin.register(SourceAsset)
class SourceAdmin(ProvenanceAdmin):
    exclude = ["data"]
    list_display = ["filename", "domain", "size", "created_at"]
    list_filter = ["domain"]


@admin.register(ImportRun)
class RunAdmin(ProvenanceAdmin):
    list_display = ["source", "adapter", "status", "attempts", "created_at"]
    list_filter = ["status"]


@admin.register(ContentDocument)
class DocumentAdmin(ProvenanceAdmin):
    list_display = ["title", "revision_number", "approved_revision"]


admin.site.register(ContentRevision, ProvenanceAdmin)
admin.site.register(ExtractionSnapshot, ProvenanceAdmin)
admin.site.register(SourceRegistration, ProvenanceAdmin)
admin.site.register(ManagedDomain, ProvenanceAdmin)
admin.site.register(FilesystemArtifact, ProvenanceAdmin)
admin.site.register(ImportBatch, ProvenanceAdmin)
admin.site.register(ImportJob, ProvenanceAdmin)
admin.site.register(JobAttempt, ProvenanceAdmin)
admin.site.register(TextProposal, ProvenanceAdmin)
for graph_model in (
    ContentResource, BlockSnapshot, RelationType, ResourceRelation,
    ContentCollection, CollectionEntry, CollectionLink,
):
    admin.site.register(graph_model, ProvenanceAdmin)
