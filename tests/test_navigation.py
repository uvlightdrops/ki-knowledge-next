"""The host menu is consistent across embedded and native application pages."""

from types import SimpleNamespace
from uuid import uuid4

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, RequestFactory
from django.urls import resolve, reverse

from knext.content.rendering import render_output
from knext.content.services import import_upload
from knext.navigation import navigation

pytestmark = pytest.mark.django_db


@pytest.fixture
def client():
    browser = Client()
    browser.force_login(User.objects.create_superuser("navigator", password="test"))
    return browser


def nav_state(path, staff=True):
    request = RequestFactory().get(path)
    request.user = SimpleNamespace(is_staff=staff)
    request.resolver_match = resolve(path)
    request.active_domain = "Dokumentation"
    return navigation(request)


@pytest.mark.parametrize("view,group,active", [
    ("content:index", "INPUT", "Inhalte"),
    ("content:inventory", "INPUT", "Quellen"),
    ("content:files", "INPUT", "Dateien"),
    ("content:jobs", "INPUT", "Jobs"),
    ("content:output", "OUTPUT", "Statische Ausgabe"),
    ("content:documents", "INTERN", "Werkstatt"),
    ("content:editor-index", "INTERN", "Editor · Entwurf"),
    ("content:editor-wide-index", "INTERN", "Editor breit · Entwurf"),
    ("content:collections", "INTERN", "Zusammenstellungen"),
    ("content:resources", "INTERN", "Ressourcen"),
    ("content:relation-types", "INTERN", "Beziehungstypen"),
    ("workbench-demo", "INTERN", "Demo"),
    ("domains", "Einstellungen", "Domänen"),
    ("wissenswiki:workspace", "INTERN", "Arbeitsraum"),
    ("wissenswiki:graph", "INTERN", "Wissensnetz"),
    ("wissenswiki:graph-header", "INTERN", "Wissensnetz"),
    ("wissenswiki:settings", "Einstellungen", "Netz-Einstellungen"),
    ("admin:index", "Administration", "Django-Administration"),
    ("admin:auth_user_changelist", "Administration", "Django-Administration"),
])
def test_shared_navigation_group_and_active_area(client, view, group, active):
    response = client.get(reverse(view), {} if view.startswith("admin:") else {"domain": "Dokumentation"})
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    assert len(soup.select(".knext-app-navigation")) == 1
    primary = soup.select_one('nav[aria-label="Hauptnavigation"]')
    assert [a.get_text() for a in primary.select("a")] == [
        "INPUT", "INTERN", "OUTPUT", "Administration", "Einstellungen",
    ]
    assert primary.select_one("[aria-current]").get_text() == group
    secondary = soup.select_one(".knext-secondary:not([hidden])")
    assert secondary["aria-label"] == f"{group} – Unternavigation"
    assert secondary.select_one("[aria-current]").get_text() == active
    assert soup.select_one('.knext-menu summary[aria-label="Hauptmenü"]')
    assert soup.select_one('script[src="/static/knext/navigation.js"]')
    assert soup.select_one('link[href="/static/knext/navigation.css"]')
    assert soup.select_one('form.knext-domain-switcher input[name="csrfmiddlewaretoken"]')
    assert "Prototyp · Import" not in soup.get_text()


@pytest.mark.parametrize("view,args,group,item,workshop", [
    ("content:run", [uuid4()], "input", "Inhalte", False),
    ("content:materialize", [uuid4()], "input", "Inhalte", False),
    ("content:artifact", [1], "input", "Dateien", False),
    ("content:source", [uuid4()], "input", "Quellen", False),
    ("content:job", [uuid4()], "input", "Jobs", False),
    ("content:document", [uuid4()], "intern", "Werkstatt", False),
    ("content:editor", [uuid4()], "intern", "Editor · Entwurf", False),
    ("content:editor-restore", [uuid4()], "intern", "Editor · Entwurf", False),
    ("content:editor-wide", [uuid4()], "intern", "Editor breit · Entwurf", False),
    ("content:editor-wide-restore", [uuid4()], "intern", "Editor breit · Entwurf", False),
    ("content:revision", [uuid4(), 1], "intern", "Werkstatt", False),
    ("content:collection", [uuid4()], "intern", "Zusammenstellungen", True),
    ("content:collection-create", [], "intern", "Zusammenstellungen", True),
    ("content:collection-edit", [uuid4()], "intern", "Zusammenstellungen", True),
    ("content:resource", [uuid4()], "intern", "Ressourcen", True),
    ("content:folder-create", [], "intern", "Ressourcen", True),
    ("content:relation-types", [], "intern", "Beziehungstypen", True),
    ("content:relation-delete", [1], "intern", "Beziehungstypen", True),
    ("content:site-download", [], "output", "Statische Ausgabe", False),
])
def test_detail_and_action_routes_match_exact_group(view, args, group, item, workshop):
    state = nav_state(reverse(view, args=args))
    selected = [g for g in state["app_navigation_groups"] if g["active"]]
    assert [g["key"] for g in selected] == [group]
    assert [entry["label"] for entry in selected[0]["items"] if entry["active"]] == [item]
    assert state["app_workshop_context"] is workshop


