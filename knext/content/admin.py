"""Read-only provenance inspection; changes go through revision-aware views."""

from django.contrib import admin

from .models import ContentDocument, ContentRevision, ImportRun, SourceAsset


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
