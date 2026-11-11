import hashlib
import json
import os
import signal
import uuid
from unittest.mock import patch
from zipfile import ZipFile

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.core.management import call_command, CommandError
from django.test import Client
from wissenswiki.config import registry

from knext.content.artifacts import materialize_run
from knext.content.file_catalog import file_catalog
from knext.content.importers.base import ImportFailure
from knext.content.inventory import provisioned_files
from knext.content.jobs import (
    cancel_job, claim_job, enqueue_paths, enqueue_run, execute_job,
    recover_interrupted, retry_job, worker_lock, worker_running,
)
from knext.content.models import ContentRevision, FilesystemArtifact, ImportJob, ImportRun, JobAttempt, SourceAsset
from knext.content.services import RevisionConflict, revise

pytestmark = pytest.mark.django_db
MARKDOWN = '---\nproject: Books\nstatus: draft\n---\n# Test\n\n## Detail [detail]\n\n```yaml block-meta\nupdated: "2026-11-11 06"\nstatus: draft\nrelations: []\n```\n\nOriginal.\n'


@pytest.fixture
def environment(tmp_path, settings):
    root = tmp_path / "data"
    file = root / "Books/md/test.md"
    file.parent.mkdir(parents=True)
    file.write_text(MARKDOWN)
    relations = tmp_path / "relations"
    relations.mkdir()
    (tmp_path / "workspace").mkdir()
    (tmp_path / "var").mkdir()
    settings.VAR_DIR = tmp_path / "var"
    settings.WISSENSWIKI = {
        "WORKSPACE": str(tmp_path / "workspace"),
        "MARKDOWN_DATA": {"root": str(root), "relations": str(relations), "prefix": "ki:", "subdir": "md"},
    }
    user = User.objects.create_user("job-writer")
    browser = Client()
    browser.force_login(user)
    return root, file, user, browser


def run_batch(user):
    batch = enqueue_paths(["Books/md/test.md"], ImportJob.Kind.IMPORT, user)
    call_command("content_worker", once=True)
    job = batch.jobs.get()
    job.refresh_from_db()
    return job


def test_batch_register_extract_materialize_exact_bytes_and_browse(environment):
    root, staged, user, browser = environment
    job = run_batch(user)
    assert job.status == ImportJob.Status.SUCCEEDED
    assert job.attempts == 1 and job.history.get().status == "succeeded"
    document = job.run.documents.get()
    path = root / f"Books/md/_extractions/{job.run_id}/{document.pk}.md"
    assert path.read_bytes() == document.extraction.markdown.encode() == MARKDOWN.encode()
    assert path.stat().st_mode & 0o222 == 0
    original = root / f"Books/orig/{job.source_id}/test.md"
    assert original.read_bytes() == staged.read_bytes()
    manifest = json.loads((path.parent / "manifest.json").read_text())
    assert manifest["source_sha256"] == job.source.sha256
    assert manifest["documents"][0]["sha256"] == hashlib.sha256(path.read_bytes()).hexdigest()
    assert FilesystemArtifact.objects.count() == 3
    assert ContentRevision.objects.count() == 1
    # Generated snapshots do not recursively enter the import pipeline.
    assert [f.relative_path for f in provisioned_files()] == ["Books/md/test.md"]
    snapshot = browser.get("/wiki/api", {"domain": "ki:Books"}).json()
    assert any(str(document.pk) in block.get("path", "") for block in snapshot["blocks"])
    blocks = browser.get(f"/content/documents/{document.pk}/extraction/blocks/")
    assert blocks.status_code == 200 and b"block-meta" in blocks.content