def test_menu_preserves_domain_for_graph_and_settings_but_not_workspace(client):
    response = client.get(reverse("wissenswiki:settings"), {"domain": "Dokumentation"})
    menu = BeautifulSoup(response.content, "html.parser").select_one(".knext-menu")
    links = {link.get_text(): link["href"] for link in menu.select("a")}
    assert links["Wissensnetz"] == "/wiki/graph-header/?domain=Dokumentation"
    assert links["Netz-Einstellungen"] == "/wiki/settings/?domain=Dokumentation"
    assert links["Arbeitsraum"] == "/wiki/"
    assert links["Inhalte"] == "/content/"
    assert links["Statische Ausgabe"] == reverse("content:output")


@pytest.mark.parametrize("view", [
    "content:collections", "content:resources", "content:relation-types",
])
def test_internal_graph_pages_keep_workshop_context(client, view):
    soup = BeautifulSoup(client.get(reverse(view)).content, "html.parser")
    secondary = soup.select_one('.knext-secondary[data-group="intern"]')
    assert secondary.select_one(".knext-workshop-context").get_text() == "Werkstatt"
    assert secondary.select_one("[aria-current]").get_text() != "Werkstatt"


def test_nonstaff_navigation_hides_administration():
    browser = Client()
    browser.force_login(User.objects.create_user("reader"))
    soup = BeautifulSoup(browser.get(reverse("content:index")).content, "html.parser")
    assert not soup.select_one('.knext-app-navigation a[href="/admin/"]')
    assert not soup.select_one('.knext-primary [data-group="admin"]')
    assert browser.get(reverse("admin:index")).status_code == 302


def test_menu_is_on_document_and_run_but_not_static_export(client):
    user = User.objects.get(username="navigator")
    run, _ = import_upload(SimpleUploadedFile("menu.md", b"# Menu\n\nBody"), "Dokumentation", user)
    document = run.documents.get()
    for view, pk, group, label in [
        ("content:run", run.pk, "INPUT", "Inhalte"),
        ("content:document", document.pk, "INTERN", "Werkstatt"),
    ]:
        soup = BeautifulSoup(client.get(reverse(view, args=[pk])).content, "html.parser")
        assert soup.select_one('.knext-primary [aria-current]').get_text() == group
        assert soup.select_one('.knext-secondary:not([hidden]) [aria-current]').get_text() == label
    assert "knext-app-navigation" not in render_output(document.revisions.get())


def test_output_page_link_and_all_groups_available_without_script(client):
    soup = BeautifulSoup(client.get(reverse("content:index")).content, "html.parser")
    assert not soup.select_one("#static-output")
    assert not soup.select_one('a[href*="/content/export/"]')
    assert soup.select_one('.knext-primary a[data-group="output"]')["href"] == reverse("content:output")
    assert soup.select_one('.knext-secondary[data-group="output"][hidden] a')["href"] == reverse("content:output")
    assert len(soup.select(".knext-menu-group")) == 5
    assert soup.select_one('.knext-menu a[href="/content/sources/"]')
    assert soup.select_one('.knext-menu a[href="/content/documents/"]')


def test_navigation_assets_are_discoverable():
    from django.contrib.staticfiles.finders import find

    assert find("knext/navigation.css")
    assert find("knext/navigation.js")


def test_workshop_list_links_documents_and_preserves_approval_state(client):
    user = User.objects.get(username="navigator")
    run, _ = import_upload(SimpleUploadedFile("direct.md", b"# Direct\n\nBody"), "Dokumentation", user)
    document = run.documents.get()
    response = client.get(reverse("content:documents"))
    soup = BeautifulSoup(response.content, "html.parser")
    assert response.status_code == 200
    assert soup.select_one(f'a[href="{reverse("content:document", args=[document.pk])}"]')
    assert soup.select_one(f'a[href="{reverse("content:source", args=[run.source_id])}"]')
    assert "Noch nicht freigegeben" in soup.get_text()
    assert Client().get(reverse("content:documents")).status_code == 302
