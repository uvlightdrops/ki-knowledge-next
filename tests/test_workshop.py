"""Provisioned originals, immutable extraction and revision-aware workshop integration."""

import hashlib
import io
import json
from zipfile import ZipFile

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from knext.content import inventory
from knext.content.importers.base import ImportFailure
from knext.content.inventory import provisioned_files, register_provisioned
from knext.content.markdown_document import split_markdown
from knext.content.models import (
    ContentDocument, ContentRevision, ExtractionSnapshot, ImportRun, SourceAsset, SourceRegistration,
)
from knext.content.services import (
    RevisionConflict, approve, extract_source, import_upload, process_run, register_bytes, restore, revise,
)

pytestmark = pytest.mark.django_db
HEADER = '---\n# Preserve comments\nproject: "Knowledge"\ncreated: 2026-11-10\ntags: [one, two]\n---\n'
BODY = "# Chapter\n\nFirst passage.\n\n## Detail [stable-id]\n\nSource material.\n"


@pytest.fixture
def writer():
    return User.objects.create_user("workshop-writer")


@pytest.fixture
def client(writer):
    browser = Client()
    browser.force_login(writer)
    return browser


@pytest.fixture
def staged(tmp_path, settings):
    settings.WISSENSWIKI = {
        **settings.WISSENSWIKI,
        "MARKDOWN_DATA": {**settings.WISSENSWIKI["MARKDOWN_DATA"], "root": str(tmp_path / "data")},
    }
    file = tmp_path / "data" / "Books" / "md" / "chapter.md"
    file.parent.mkdir(parents=True)
    file.write_text(HEADER + BODY, encoding="utf-8")
    return file


def import_document(writer):
    run, _ = import_upload(
        SimpleUploadedFile("chapter.md", (HEADER + BODY).encode()), "Books", writer,
    )
    return run.documents.get()


def test_staging_is_read_only_and_registration_is_not_extraction(client, staged, writer):
    response = client.get(reverse("content:inventory"))
    assert response.status_code == 200 and b"Books/md/chapter.md" in response.content
    assert not SourceAsset.objects.exists()
    assert not ImportRun.objects.exists()
    source, created = register_provisioned("Books/md/chapter.md", writer)
    assert created and bytes(source.data) == staged.read_bytes()
    assert source.format == ".md"
    assert source.registrations.get().relative_path == "Books/md/chapter.md"
    assert not ImportRun.objects.exists() and not ContentDocument.objects.exists()
    assert "Registriert, noch nicht zerlegt." in client.get(reverse("content:source", args=[source.pk])).content.decode()


def test_registration_pins_bytes_and_changed_file_creates_new_source(staged, writer):
    original, created = register_provisioned("Books/md/chapter.md", writer)
    repeated, created = register_provisioned("Books/md/chapter.md", writer)
    assert not created and repeated.pk == original.pk
    staged.write_text("# Changed source\n\nOther material.")
    changed, created = register_provisioned("Books/md/chapter.md", writer)
    assert created and changed.pk != original.pk
    staged.unlink()
    run, created = extract_source(original, writer)
    assert created and run.status == ImportRun.Status.SUCCEEDED
    assert run.documents.get().revisions.get().body == BODY
    assert SourceRegistration.objects.count() == 2
    duplicate, created = extract_source(original, writer)
    assert not created and duplicate.pk == run.pk


def test_identical_bytes_with_different_formats_have_separate_adapter_identity(writer):
    markdown, _ = register_bytes("a.md", b"# Title\n\nBody", "Books", writer)
    literal, _ = register_bytes("a.txt", b"# Title\n\nBody", "Books", writer)
    assert markdown.pk != literal.pk
    assert markdown.sha256 == literal.sha256
    md_run, _ = extract_source(markdown, writer)
    text_run, _ = extract_source(literal, writer)
    assert md_run.documents.get().revisions.get().body.startswith("# Title")
    assert text_run.documents.get().revisions.get().body.startswith("```")


@pytest.mark.parametrize("relative", [
    "../chapter.md", "/Books/md/chapter.md", "Books/../chapter.md",
    "Books/md/../chapter.md", "Books/md//chapter.md", "Books/md/hidden/.private.md",
    "Books/md/wrong.pdf", "Books/md/a\\b.md", "Books/.md/chapter.md",
])
def test_registration_rejects_untrusted_paths(staged, writer, relative):
    with pytest.raises(ImportFailure):
        register_provisioned(relative, writer)
    assert not SourceAsset.objects.exists()


def test_symlinks_are_neither_listed_nor_imported(staged, tmp_path, writer):
    outside = tmp_path / "private.md"
    outside.write_text("outside")
    link = staged.parent / "link.md"
    link.symlink_to(outside)
    directory_link = staged.parents[1] / "pdf"
    directory_link.symlink_to(staged.parent, target_is_directory=True)
    assert [item.relative_path for item in provisioned_files()] == ["Books/md/chapter.md"]
    with pytest.raises(ImportFailure, match="Symlink"):
        register_provisioned("Books/md/link.md", writer)
    assert not SourceAsset.objects.exists()


