"""Import, revision and export behavior against an isolated Django database."""

import io
import json
from zipfile import ZipFile

import pytest
from django.contrib.auth.models import Permission, User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from knext.content.models import ContentDocument, ImportRun, SourceAsset
from knext.content.services import RevisionConflict, approve, import_upload, revise

pytestmark = pytest.mark.django_db


@pytest.fixture
def writer():
    return User.objects.create_user("editor")


@pytest.fixture
def client(writer):
    browser = Client()
    browser.force_login(writer)
    return browser


def upload(name="notes.md", text="# Original\n\n## Thema\n\nPrüfbarer Inhalt."):
    return SimpleUploadedFile(name, text.encode("utf-8"))


def imported(writer):
    run, _ = import_upload(upload(), "Dokumentation", writer)
    return run.documents.get()


def test_import_preserves_original_and_creates_unapproved_revision(writer):
    run, created = import_upload(upload(), "Dokumentation", writer)
    assert created and run.status == ImportRun.Status.SUCCEEDED
    assert bytes(run.source.data) == upload().read()
    assert run.source.size == len(upload().read())
    assert len(run.source.sha256) == 64
    document = run.documents.get()
    assert document.title == "Original"
    assert document.revision_number == 1
    assert document.approved_revision is None
    assert document.revisions.get().created_by == writer
    assert document.revisions.get().body.startswith("# Original")


def test_duplicate_is_idempotent_per_domain_and_preserves_edited_draft(writer):
    document = imported(writer)
    revise(document, expected=1, title="Bearbeitet", body="Neuer Inhalt", user=writer)
    run, created = import_upload(upload(), "Dokumentation", writer)
    assert not created and run.documents.get().revision_number == 2
    assert run.documents.get().title == "Bearbeitet"
    assert SourceAsset.objects.count() == 1
    other, created = import_upload(upload(), "Andere Domäne", writer)
    assert created and other.source_id != run.source_id


def test_failed_import_is_visible_and_retry_does_not_create_drafts(client):
    response = client.post(reverse("content:import"), {
        "domain": "Dokumentation", "file": SimpleUploadedFile("bad.pdf", b"not a pdf"),
    })
    assert response.status_code == 302
    run = ImportRun.objects.get()
    assert run.status == ImportRun.Status.FAILED and run.error
    assert not run.documents.exists()
    response = client.post(reverse("content:retry", args=[run.pk]))
    run.refresh_from_db()
    assert response.status_code == 302 and run.attempts == 2
    assert run.status == ImportRun.Status.FAILED
    assert not ContentDocument.objects.exists()
    assert "Fehlgeschlagen" in client.get(response.url).content.decode()


def test_unsupported_format_and_invalid_domain_do_not_register_sources(client):
    for domain, file in [
        ("Dokumentation", SimpleUploadedFile("code.exe", b"x")),
        ("not-configured", upload()),
    ]:
        response = client.post(reverse("content:import"), {"domain": domain, "file": file})
        assert response.status_code == 200 and response.context["form"].errors
    assert not SourceAsset.objects.exists()


def test_revision_conflict_preserves_both_history_and_submitted_text(client, writer):
    document = imported(writer)
    revise(document, expected=1, title="Revision zwei", body="Aktuell", user=writer)
    response = client.post(reverse("content:document", args=[document.pk]), {
        "expected": 1, "title": "Veralteter Editor", "body": "Nicht verlieren",
    })
    assert response.status_code == 409
    assert "Nicht verlieren" in response.content.decode()
    document.refresh_from_db()
    assert document.revision_number == 2 and document.revisions.count() == 2
    assert document.title == "Revision zwei"


def test_approval_requires_permission_and_pins_exact_revision(client, writer):
    document = imported(writer)
    url = reverse("content:approve", args=[document.pk])
    assert client.get(url).status_code == 405
    assert client.post(url, {"expected": 1}).status_code == 403
    writer.user_permissions.add(Permission.objects.get(codename="publish_content"))
    assert client.post(url, {"expected": 1}).status_code == 302
    document.refresh_from_db()
    assert document.approved_revision.number == 1
    assert document.approved_by == writer and document.approved_at is not None
    revise(document, expected=1, title="Unveröffentlicht", body="Geheimer Entwurf", user=writer)
    assert document.approved_revision.number == 1
    result = client.get(reverse("content:download", args=[document.pk]))
    assert result.status_code == 200
    assert "Geheimer Entwurf" not in result.content.decode()
    assert "Original" in result.content.decode()
    assert client.post(url, {"expected": 1}).status_code == 409