def test_idempotent_retry_repairs_missing_file_never_creates_revision(environment):
    root, _, user, _ = environment
    first = run_batch(user)
    document = first.run.documents.get()
    revision_id = document.revisions.get().pk
    (root / f"Books/md/_extractions/{first.run_id}/{document.pk}.md").unlink()
    batch = enqueue_run(first.run, user)
    call_command("content_worker", once=True)
    assert batch.jobs.get().status == "succeeded"
    assert FilesystemArtifact.objects.count() == 3
    assert ContentRevision.objects.get().pk == revision_id
    revise(document, expected=1, title="Edited", body="New body", user=user)
    assert materialize_run(first.run)
    assert (root / f"Books/md/_extractions/{first.run_id}/{document.pk}.md").read_text() == MARKDOWN


def test_altered_output_is_failed_and_never_overwritten(environment):
    root, _, user, _ = environment
    first = run_batch(user)
    document = first.run.documents.get()
    path = root / f"Books/md/_extractions/{first.run_id}/{document.pk}.md"
    path.chmod(0o600)
    path.write_text("Admin changed")
    batch = enqueue_run(first.run, user)
    call_command("content_worker", once=True)
    job = batch.jobs.get()
    assert job.status == "failed" and "kein Überschreiben" in job.error
    assert path.read_text() == "Admin changed"
    assert not list(path.parent.glob(".knext-*"))
    assert ContentRevision.objects.count() == 1


def test_replaced_input_fails_before_registration(environment):
    _, file, user, _ = environment
    batch = enqueue_paths(["Books/md/test.md"], ImportJob.Kind.IMPORT, user)
    file.write_text("# Replacement")
    call_command("content_worker", once=True)
    job = batch.jobs.get()
    assert job.status == "failed" and "seit Batch-Auswahl geändert" in job.error
    assert not SourceAsset.objects.exists()
    retry_job(job)
    call_command("content_worker", once=True)
    job.refresh_from_db()
    assert job.status == "failed" and job.attempts == 2
    assert list(job.history.values_list("status", flat=True)) == ["failed", "failed"]


def test_register_only_keeps_original_without_extraction(environment):
    root, _, user, _ = environment
    batch = enqueue_paths(["Books/md/test.md"], ImportJob.Kind.REGISTER, user)
    call_command("content_worker", once=True)
    job = batch.jobs.get()
    assert job.status == "succeeded"
    assert (root / job.result["paths"][0]).read_text() == MARKDOWN
    assert not ImportRun.objects.exists()


def test_crashed_attempt_is_visible_and_only_owned_import_is_recovered(environment):
    _, _, user, _ = environment
    batch = enqueue_paths(["Books/md/test.md"], ImportJob.Kind.IMPORT, user)
    with worker_lock():
        job = claim_job()
        # Simulate unexpected adapter failure; next worker must preserve interrupted history.
        with patch("knext.content.jobs.process_run", side_effect=RuntimeError("adapter bug")):
            with pytest.raises(RuntimeError):
                execute_job(job)
        run = ImportRun.objects.get()
        ImportRun.objects.filter(pk=run.pk).update(status="processing", processing_job=job)
    with worker_lock():
        assert recover_interrupted() == 1
        assert claim_job() is None
    job.refresh_from_db()
    run.refresh_from_db()
    assert job.status == "failed" and job.history.get().status == "interrupted"
    assert run.status == "failed"
    retry_job(job)
    call_command("content_worker", once=True)
    assert batch.jobs.get().status == "succeeded"
    assert JobAttempt.objects.count() == 2


def test_worker_lock_and_queued_cancel_prevent_duplicate_execution(environment):
    _, _, user, _ = environment
    batch = enqueue_paths(["Books/md/test.md"], ImportJob.Kind.IMPORT, user)
    with worker_lock():
        with pytest.raises(ImportFailure, match="läuft bereits"):
            with worker_lock():
                pass
    job = batch.jobs.get()
    cancel_job(job)
    with pytest.raises(RevisionConflict):
        cancel_job(job)
    assert claim_job() is None
    assert not SourceAsset.objects.exists()


