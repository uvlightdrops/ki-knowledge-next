import hashlib
import json

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.contrib.staticfiles.finders import find
from django.test import Client
from django.urls import reverse

pytestmark = pytest.mark.django_db


@pytest.fixture
def browser():
    client = Client()
    client.force_login(User.objects.create_user("demo-reader"))
    return client


def test_demo_shell_loads_original_assets_and_explicit_warning(browser):
    response = browser.get(reverse("workbench-demo"))
    soup = BeautifulSoup(response.content, "html.parser")
    bootstrap = json.loads(soup.select_one("#workbench-bootstrap").string)
    assert bootstrap["domain"] == "UI-Demo"
    assert bootstrap["canCapture"] is True
    assert soup.select_one("#workbench-root")
    assert "kein Schreibzugriff" in soup.get_text()
    assert find(soup.select_one('script[type="module"]')["src"].removeprefix("/static/"))
    assert find("django_site/workbench/THIRD-PARTY-NOTICES.txt")
    assert find("django_site/workbench/assets/editor.worker-DCX81QGM.js")
    assert "style-src 'self' 'unsafe-inline'" in response["Content-Security-Policy"]


def test_demo_startup_lists_and_document_contract(browser):
    base = "/workbench/demo-api/"
    documents = browser.get(base + "documents", {"domain": "UI-Demo"}).json()["documents"]
    assert len(documents) == 2
    for document in documents:
        resource = base + "documents/" + document["id"]
        full = browser.get(resource, {"domain": "UI-Demo"}).json()
        revision = full["revision"]
        assert revision["content_sha256"] == hashlib.sha256(revision["text"].encode()).hexdigest()
        annotation = full["annotations"][0]
        assert revision["text"][annotation["start"]:annotation["end"]] == annotation["exact"]
        assert browser.get(resource + "/revisions", {"domain": "UI-Demo"}).json()["revisions"] == [revision]
        assert browser.get(resource + "/revisions/" + revision["id"], {"domain": "UI-Demo"}).json() == full
    for resource, key in [
        ("documents?archived=1&", "documents"), ("annotations?archived=1&", "annotations"),
        ("relations?", "relations"),
    ]:
        assert browser.get(base + resource + "domain=UI-Demo").json()[key] == []
    assert browser.get(base + "annotations", {"domain": "UI-Demo"}).status_code == 200
    assert browser.get(base + "sources", {"domain": "UI-Demo"}).json()["sources"][0]["registered"]


@pytest.mark.parametrize("method", ["post", "put", "patch", "delete"])
def test_demo_rejects_all_writes_without_changing_fixture(browser, method):
    before = browser.get("/workbench/demo-api/documents", {"domain": "UI-Demo"}).json()
    response = getattr(browser, method)("/workbench/demo-api/documents", {"title": "Changed"})
    assert response.status_code == 405
    assert "ohne Schreibzugriff" in response.json()["error"]["message"]
    assert browser.get("/workbench/demo-api/documents", {"domain": "UI-Demo"}).json() == before


def test_demo_missing_provider_and_unknown_data_are_explicit(browser):
    response = browser.get("/workbench/demo-api/provider", {"domain": "UI-Demo"})
    assert response.status_code == 501
    assert "nicht verbunden" in response.json()["error"]["message"]
    assert browser.get("/workbench/demo-api/documents", {"domain": "Dokumentation"}).status_code == 400
    assert browser.get("/workbench/demo-api/unknown", {"domain": "UI-Demo"}).status_code == 404
    assert Client().get("/workbench/demo-api/documents").status_code == 401
    assert Client().get(reverse("workbench-demo")).status_code == 302


def test_dark_theme_is_loaded_after_workspace_styles_only_in_workspace(browser):
    soup = BeautifulSoup(browser.get(reverse("wissenswiki:workspace")).content, "html.parser")
    styles = [link["href"] for link in soup.select('link[rel="stylesheet"]')]
    assert styles.index("/static/wissenswiki/workspace.css") < styles.index("/static/knext/theme.css")
    assert find("knext/theme.css")
    assert "/static/knext/theme.css" not in browser.get(reverse("content:index")).content.decode()
