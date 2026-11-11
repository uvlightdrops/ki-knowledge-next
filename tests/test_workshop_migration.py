"""Data upgrade preserves old revision IDs, approvals and original YAML headers."""

import hashlib
import importlib
from types import SimpleNamespace

import pytest
from django.contrib.auth.models import User
from django.db import connection
from django.db.migrations.loader import MigrationLoader

from knext.content.models import ContentDocument, ContentRevision, SourceAsset

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize("inline_header", [False, True])
def test_backfill_preserves_revision_lineage_and_approval(inline_header):
    loader = MigrationLoader(connection)
    historical = loader.project_state([("content", "0003_extractionsnapshot_sourceregistration_and_more")]).apps
    sources = historical.get_model("content", "SourceAsset")
    runs = historical.get_model("content", "ImportRun")
    documents = historical.get_model("content", "ContentDocument")
    revisions = historical.get_model("content", "ContentRevision")
    user = User.objects.create_user("legacy-author")
    header = '---\n# historical comment\nproject: "Legacy"\n---\n'
    body = "# Legacy\n\nOriginal body.\n"
    original = (header + body).encode()
    source = sources.objects.create(
        domain="Books", filename="legacy.md", data=original, size=len(original),
        sha256=hashlib.sha256(original).hexdigest(), uploaded_by_id=user.pk,
    )
    run = runs.objects.create(source=source, pipeline_version="content-import-v1", adapter="text-v1")
    document = documents.objects.create(run=run, title="Edited", revision_number=2)
    first = revisions.objects.create(
        document=document, number=1, title="Legacy", body=header + body if inline_header else body,
        metadata={"project": "Legacy"}, created_by_id=user.pk,
    )
    second = revisions.objects.create(
        document=document, number=2, title="Edited", body="An already edited draft.\n",
        metadata={"project": "Legacy"}, created_by_id=user.pk,
    )
    documents.objects.filter(pk=document.pk).update(approved_revision=second, approved_by_id=user.pk)

    migration = importlib.import_module("knext.content.migrations.0004_backfill_workshop_lineage")
    migration.backfill(historical, SimpleNamespace(connection=connection))

    upgraded = ContentDocument.objects.get(pk=document.pk)
    assert upgraded.approved_revision_id == second.pk
    assert upgraded.approved_by_id == user.pk
    assert upgraded.revision_number == 2
    assert upgraded.extraction.markdown == header + body
    assert upgraded.extraction.created_at == first.created_at
    initial = ContentRevision.objects.get(pk=first.pk)
    edited = ContentRevision.objects.get(pk=second.pk)
    assert initial.body == body and initial.yaml_header == header and initial.parent_id is None
    assert edited.body == "An already edited draft.\n" and edited.yaml_header == header
    assert edited.parent_id == initial.pk
    assert initial.cause == edited.cause == "legacy"
    assert len(edited.content_sha256) == 64
    assert SourceAsset.objects.get(pk=source.pk).format == ".md"