def test_worker_status_uses_live_lock_and_not_leftover_file(environment):
    assert worker_running() is False
    with worker_lock():
        assert worker_running() is True
    assert worker_running() is False


def test_batch_and_job_pages_show_live_counts_and_worker_state(environment):
    _, _, user, browser = environment
    batch = enqueue_paths(["Books/md/test.md"], "import", user)
    job = batch.jobs.get()
    for url in ["/content/jobs/", f"/content/batches/{batch.pk}/", f"/content/jobs/{job.pk}/"]:
        response = browser.get(url)
        assert response.context["job_total"] == 1
        assert response.context["job_finished"] == 0
        assert response.context["worker_running"] is False
        assert b"Kein Importworker aktiv" in response.content
        assert b"content/jobs.js" in response.content
        with worker_lock():
            assert browser.get(url).context["worker_running"] is True
    call_command("content_worker", once=True)
    response = browser.get(f"/content/batches/{batch.pk}/")
    assert response.context["job_finished"] == 1
    assert (ImportJob.Status.SUCCEEDED.label, 1) in response.context["job_counts"]


def test_unreadable_worker_status_is_explicit(environment):
    _, _, _, browser = environment
    with patch("knext.content.job_views.worker_running", side_effect=PermissionError("lock denied")):
        response = browser.get("/content/jobs/")
    assert response.context["worker_running"] is None
    assert b"Workerstatus nicht" in response.content


def test_worker_term_finishes_current_job_without_claiming_another(environment):
    _, _, user, _ = environment
    enqueue_paths(["Books/md/test.md"], "import", user)
    enqueue_paths(["Books/md/test.md"], "import", user)
    original = signal.getsignal(signal.SIGTERM)
    def finish_and_stop(job):
        signal.getsignal(signal.SIGTERM)(signal.SIGTERM, None)
        execute_job(job)
    with patch("knext.content.management.commands.content_worker.execute_job", side_effect=finish_and_stop):
        call_command("content_worker")
    assert list(ImportJob.objects.order_by("created_at").values_list("status", flat=True)) == ["succeeded", "queued"]
    assert signal.getsignal(signal.SIGTERM) == original


def test_selected_jobs_cancel_together_and_keep_history(environment):
    _, _, user, browser = environment
    batches = [enqueue_paths(["Books/md/test.md"], "import", user) for _ in range(2)]
    ids = list(ImportJob.objects.values_list("pk", flat=True))
    for batch in batches:
        page = browser.get(f"/content/batches/{batch.pk}/")
        assert b"Alle wartenden Jobs dieser Seite" in page.content
        assert f'value="{batch.jobs.get().pk}"'.encode() in page.content
    response = browser.post("/content/jobs/cancel-selected/?status=queued", {"jobs": [*ids, ids[0]]})
    assert response.status_code == 302
    assert response.url == "/content/jobs/?status=queued"
    assert ImportJob.objects.filter(status="cancelled").count() == 2
    assert not JobAttempt.objects.exists()
    assert not SourceAsset.objects.exists()
    call_command("content_worker", once=True)
    assert not SourceAsset.objects.exists()


def test_selected_cancel_rejects_stale_selection_atomically(environment):
    _, _, user, browser = environment
    enqueue_paths(["Books/md/test.md"], "import", user)
    second = enqueue_paths(["Books/md/test.md"], "import", user).jobs.get()
    claim_job(second.pk)
    response = browser.post("/content/jobs/cancel-selected/", {"jobs": list(ImportJob.objects.values_list("pk", flat=True))})
    assert response.status_code == 409
    assert ImportJob.objects.filter(status="queued").count() == 1
    assert ImportJob.objects.filter(status="running").count() == 1
    assert not ImportJob.objects.filter(status="cancelled").exists()


