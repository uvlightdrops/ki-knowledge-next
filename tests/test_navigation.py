"""The host menu is consistent across embedded and native application pages."""

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from knext.content.rendering import render_output
from knext.content.services import import_upload

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    browser = Client()
    browser.force_login(User.objects.create_superuser("navigator", password=None))
    return browser


@pytest.mark.parametrize("view,active", [
    ("content:index", "Import und Inhalte"),
    ("content:import", "Import und Inhalte"),
    ("wissenswiki:workspace", "Arbeitsraum"),
    ("wissenswiki:graph", "Wissensnetz"),
    ("wissenswiki:graph-header", "Wissensnetz"),
    ("wissenswiki:settings", "Netz-Einstellungen"),
    ("admin:index", "Administration"),
    ("admin:auth_user_changelist", "Administration"),
])
def test_menu_is_present_once_with_current_area(client, view, active):
    response = client.get(reverse(view), {} if view.startswith("admin:") else {"domain": "Dokumentation"})
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    assert len(soup.select(".knext-menu")) == 1
    navigation = soup.select_one(".knext-menu nav")
    assert [link.get_text() for link in navigation.select("a")] == [
        "Import und Inhalte", "Wissensnetz", "Arbeitsraum", "Netz-Einstellungen", "Administration",
    ]
    assert navigation.select_one('[aria-current="page"]').get_text() == active
    assert soup.select_one(".knext-menu summary")["aria-label"] == "Hauptmenü"
    assert soup.select_one('script[src="/static/knext/navigation.js"]')
    assert soup.select_one('link[href="/static/knext/navigation.css"]')


def test_menu_preserves_domain_for_graph_and_settings_but_not_workspace(client):
    response = client.get(reverse("wissenswiki:settings"), {"domain": "Doku & mehr"})
    menu = BeautifulSoup(response.content, "html.parser").select_one(".knext-menu")
    links = {link.get_text(): link["href"] for link in menu.select("a")}
    assert links["Wissensnetz"] == "/wiki/graph-header/?domain=Doku+%26+mehr"
    assert links["Netz-Einstellungen"] == "/wiki/settings/?domain=Doku+%26+mehr"
    assert links["Arbeitsraum"] == "/wiki/"
    assert links["Import und Inhalte"] == "/content/"


def test_nonstaff_menu_hides_administration():
    browser = Client()
    browser.force_login(User.objects.create_user("reader"))
    soup = BeautifulSoup(browser.get(reverse("content:index")).content, "html.parser")
    assert not soup.select_one('.knext-menu a[href="/admin/"]')
    assert len(soup.select(".knext-menu a")) == 4


def test_menu_is_on_document_and_run_but_not_static_export(client):
    user = User.objects.get(username="navigator")
    run, _ = import_upload(SimpleUploadedFile("menu.md", b"# Menu\n\nBody"), "Dokumentation", user)
    document = run.documents.get()
    for view, pk in [("content:run", run.pk), ("content:document", document.pk)]:
        soup = BeautifulSoup(client.get(reverse(view, args=[pk])).content, "html.parser")
        assert soup.select_one('.knext-menu a[aria-current="page"]').get_text() == "Import und Inhalte"
    assert "knext-menu" not in render_output(document.revisions.get())


def test_navigation_assets_are_discoverable():
    from django.contrib.staticfiles.finders import find

    assert find("knext/navigation.css")
    assert find("knext/navigation.js")
