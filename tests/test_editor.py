"""Editor workflows preserve originals, revision history and conflict buffers."""

import json

from bs4 import BeautifulSoup
import pytest
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from knext.content.models import ContentRevision
from knext.content.services import approve, import_upload, revise

pytestmark = pytest.mark.django_db
HEADER = "---\ntags: [one]\n---\n"
BODY = "# Title\n\nIntro.\n\n## First [first]\n\n😀 Text.\n\n### Nested [nested]\n\nDetail.\n"


@pytest.fixture
def document():
    user = User.objects.create_superuser("editor", "editor@example.org", "test-password")
    run, _ = import_upload(SimpleUploadedFile("editor.md", (HEADER + BODY).encode()), "Books", user)
    return run.documents.get()


@pytest.fixture
def browser(document):
    client = Client()
    client.force_login(User.objects.get(username="editor"))
    return client


def payload(document, **overrides):
    return {"expected": document.revision_number, "title": "Title", "body": BODY, **overrides}


def test_editor_landing_navigation_and_empty_state(browser, document):
    response = browser.get(reverse("content:editor-index"))
    soup = BeautifulSoup(response.content, "html.parser")
    assert soup.select_one(f'a[href="{reverse("content:editor", args=[document.pk])}"]')
    assert soup.select_one('.knext-secondary [aria-current]').get_text() == "Editor · Entwurf"
    response = browser.get(reverse("content:editor-index"), {"q": "no-match"})
    assert "Keine passenden Dokumente" in response.content.decode()


def test_editor_shows_source_text_safe_preview_and_optional_network(browser, document):
    count = ContentRevision.objects.count()
    response = browser.get(reverse("content:editor", args=[document.pk]))
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    assert soup.select_one("#editor-network").has_attr("hidden")
    assert soup.select_one("#id_body").get_text().removeprefix("\n") == BODY
    assert soup.select_one("#editor-preview-body strong") is None
    assert soup.select_one("#editor-preview-body h2").get_text() == "First [first]"
    outline = json.loads(soup.select_one("#editor-outline-data").get_text())
    assert outline[0]["title"] == "First"
    assert outline[1]["parent"] == 0
    assert outline[1]["start"] == 9
    assert ContentRevision.objects.count() == count
    assert soup.select_one('script[src="/static/content/editor.js"]')


def test_editor_save_and_restore_preserve_header_history_and_approval(browser, document):
    user = User.objects.get(username="editor")
    approve(document, expected=1, user=user)
    original = document.revisions.get(number=1)
    url = reverse("content:editor", args=[document.pk])
    response = browser.post(url, payload(document, body=BODY + "\nChanged."))
    assert response.status_code == 302 and response.url == url
    document.refresh_from_db()
    assert document.revision_number == 2
    assert document.approved_revision_id == original.pk
    assert document.revisions.get(number=2).yaml_header == HEADER
    soup = BeautifulSoup(browser.get(url).content, "html.parser")
    assert soup.select_one("#backup-number option")["value"] == "1"
    response = browser.post(reverse("content:editor-restore", args=[document.pk]),
                            payload(document, number=1, body=""))
    assert response.status_code == 302 and response.url == url
    document.refresh_from_db()
    restored = document.revisions.get(number=3)
    assert restored.body == BODY
    assert restored.restored_from_id == original.pk
    assert restored.parent.number == 2
    assert document.approved_revision_id == original.pk
    assert document.revisions.count() == 3
    assert document.extraction.markdown == HEADER + BODY


@pytest.mark.parametrize("action", ["editor", "editor-restore"])
def test_editor_conflict_keeps_submitted_buffer_and_old_expectation(browser, document, action):
    user = User.objects.get(username="editor")
    revise(document, expected=1, title="Other", body=BODY + "\nOther change.", user=user)
    response = browser.post(reverse(f"content:{action}", args=[document.pk]),
                            payload(document, expected=1, body="My unsaved text", number=1))
    # A restore requires a historical version older than the expected head.
    assert response.status_code == (400 if action == "editor-restore" else 409)
    soup = BeautifulSoup(response.content, "html.parser")
    assert soup.select_one("#id_body").get_text().removeprefix("\n") == "My unsaved text"
    assert soup.select_one('input[name="expected"]')["value"] == "1"
    assert document.revisions.count() == 2
    saved = json.loads(soup.select_one("#editor-saved-data").get_text())
    assert saved["body"].endswith("Other change.")


def test_restore_conflict_does_not_replace_editor_buffer(browser, document):
    user = User.objects.get(username="editor")
    revise(document, expected=1, title="Two", body=BODY + "Two", user=user)
    revise(document, expected=2, title="Three", body=BODY + "Three", user=user)
    response = browser.post(reverse("content:editor-restore", args=[document.pk]),
                            payload(document, expected=2, number=1, body="Keep me"))
    assert response.status_code == 409
    soup = BeautifulSoup(response.content, "html.parser")
    assert soup.select_one("#id_body").get_text().removeprefix("\n") == "Keep me"
    assert document.revisions.count() == 3


def test_preview_is_sanitized_updates_outline_and_never_saves(browser, document):
    count = ContentRevision.objects.count()
    response = browser.post(reverse("content:editor-preview"), payload(document,
        body="## New\n\n**Bold**\n\n<script>alert(1)</script>\n\n[Bad](javascript:alert%281%29)"))
    assert response.status_code == 200
    result = response.json()
    assert "<strong>Bold</strong>" in result["html"]
    assert "<script" not in result["html"] and "javascript:" not in result["html"]
    assert result["outline"][0]["title"] == "New"
    assert ContentRevision.objects.count() == count
    document.refresh_from_db()
    assert document.revision_number == 1


@pytest.mark.parametrize("body", ["", "---\nfoo: bar\n---\nText", "## A [same]\n## B [same]"])
def test_preview_rejects_invalid_body_explicitly(browser, document, body):
    response = browser.post(reverse("content:editor-preview"), payload(document, body=body))
    assert response.status_code == 400
    assert "errors" in response.json() or "error" in response.json()


def test_editor_requires_authentication_and_csrf(document):
    url = reverse("content:editor", args=[document.pk])
    assert Client().get(url).status_code == 302
    assert Client().get(reverse("content:editor-index")).status_code == 302
    browser = Client(enforce_csrf_checks=True)
    browser.force_login(User.objects.get(username="editor"))
    assert browser.post(url, payload(document)).status_code == 403
    assert browser.post(reverse("content:editor-preview"), payload(document)).status_code == 403
    assert browser.post(reverse("content:editor-restore", args=[document.pk]),
                        payload(document, number=1)).status_code == 403