def test_selected_cancel_enforces_owner_staff_batch_and_csrf(environment):
    _, _, user, browser = environment
    batch = enqueue_paths(["Books/md/test.md"], "import", user)
    job = batch.jobs.get()
    stranger = User.objects.create_user("stranger")
    other = Client()
    other.force_login(stranger)
    assert other.post("/content/jobs/cancel-selected/", {"jobs": [job.pk]}).status_code == 403
    assert b'name="jobs"' not in other.get("/content/jobs/").content
    wrong_batch = enqueue_paths(["Books/md/test.md"], "import", user)
    assert browser.post("/content/jobs/cancel-selected/", {"jobs": [job.pk], "batch": wrong_batch.pk}).status_code == 400
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(user)
    assert csrf.post("/content/jobs/cancel-selected/", {"jobs": [job.pk]}).status_code == 403
    stranger.is_staff = True
    stranger.save()
    response = other.post("/content/jobs/cancel-selected/", {"jobs": [job.pk], "batch": batch.pk})
    assert response.status_code == 302 and response.url == f"/content/batches/{batch.pk}/"
    job.refresh_from_db()
    assert job.status == "cancelled"


@pytest.mark.parametrize("values", [[], ["bad"], ["00000000-0000-4000-8000-000000000000"], [str(uuid.uuid4()) for _ in range(101)]])
def test_selected_cancel_rejects_invalid_or_unbounded_selection(environment, values):
    _, _, _, browser = environment
    assert browser.post("/content/jobs/cancel-selected/", {"jobs": values}).status_code == 400
    assert browser.get("/content/jobs/cancel-selected/").status_code == 405


def test_file_counts_filters_and_batch_page(environment):
    _, _, user, browser = environment
    job = run_batch(user)
    catalog, errors, summary = file_catalog()
    assert not errors
    assert len(catalog) == 4
    assert {row["area"]: row["files"] for row in summary} == {"provisioned": 1, "original": 1, "extraction": 2}
    response = browser.get("/content/files/", {"area": "extraction", "q": ".md"})
    assert response.status_code == 200
    assert response.context["page_obj"].paginator.count == 1
    assert browser.get("/content/jobs/", {"status": "succeeded"}).context["page_obj"].paginator.count == 1
    assert browser.get(f"/content/batches/{job.batch_id}/").status_code == 200
    assert browser.get(f"/content/jobs/{job.pk}/").status_code == 200
    assert browser.get("/content/sources/").context["page_obj"].paginator.count == 1


def test_batch_ui_validates_selection_permissions_and_csrf(environment):
    _, _, _, browser = environment
    response = browser.post("/content/jobs/batch/", {"kind": "import", "paths": ["Books/md/test.md"]})
    assert response.status_code == 302
    job = ImportJob.objects.get()
    other = Client()
    other.force_login(User.objects.create_user("other"))
    assert other.post(f"/content/jobs/{job.pk}/control/", {"action": "cancel"}).status_code == 403
    response = browser.post("/content/jobs/batch/", {"kind": "extract", "sources": ["invalid"]}, follow=True)
    assert response.status_code == 200
    assert "Ungültige Quellenauswahl." in response.content.decode()
    response = browser.post("/content/jobs/batch/?format=md", {"kind": "import", "paths": []}, follow=True)
    assert response.redirect_chain == [("/content/sources/?format=md", 302)]
    assert response.status_code == 200 and b'role="alert"' in response.content
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(job.batch.created_by)
    assert csrf.post("/content/jobs/batch/", {"kind": "import", "paths": ["Books/md/test.md"]}).status_code == 403


def test_inventory_tables_submit_their_own_selection(environment):
    _, _, user, browser = environment
    job = run_batch(user)
    page = BeautifulSoup(browser.get("/content/sources/").content, "html.parser")
    headers = page.select("thead input[data-batch-toggle]")
    assert {header["data-batch-toggle"] for header in headers} == {"file-batch", "source-batch"}
    for form_id, field, value in [
        ("file-batch", "paths", "Books/md/test.md"),
        ("source-batch", "sources", str(job.source_id)),
    ]:
        form = page.find("form", id=form_id)
        assert form is not None
        checkbox = page.find("input", attrs={"form": form_id, "name": field})
        assert checkbox["value"] == value
        action = form.find("select", attrs={"name": "kind"}).find_all("option")[-1]["value"]
        response = browser.post(form["action"], {"kind": action, field: [checkbox["value"]]})
        assert response.status_code == 302 and "/content/batches/" in response.url
        assert ImportJob.objects.order_by("-created_at").first().kind == action


