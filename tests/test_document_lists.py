"""Shared text lists filter and sort before pagination without mixing provenance."""

from urllib.parse import parse_qs, urlsplit

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from knext.content.models import ActiveDomain, SourceRegistration
from knext.content.services import approve, import_upload, revise

pytestmark = pytest.mark.django_db


@pytest.fixture
def rows():
    user = User.objects.create_superuser("list-editor", "lists@example.org", "test-password")
    documents = []
    for title, domain, filename, folder in [
        ("Zulu", "Books", "z.md", "md/old"),
        ("alpha", "Books", "a.md", "md/current/deep"),
        ("Beta", "Other", "b.md", None),
    ]:
        run, _ = import_upload(SimpleUploadedFile(filename, f"# {title}\n\n{title}.".encode()), domain, user)
        document = run.documents.get()
        if folder:
            SourceRegistration.objects.create(
                source=run.source, relative_path=f"{domain}/{folder}/{filename}", registered_by=user,
            )
        documents.append(document)
    revise(documents[0], expected=1, title="Zulu", body="# Zulu\n\nChanged.", user=user)
    approve(documents[0], expected=2, user=user)
    client = Client()
    client.force_login(user)
    return client, documents, user


@pytest.mark.parametrize("view", ["documents", "editor-index"])
def test_text_lists_split_provenance_and_align_every_filter_with_sortable_column(rows, view):
    client, documents, _ = rows
    response = client.get(reverse(f"content:{view}"))
    assert response.status_code == 200
    soup = BeautifulSoup(response.content, "html.parser")
    assert [header.get_text(strip=True) for header in soup.select("thead th")] == [
        "Titel", "Domäne", "Ordner", "Dateiname", "Arbeitsstand", "Freigabe",
    ]
    assert len(soup.select("thead th a")) == 6
    assert len(soup.select("thead tr.table-filters td")) == 6
    assert [field["name"] for field in soup.select("thead input, thead select")] == [
        "q", "domain_q", "folder", "filename", "revision", "approved",
    ]
    folders = {row.title: row.source_folder for row in response.context["documents"]}
    assert folders == {"Zulu": "md/old", "alpha": "md/current/deep", "Beta": ""}
    assert soup.select_one(f'a[href="{reverse("content:editor", args=[documents[0].pk])}"]')


@pytest.mark.parametrize("view", ["documents", "editor-index"])
@pytest.mark.parametrize("filters,expected", [
    ({"q": "ALP"}, ["alpha"]),
    ({"domain_q": "other"}, ["Beta"]),
    ({"folder": "current/deep"}, ["alpha"]),
    ({"filename": "Z.MD"}, ["Zulu"]),
    ({"revision": "2"}, ["Zulu"]),
    ({"approved": "yes"}, ["Zulu"]),
    ({"approved": "no", "domain_q": "Books"}, ["alpha"]),
    ({"q": "alpha", "filename": "z.md"}, []),
])
def test_text_lists_apply_each_column_filter_and_combinations(rows, view, filters, expected):
    client, _, _ = rows
    response = client.get(reverse(f"content:{view}"), filters)
    assert [row.title for row in response.context["documents"]] == expected


@pytest.mark.parametrize("view", ["documents", "editor-index"])
@pytest.mark.parametrize("sort,expected", [
    ("q", ["alpha", "Beta", "Zulu"]),
    ("-q", ["Zulu", "Beta", "alpha"]),
    ("domain_q", ["Zulu", "alpha", "Beta"]),
    ("-domain_q", ["Beta", "Zulu", "alpha"]),
    ("folder", ["Beta", "alpha", "Zulu"]),
    ("-folder", ["Zulu", "alpha", "Beta"]),
    ("filename", ["alpha", "Beta", "Zulu"]),
    ("-filename", ["Zulu", "Beta", "alpha"]),
    ("revision", ["alpha", "Beta", "Zulu"]),
    ("-revision", ["Zulu", "alpha", "Beta"]),
    ("approved", ["Zulu", "alpha", "Beta"]),
    ("-approved", ["Zulu", "alpha", "Beta"]),
])
def test_text_lists_sort_all_columns_in_both_directions(rows, view, sort, expected):
    client, _, _ = rows
    response = client.get(reverse(f"content:{view}"), {"sort": sort})
    # Equal values have an ID tie-break, not a title/creation-order guarantee.
    actual = [row.title for row in response.context["documents"]]
    if sort.lstrip("-") in {"domain_q", "revision", "approved"}:
        if sort == "domain_q":
            assert set(actual[:2]) == {"Zulu", "alpha"} and actual[2] == "Beta"
        elif sort == "-domain_q":
            assert actual[0] == "Beta" and set(actual[1:]) == {"Zulu", "alpha"}
        elif sort == "revision":
            assert set(actual[:2]) == {"alpha", "Beta"} and actual[2] == "Zulu"
        else:
            assert actual[0] == "Zulu" and set(actual[1:]) == {"alpha", "Beta"}
    else:
        assert actual == expected