def test_inventory_rejects_symlink_data_root(staged, tmp_path, settings):
    root = tmp_path / "linked-root"
    root.symlink_to(staged.parents[2], target_is_directory=True)
    settings.WISSENSWIKI["MARKDOWN_DATA"]["root"] = str(root)
    with pytest.raises(ImportFailure, match="Datenwurzel"):
        provisioned_files()


def test_inventory_does_not_descend_unrelated_format_directories(staged, monkeypatch):
    unrelated = staged.parents[1] / "private-backups"
    unrelated.mkdir()
    original = inventory.os.scandir

    def inspect(path):
        if path == unrelated:
            raise PermissionError("Unrelated directory must not be read.")
        return original(path)

    monkeypatch.setattr(inventory.os, "scandir", inspect)
    assert [item.relative_path for item in provisioned_files()] == ["Books/md/chapter.md"]


def test_registration_ignores_unsupported_files_and_rejects_oversize(staged, writer):
    (staged.parent / "ignored.exe").write_bytes(b"binary")
    with staged.open("wb") as stream:
        stream.truncate(10 * 1024 * 1024 + 1)
    assert len(provisioned_files()) == 1
    with pytest.raises(ImportFailure, match="10 MiB"):
        register_provisioned("Books/md/chapter.md", writer)


def test_extraction_is_separate_from_body_only_editor_and_preserves_header(client, writer):
    document = import_document(writer)
    baseline = document.extraction
    first = document.revisions.get()
    assert baseline.markdown == HEADER + BODY
    assert baseline.sha256 == hashlib.sha256((HEADER + BODY).encode()).hexdigest()
    assert first.body == BODY and first.yaml_header == HEADER
    assert first.frontmatter == {"project": "Knowledge", "created": "2026-11-10", "tags": ["one", "two"]}
    soup = BeautifulSoup(client.get(reverse("content:document", args=[document.pk])).content, "html.parser")
    assert soup.select_one("textarea").get_text().removeprefix("\n") == BODY
    revised = revise(document, expected=1, title="New title", body="New body\n", user=writer)
    assert revised.parent == first and revised.yaml_header == HEADER
    assert revised.frontmatter == first.frontmatter
    assert revised.content_sha256 != first.content_sha256
    baseline.refresh_from_db()
    first.refresh_from_db()
    assert baseline.markdown == HEADER + BODY and first.body == BODY


@pytest.mark.parametrize("target", ["source", "snapshot", "revision", "registration"])
def test_snapshots_reject_model_queryset_and_bulk_mutation(staged, writer, target):
    source, _ = register_provisioned("Books/md/chapter.md", writer)
    run, _ = extract_source(source, writer)
    document = run.documents.get()
    record = {
        "source": source, "snapshot": document.extraction,
        "revision": document.revisions.get(), "registration": source.registrations.get(),
    }[target]
    with pytest.raises(ValidationError, match="unveränderlich"):
        record.save()
    with pytest.raises(ValidationError):
        type(record).objects.filter(pk=record.pk).update(pk=record.pk)
    with pytest.raises(ValidationError):
        type(record).objects.bulk_update([record], ["pk"])
    with pytest.raises((ValidationError, ValueError)):
        record.delete()
    with pytest.raises(ValidationError):
        type(record).objects.filter(pk=record.pk).delete()


def test_historical_inspection_download_diff_and_restore_do_not_rewrite_approval(client, writer):
    document = import_document(writer)
    first = document.revisions.get()
    publisher = User.objects.create_superuser("workshop-publisher")
    approve(document, expected=1, user=publisher)
    second = revise(document, expected=1, title="Edited", body="Different text.\n", user=writer)
    detail = client.get(reverse("content:revision", args=[document.pk, 2]))
    assert detail.status_code == 200
    assert "Different text." in detail.content.decode()
    assert detail.context["diff"].startswith("--- Revision 1")
    restored = client.post(reverse("content:restore", args=[document.pk, 1]), {"expected": 2})
    assert restored.status_code == 302
    document.refresh_from_db()
    third = document.revisions.get(number=3)
    assert third.parent == second and third.restored_from == first and third.cause == "restore"
    assert third.content_sha256 == first.content_sha256 and third.yaml_header == HEADER
    assert document.approved_revision == first
    assert document.revisions.count() == 3
    assert client.post(reverse("content:restore", args=[document.pk, 1]), {"expected": 2}).status_code == 409
    md = client.get(reverse("content:revision", args=[document.pk, 3]), {"format": "markdown"})
    assert md.content.decode() == HEADER + BODY
    baseline = client.get(reverse("content:extraction", args=[document.pk]), {"format": "markdown"})
    assert baseline.content.decode() == HEADER + BODY
    assert client.get(reverse("content:revision", args=[document.pk, 99])).status_code == 404


def test_editor_rejects_yaml_instead_of_silently_discarding_it(client, writer):
    document = import_document(writer)
    response = client.post(reverse("content:document", args=[document.pk]), {
        "expected": 1, "title": "Title", "body": "---\nnew: metadata\n---\nBody",
    })
    assert response.status_code == 400
    assert "gehören nicht in den Texteditor" in response.content.decode()
    assert document.revisions.count() == 1
    with pytest.raises(ImportFailure):
        revise(document, expected=1, title="Title", body="---\nx: y\n---\nText", user=writer)


