"""Preserve existing documents and approvals while making provenance explicit."""

import hashlib
from pathlib import Path

from django.db import migrations

from knext.content.markdown_document import revision_digest, split_markdown


def backfill(apps, schema_editor):
    source_model = apps.get_model("content", "SourceAsset")
    document_model = apps.get_model("content", "ContentDocument")
    revision_model = apps.get_model("content", "ContentRevision")
    extraction_model = apps.get_model("content", "ExtractionSnapshot")
    alias = schema_editor.connection.alias
    for source in source_model.objects.using(alias).only("pk", "filename").iterator():
        source_model.objects.using(alias).filter(pk=source.pk).update(
            format=Path(source.filename).suffix.lower(),
        )
    for document in document_model.objects.using(alias).select_related("run__source").iterator():
        revisions = list(revision_model.objects.using(alias).filter(document=document).order_by("number"))
        if not revisions:
            raise RuntimeError(f"Dokument {document.pk} besitzt keine Ausgangsrevision; Migration abgebrochen.")
        initial = split_markdown(revisions[0].body)
        header = initial.header
        if not header and document.run.source.format in {".md", ".markdown"}:
            original = bytes(document.run.source.data).decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n")
            header = split_markdown(original).header
        markdown = header + initial.body
        snapshot = extraction_model.objects.using(alias).create(
            document=document, title=revisions[0].title, markdown=markdown,
            metadata=revisions[0].metadata, sha256=hashlib.sha256(markdown.encode("utf-8")).hexdigest(),
        )
        extraction_model.objects.using(alias).filter(pk=snapshot.pk).update(created_at=revisions[0].created_at)
        previous = None
        for revision in revisions:
            parsed = split_markdown(revision.body)
            current_header = parsed.header or header
            separated = split_markdown(current_header + parsed.body)
            revision_model.objects.using(alias).filter(pk=revision.pk).update(
                body=parsed.body, yaml_header=current_header, frontmatter=separated.frontmatter,
                parent_id=previous.pk if previous else None, cause="legacy",
                content_sha256=revision_digest(revision.title, parsed.body, current_header, revision.metadata),
            )
            previous = revision


class Migration(migrations.Migration):
    dependencies = [("content", "0003_extractionsnapshot_sourceregistration_and_more")]
    operations = [migrations.RunPython(backfill)]
