from unittest.mock import patch

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.test import Client

from knext.content.jobs import claim_job, execute_job
from knext.content.models import ActiveDomain, ManagedDomain, SourceAsset
from knext.domains import domain_registry
from wissenswiki.config import registry

pytestmark = pytest.mark.django_db


@pytest.fixture
def environment(tmp_path, settings):
    data = tmp_path / "data"
    data.mkdir()
    (tmp_path / "workspace").mkdir()
    (tmp_path / "relations").mkdir()
    settings.WISSENSWIKI = {
        "WORKSPACE": str(tmp_path / "workspace"),
        "MARKDOWN_DATA": {"root": str(data), "relations": str(tmp_path / "relations"), "prefix": "ki:", "subdir": "md"},
    }
    staff = User.objects.create_user("domain-admin", is_staff=True)
    reader = User.objects.create_user("domain-reader")
    admin_browser = Client()
    admin_browser.force_login(staff)
    reader_browser = Client()
    reader_browser.force_login(reader)
    return data, staff, reader, admin_browser, reader_browser


def test_staff_creates_persistent_empty_domain_visible_to_reader_and_wiki(environment):
    data, staff, reader, admin, browser = environment
    assert admin.post("/domains/", {"folder": "Books"}).status_code == 302
    assert (data / "Books/md").is_dir()
    assert ManagedDomain.objects.get().created_by == staff
    assert "ki:Books" in domain_registry().domains
    assert "ki:Books" not in registry().domains  # No mutable shared cache injection.
    assert "ki:Books" in browser.get("/domains/").content.decode()
    snapshot = browser.get("/wiki/api", {"domain": "ki:Books"})
    assert snapshot.status_code == 200
    assert snapshot.json()["blocks"] == []
    assert browser.get("/wiki/graph-header/", {"domain": "ki:Books"}).status_code == 200


def test_personal_switcher_persists_per_user_across_sessions(environment):
    _, _, reader, admin, browser = environment
    admin.post("/domains/", {"folder": "Books"})
    response = browser.post("/domains/select/", {"domain": "ki:Books", "next": "/wiki/graph-header/?domain=old&page=2"})
    assert response.url == "/wiki/graph-header/"
    assert browser.get(response.url).url == "/wiki/graph-header/?domain=ki%3ABooks"
    soup = BeautifulSoup(browser.get("/content/").content, "html.parser")
    assert soup.select_one("#knext-domain option[selected]")["value"] == "ki:Books"
    assert not soup.select_one('input[type="file"]')
    output = BeautifulSoup(browser.get("/content/output/").content, "html.parser")
    assert output.select_one("#knext-domain option[selected]")["value"] == "ki:Books"
    other_session = Client()
    other_session.force_login(reader)
    assert other_session.get("/wiki/settings/").url.endswith("?domain=ki%3ABooks")
    assert not ActiveDomain.objects.filter(user__username="domain-admin").exists()
    browser.post("/domains/select/", {"domain": "", "next": "/content/"})
    assert ActiveDomain.objects.get(user=reader).name == ""
    assert browser.get("/wiki/").status_code == 200


def test_domain_lists_and_batch_import_use_same_folder_identity(environment):
    data, _, _, admin, browser = environment
    for folder in ["Books", "Notes"]:
        admin.post("/domains/", {"folder": folder})
        (data / folder / "md/test.md").write_text(f"# {folder}\n\nContent")
        response = browser.post("/content/jobs/batch/", {
            "kind": "import", "paths": [f"{folder}/md/test.md"],
        })
        assert response.status_code == 302
        execute_job(claim_job())
    assert set(SourceAsset.objects.values_list("domain", flat=True)) == {"Books", "Notes"}
    browser.post("/domains/select/", {"domain": "ki:Books", "next": "/content/"})
    assert browser.get("/content/").context["runs"].count() == 1
    assert browser.get("/content/documents/").context["documents"].count() == 1
    assert len(browser.get("/content/sources/").context["sources"]) == 1


def test_domain_creation_validates_staff_paths_and_existing_folders(environment):
    data, _, _, admin, browser = environment
    assert browser.post("/domains/", {"folder": "Books"}).status_code == 403
    for invalid in ["../escape", ".hidden", "two/parts", "space name"]:
        assert admin.post("/domains/", {"folder": invalid}).status_code == 400
    (data / "Existing").mkdir()
    (data / "Existing/keep.txt").write_text("keep")
    assert admin.post("/domains/", {"folder": "Existing"}).status_code == 400
    assert (data / "Existing/keep.txt").read_text() == "keep"
    assert not ManagedDomain.objects.exists()
    assert admin.post("/domains/", {"folder": "Books"}).status_code == 302
    assert admin.post("/domains/", {"folder": "Books"}).status_code == 400


def test_creation_filesystem_failure_rolls_back_database_and_owned_directories(environment):
    data, _, _, admin, _ = environment
    original_mkdir = __import__("os").mkdir

    def fail_subdir(path, *args, **kwargs):
        if path == "md":
            raise PermissionError("fixture denied")
        return original_mkdir(path, *args, **kwargs)

    with patch("knext.domains.os.mkdir", side_effect=fail_subdir):
        response = admin.post("/domains/", {"folder": "Failure"})
    assert response.status_code == 400
    assert "fixture denied" in response.content.decode()
    assert not ManagedDomain.objects.exists()
    assert not (data / "Failure").exists()


def test_invalid_switch_and_redirect_do_not_change_selection(environment):
    _, _, reader, admin, browser = environment
    admin.post("/domains/", {"folder": "Books"})
    assert browser.post("/domains/select/", {"domain": "missing"}).status_code == 400
    assert browser.post("/domains/select/", {"domain": "ki:Books", "next": "https://example.com/"}).status_code == 400
    assert not ActiveDomain.objects.filter(user=reader).exists()
    assert Client().get("/domains/").status_code == 302
    csrf_browser = Client(enforce_csrf_checks=True)
    csrf_browser.force_login(reader)
    assert csrf_browser.post("/domains/select/", {"domain": "ki:Books"}).status_code == 403


def test_short_domain_url_is_normalized_for_wiki_api_without_saving_selection(environment):
    _, _, reader, admin, browser = environment
    admin.post("/domains/", {"folder": "Books"})
    response = browser.get("/wiki/graph-header/", {"domain": "Books"})
    assert response.status_code == 302
    assert response.url == "/wiki/graph-header/?domain=ki%3ABooks"
    assert browser.get(response.url).status_code == 200
    assert not ActiveDomain.objects.filter(user=reader).exists()
    assert browser.get("/wiki/api", {"domain": "ki:Books"}).status_code == 200