@pytest.mark.parametrize("header", [
    "---\nx: one\nx: two\n---\n",
    "---\n1: numeric key\n---\n",
    "---\nx: .nan\n---\n",
    "---\nx: &ref [*ref]\n---\n",
    "---\n- list\n---\n",
    "---\nx: y\n",
])
def test_invalid_headers_leave_registered_source_but_no_partial_extraction(writer, header):
    run, _ = import_upload(SimpleUploadedFile("invalid.md", (header + BODY).encode()), "Books", writer)
    assert run.status == ImportRun.Status.FAILED
    assert SourceAsset.objects.count() == 1
    assert not ContentDocument.objects.exists() and not ExtractionSnapshot.objects.exists()


def test_snapshot_validation_failure_rolls_back_entire_extraction(writer, monkeypatch):
    def reject(**kwargs):
        raise ValidationError("Ungültiger Ausgangsstand")

    monkeypatch.setattr(ContentRevision.objects, "create", reject)
    run, _ = import_upload(SimpleUploadedFile("chapter.md", (HEADER + BODY).encode()), "Books", writer)
    assert run.status == ImportRun.Status.FAILED and "Ungültiger Ausgangsstand" in run.error
    assert not ContentDocument.objects.exists() and not ExtractionSnapshot.objects.exists()
    assert SourceAsset.objects.count() == 1


def test_obsolete_pipeline_cannot_retry_under_a_new_implementation(writer):
    source, _ = register_bytes("chapter.md", BODY.encode(), "Books", writer)
    old = ImportRun.objects.create(
        source=source, pipeline_version="content-import-v1", adapter="text-v1", status="failed",
    )
    with pytest.raises(RevisionConflict, match="Pipeline-Version"):
        process_run(old, writer)
    current, _ = extract_source(source, writer)
    old.refresh_from_db()
    assert old.status == "failed" and old.attempts == 0
    assert current.pk != old.pk and current.status == "succeeded"


def test_extraction_verifies_stored_original_fingerprint(writer):
    source, _ = register_bytes("chapter.md", BODY.encode(), "Books", writer)
    # Simulate storage damage without mutating the persisted source.
    source.data = b"corrupted bytes"
    run = ImportRun.objects.create(
        source=source, pipeline_version="content-import-v2", adapter="text-v1",
    )
    process_run(run, writer)
    assert run.status == "failed" and "Prüfsumme" in run.error
    assert not ContentDocument.objects.exists()


def test_header_size_and_alias_expansion_are_bounded():
    with pytest.raises(ImportFailure, match="128 KiB"):
        split_markdown("---\nvalue: " + "x" * (128 * 1024) + "\n---\nBody")
    values = "base: &base [" + ",".join(["value"] * 100) + "]\n"
    with pytest.raises(ImportFailure, match="Alias"):
        split_markdown("---\n" + values + "expanded: [" + ",".join(["*base"] * 100) + "]\n---\nBody")


def test_crlf_empty_header_and_end_marker_are_separated():
    value = split_markdown("---\r\nproject: value\r\n...\r\n# Body\r\n")
    assert value.body == "# Body\r\n"
    assert value.header == "---\r\nproject: value\r\n...\r\n"
    assert split_markdown("---\n---\nBody").frontmatter == {}
    assert split_markdown("Text\n\n---\n\nRule").header == ""


def test_state_changes_require_authentication_post_and_csrf(client, staged, writer):
    inventory = reverse("content:inventory")
    assert Client().get(inventory).status_code == 302
    assert client.get(reverse("content:register-source")).status_code == 405
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(writer)
    assert csrf.post(reverse("content:register-source"), {"relative_path": "Books/md/chapter.md"}).status_code == 403
    registered = client.post(reverse("content:register-source"), {"relative_path": "Books/md/chapter.md"})
    assert registered.status_code == 302
    source = SourceAsset.objects.get()
    assert client.get(reverse("content:extract-source", args=[source.pk])).status_code == 405
    result = client.post(reverse("content:extract-source", args=[source.pk]))
    assert result.status_code == 302
    document = ContentDocument.objects.get()
    assert Client().get(reverse("content:extraction", args=[document.pk])).status_code == 302
    assert Client().get(reverse("content:revision", args=[document.pk, 1])).status_code == 302
    assert client.get(reverse("content:restore", args=[document.pk, 1])).status_code == 405


def test_snapshot_hashes_are_in_approved_export_manifest(client, writer):
    document = import_document(writer)
    publisher = User.objects.create_superuser("export-publisher")
    approve(document, expected=1, user=publisher)
    response = client.get(reverse("content:site-download"), {"domain": "Books"})
    with ZipFile(io.BytesIO(response.content)) as archive:
        entry = json.loads(archive.read("manifest.json"))["documents"][0]
        assert entry["revision_sha256"] == document.approved_revision.content_sha256
        assert entry["extraction_sha256"] == document.extraction.sha256
        assert HEADER not in archive.read(f"{document.pk}.html").decode()