@pytest.mark.parametrize("view", ["documents", "editor-index"])
def test_text_lists_sort_links_preserve_filters_and_drop_page(rows, view):
    client, _, _ = rows
    response = client.get(reverse(f"content:{view}"), {
        "sort": "filename", "folder": "md", "domain_q": "Books", "page": "1",
    })
    soup = BeautifulSoup(response.content, "html.parser")
    header = soup.select("thead th")[3]
    assert header["aria-sort"] == "ascending"
    query = parse_qs(urlsplit(header.a["href"]).query)
    assert query == {"sort": ["-filename"], "folder": ["md"], "domain_q": ["Books"]}
    assert soup.select_one('input[type="hidden"][name="sort"]')["value"] == "filename"


@pytest.mark.parametrize("view", ["documents", "editor-index"])
def test_text_lists_bad_revision_filter_displays_error_without_query_crash(rows, view):
    client, _, _ = rows
    response = client.get(reverse(f"content:{view}"), {"revision": "not-a-number"})
    assert response.status_code == 200
    assert BeautifulSoup(response.content, "html.parser").select_one('[role="alert"]')
    assert list(response.context["documents"]) == []


def test_text_list_uses_latest_registered_location_without_duplicate_rows(rows):
    client, documents, user = rows
    SourceRegistration.objects.create(
        source=documents[0].run.source, relative_path="Books/md/moved/z.md", registered_by=user,
    )
    response = client.get(reverse("content:documents"), {"folder": "moved"})
    assert [(row.pk, row.source_folder) for row in response.context["documents"]] == [
        (documents[0].pk, "md/moved"),
    ]


@pytest.mark.parametrize("view", ["documents", "editor-index"])
def test_text_list_column_filter_cannot_escape_active_domain(rows, view, settings):
    client, _, user = rows
    domain = settings.WISSENSWIKI["DOMAINS"][0]["name"]
    ActiveDomain.objects.create(user=user, name=domain)
    response = client.get(reverse(f"content:{view}"), {"domain_q": "Other"})
    assert list(response.context["documents"]) == []
    assert ActiveDomain.objects.get(user=user).name == domain


@pytest.mark.parametrize("view", ["documents", "editor-index"])
def test_text_lists_filter_and_sort_before_pagination(rows, view, monkeypatch):
    from knext.content.views import DocumentListView

    client, _, _ = rows
    monkeypatch.setattr(DocumentListView, "paginate_by", 1)
    response = client.get(reverse(f"content:{view}"), {"folder": "md", "sort": "filename", "page": "2"})
    assert [row.title for row in response.context["documents"]] == ["Zulu"]
    assert response.context["paginator"].count == 2
    assert response.context["pagination_query"] == "folder=md&sort=filename"


def test_relationship_types_use_compact_rows_and_keep_creation_form(rows):
    client, _, _ = rows
    soup = BeautifulSoup(client.get(reverse("content:relation-types")).content, "html.parser")
    assert soup.select_one("table.compact-table.relation-types-table tbody tr")
    assert [header.get_text(strip=True) for header in soup.select("thead th")] == [
        "Bezeichnung", "Schlüssel", "Definition", "Verwendung",
    ]
    assert soup.select_one('form[method="post"] input[name="csrfmiddlewaretoken"]')
    assert len(soup.select("section.panel")) == 2