def test_export_contains_only_approved_revisions_and_scopes_domain(client, writer):
    document = imported(writer)
    publisher = User.objects.create_superuser("publisher", password=None)
    approve(document, expected=1, user=publisher)
    import_upload(upload("draft.md", "# Draft\n\nNever exported."), "Dokumentation", writer)
    import_upload(upload("other.md", "# Other\n\nOther domain."), "Elsewhere", writer)
    response = client.get(reverse("content:site-download"), {"domain": "Dokumentation"})
    assert response.status_code == 200 and response["Content-Type"] == "application/zip"
    with ZipFile(io.BytesIO(response.content)) as archive:
        assert set(archive.namelist()) == {"index.html", f"{document.pk}.html", "manifest.json"}
        index = archive.read("index.html").decode()
        assert "Original" in index and "Draft" not in index and "Other" not in index
        page = archive.read(f"{document.pk}.html").decode()
        assert 'href="index.html"' in page and "notes.md" in page and "Revision 1" in page
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["documents"][0]["revision"] == 1
        assert manifest["documents"][0]["source_sha256"] == document.run.source.sha256
    assert client.get(reverse("content:site-download"), {"domain": "Unknown"}).status_code == 404


def test_draft_download_is_rejected_and_preview_is_sanitized(client, writer):
    document = imported(writer)
    revise(document, expected=1, title="<script>alert(1)</script>",
           body='<script>alert(1)</script>\n\n[x](javascript:alert(1))\n\n<img src=x onerror=alert(1)>',
           user=writer)
    assert client.get(reverse("content:download", args=[document.pk])).status_code == 409
    response = client.get(reverse("content:document", args=[document.pk]))
    html = response.content.decode()
    assert response.status_code == 200
    assert "<script>" not in html and 'href="javascript:' not in html and "<img" not in html
    assert "Gespeicherte Vorschau" in html
    assert "&lt;script&gt;" in html


def test_login_csrf_and_workbench(client, writer):
    anonymous = Client()
    assert anonymous.get(reverse("content:index")).status_code == 302
    document = imported(writer)
    assert anonymous.get(reverse("content:document", args=[document.pk])).status_code == 302
    protected = Client(enforce_csrf_checks=True)
    protected.force_login(writer)
    assert protected.post(reverse("content:import"), {"domain": "Dokumentation", "file": upload()}).status_code == 403
    html = client.get(reverse("content:index")).content.decode()
    assert "Original" in html and "Wissensnetz" in html and "Import starten" in html
    assert reverse("content:document", args=[document.pk]) in html


def test_preview_and_output_do_not_repeat_matching_document_title(client, writer):
    from knext.content.rendering import render_output

    document = imported(writer)
    html = client.get(reverse("content:document", args=[document.pk])).content.decode()
    assert html.count("<h1>Original</h1>") == 1
    revision = document.revisions.get()
    output = render_output(revision)
    assert output.count("<h1>Original</h1>") == 1
    assert revision.body.startswith("# Original")


def test_invalid_revision_fields_are_reported(client, writer):
    document = imported(writer)
    url = reverse("content:document", args=[document.pk])
    assert client.post(url, {"expected": 1, "title": "", "body": ""}).status_code == 400
    assert client.post(reverse("content:approve", args=[document.pk]), {"expected": "x"}).status_code == 400
    assert client.post(reverse("content:retry", args=[document.run_id])).status_code == 409
    with pytest.raises(RevisionConflict):
        revise(document, expected=99, title="Conflict", body="no", user=writer)


def test_workbench_offers_each_approved_domain_once(client, writer):
    publisher = User.objects.create_superuser("publisher")
    for name in ("first.md", "second.md"):
        run, _ = import_upload(upload(name, f"# {name}\n\nBody"), "Dokumentation", writer)
        approve(run.documents.get(), expected=1, user=publisher)

    response = client.get(reverse("content:index"))

    assert list(response.context["domains"]) == ["Dokumentation"]
    assert response.content.decode().count("als HTML-Site herunterladen") == 1


@pytest.mark.parametrize("value", [".nan", ".inf", "-.inf"])
def test_nonfinite_frontmatter_fails_without_partial_drafts(writer, value):
    run, created = import_upload(
        upload(text=f"---\nvalue: {value}\n---\n# Invalid metadata\n\nBody"),
        "Dokumentation", writer,
    )

    assert created and run.status == ImportRun.Status.FAILED
    assert run.error
    assert not run.documents.exists()