def test_epub_batch_creates_new_browsable_domain_even_with_web_registry_cached(environment):
    root, _, user, browser = environment
    registry()  # Web process knew only the original Markdown domain.
    path = root / "NewBooks/epub/book.epub"
    path.parent.mkdir(parents=True)
    with ZipFile(path, "w") as archive:
        archive.writestr("mimetype", "application/epub+zip")
        archive.writestr("META-INF/container.xml", '<container><rootfiles><rootfile full-path="book.opf" media-type="application/oebps-package+xml"/></rootfiles></container>')
        archive.writestr("book.opf", '''<package version="3.0" unique-identifier="id">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/"><dc:title>Book</dc:title>
<dc:identifier id="id">synthetic</dc:identifier></metadata><manifest>
<item id="a" href="a.xhtml" media-type="application/xhtml+xml"/>
<item id="b" href="b.xhtml" media-type="application/xhtml+xml"/>
</manifest><spine><itemref idref="b"/><itemref idref="a"/></spine></package>''')
        for letter in ["a", "b"]:
            archive.writestr(f"{letter}.xhtml", f"<html><body><h1>{letter}</h1><h2>Section</h2><p>Text.</p></body></html>")
    batch = enqueue_paths(["NewBooks/epub/book.epub"], "import", user)
    with patch("knext.content.artifacts.registry.cache_clear"):
        call_command("content_worker", once=True)
    job = batch.jobs.get()
    assert job.status == "succeeded"
    assert list(job.run.documents.values_list("source_locator", flat=True)) == ["b.xhtml", "a.xhtml"]
    assert len(list((root / f"NewBooks/md/_extractions/{job.run_id}").glob("*.md"))) == 2
    response = browser.get("/wiki/api", {"domain": "ki:NewBooks"})
    assert response.status_code == 200
    assert any(block["title"] == "Section" for block in response.json()["blocks"])


def test_selected_worker_job_errors_are_explicit(environment):
    _, file, user, _ = environment
    with pytest.raises(CommandError, match="existiert nicht"):
        call_command("content_worker", job="00000000-0000-4000-8000-000000000000")
    job = enqueue_paths(["Books/md/test.md"], "import", user).jobs.get()
    file.write_text("# changed")
    with pytest.raises(CommandError, match="fehlgeschlagen"):
        call_command("content_worker", job=str(job.pk))


def test_symlinked_artifact_directory_is_never_followed(environment, tmp_path):
    root, _, user, _ = environment
    outside = tmp_path / "outside"
    outside.mkdir()
    (root / "Books/orig").symlink_to(outside, target_is_directory=True)
    batch = enqueue_paths(["Books/md/test.md"], "import", user)
    call_command("content_worker", once=True)
    assert batch.jobs.get().status == "failed"
    assert not list(outside.iterdir())
    assert not FilesystemArtifact.objects.exists()


def test_snapshot_manifests_are_downloaded_only_when_verifiable(environment):
    root, _, user, browser = environment
    run_batch(user)
    manifest = FilesystemArtifact.objects.get(kind="manifest")
    response = browser.get(f"/content/artifacts/{manifest.pk}/")
    assert response.status_code == 200 and response.json()["schema"] == "knext-extraction-v1"
    path = root / manifest.relative_path
    path.chmod(0o600)
    path.write_text("{}")
    assert browser.get(f"/content/artifacts/{manifest.pk}/").status_code == 409
