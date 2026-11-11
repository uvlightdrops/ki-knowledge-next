"""Graph identity, revision-bound outlines and independent composition workflows."""

import io
import json
import uuid

import pytest
from bs4 import BeautifulSoup
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import Client
from django.urls import reverse

from knext.content.graph_services import _validate_shape, collection_data, collection_rows, index_revision, save_collection
from knext.content.importers.base import ImportFailure
from knext.content.models import (
    ContentCollection, ContentResource, ContentRevision, ImportRun, ResourceRelation,
)
from knext.content.outline import parse_outline
from knext.content.services import RevisionConflict, approve, import_upload, restore, revise

pytestmark = pytest.mark.django_db
BODY = (
    "# Book\n\nIntroduction.\n\n## Chapter [chapter]\n\nChapter text.\n\n"
    "### Aspect [aspect]\n\nAspect text.\n\n##### Deep [deep]\n\nDeep text.\n\n"
    "## End [end]\n\nEnd text.\n"
)


@pytest.fixture(autouse=True)
def registry_paths(settings, tmp_path):
    for folder in ("workspace", "data", "relations", "docs"):
        (tmp_path / folder).mkdir()
    settings.WISSENSWIKI = {
        "WORKSPACE": str(tmp_path / "workspace"),
        "DOMAINS": [{
            "name": "Books", "source": str(tmp_path / "docs"), "relations": str(tmp_path / "relations"),
        }],
        "MARKDOWN_DATA": {"root": str(tmp_path / "data"), "relations": str(tmp_path / "data-relations")},
    }


@pytest.fixture
def writer():
    return User.objects.create_user("graph-writer")


@pytest.fixture
def client(writer):
    browser = Client()
    browser.force_login(writer)
    return browser


@pytest.fixture
def document(writer):
    run, _ = import_upload(SimpleUploadedFile("book.md", BODY.encode()), "Books", writer)
    assert run.status == ImportRun.Status.SUCCEEDED, run.error
    return run.documents.get()


@pytest.fixture
def folder():
    return ContentResource.objects.create(kind="folder", title="Topics", domain="Books")


def save(writer, folder, *, collection=None, expected=0, kind="hierarchy", data=None):
    return save_collection(
        collection=collection, expected=expected, title="Reading path", domain="Books",
        kind=kind, description="A perspective, not a publication.", user=writer,
        data=data if data is not None else {
            "entries": [{"key": "root", "resource": str(folder.pk), "position": 0}], "links": [],
        },
    )


def test_outline_preserves_all_levels_direct_text_and_skipped_parent():
    intro, blocks = parse_outline(BODY)
    assert intro == "# Book\n\nIntroduction.\n\n"
    assert [block.level for block in blocks] == [2, 3, 5, 2]
    assert [block.parent for block in blocks] == [None, 0, 1, None]
    assert [block.explicit_id for block in blocks] == ["chapter", "aspect", "deep", "end"]
    assert "Aspect text" not in blocks[0].body
    lines = BODY.splitlines(keepends=True)
    assert all(block.body == "".join(lines[block.start_line - 1:block.end_line]) for block in blocks)
    assert intro + "".join(block.body for block in blocks) == BODY


@pytest.mark.parametrize("snippet", [
    "```markdown\n## Fake [fake]\n```\n",
    "~~~~\n## Fake [fake]\n~~~~\n",
    "    ## Fake [fake]\n",
    "> ## Fake [fake]\n",
    "<!--\n## Fake [fake]\n-->\n",
    "<pre>\n## Fake [fake]\n</pre>\n",
    "<div>\n## Fake [fake]\n</div>\n",
    "- item\n  ### Fake [fake]\n",
    "```\nFake\n```\n---\n",
    "```\n- Example item\n  ```\n",
])
def test_outline_ignores_non_document_headings(snippet):
    _, blocks = parse_outline("# Title\n\n" + snippet + "\n## Real [real]\n\nText.")
    assert [item.explicit_id for item in blocks] == ["real"]


def test_setext_crlf_and_later_h1_are_lossless():
    text = "Book\r\n====\r\n\r\nIntro\r\n\r\nChapter [chapter]\r\n---\r\nText\r\n\r\n# Other\r\nMore\r\n"
    intro, blocks = parse_outline(text)
    assert intro == "Book\r\n====\r\n\r\nIntro\r\n\r\n"
    assert [block.level for block in blocks] == [2, 1]
    assert intro + "".join(block.body for block in blocks) == text


def test_outline_section_limit_is_exact():
    text = "".join(f"## Section {index}\nText.\n\n" for index in range(5000))
    assert len(parse_outline(text)[1]) == 5000
    with pytest.raises(ImportFailure, match="5000"):
        parse_outline(text + "## One more\nText.")


def test_composition_shape_limits_are_exact():
    entries = [{"key": f"n-{index}", "resource": "unused"} for index in range(5000)]
    links = [{} for _ in range(10000)]
    assert _validate_shape({"entries": entries, "links": links}, "set") == (entries, links)
    with pytest.raises(ValidationError, match="5000"):
        _validate_shape({"entries": entries + [{"key": "extra"}], "links": links}, "set")
    with pytest.raises(ValidationError, match="10000"):
        _validate_shape({"entries": entries, "links": links + [{}]}, "set")


def test_document_without_sections_has_empty_outline(writer):
    run, _ = import_upload(SimpleUploadedFile("plain.md", b"# Title\n\nBody"), "Books", writer)
    revision = run.documents.get().revisions.get()
    assert not revision.outline.entries.exists()
    assert revision.document.resources.filter(kind="document").count() == 1


def test_duplicate_explicit_ids_fail_without_partial_graph(writer):
    run, _ = import_upload(SimpleUploadedFile("bad.md", b"## One [same]\n\n### Two [same]\n"), "Books", writer)
    assert run.status == "failed" and "Doppelte Block-ID" in run.error
    assert not run.documents.exists()
    assert not ContentResource.objects.exists()


def test_revision_outlines_are_pinned_idempotent_and_keep_approval(document, writer):
    first = document.revisions.get()
    snapshot = first.blocks.get(explicit_id="chapter")
    outline = first.outline
    assert outline.kind == "hierarchy" and outline.source_revision == first
    assert outline.entries.count() == 4
    assert all(item.revision_id == first.pk for item in outline.entries.all())
    assert index_revision(first).pk == outline.pk
    publisher = User.objects.create_superuser("graph-publisher")
    approve(document, expected=1, user=publisher)
    edited = revise(document, expected=1, title="Edited book", body=BODY.replace("Chapter [chapter]", "Renamed [chapter]"), user=writer)
    renamed = edited.blocks.get(explicit_id="chapter")
    assert renamed.resource_id == snapshot.resource_id and renamed.title == "Renamed"
    assert collection_rows(outline)[0]["title"] == "Chapter"
    assert collection_rows(edited.outline)[0]["title"] == "Renamed"
    assert snapshot.resource.snapshots.count() == 2
    restored = restore(document, expected=2, number=1, user=writer)
    assert restored.blocks.get(explicit_id="chapter").resource_id == snapshot.resource_id
    document.refresh_from_db()
    assert document.approved_revision == first and first.body == BODY
    assert outline.entries.count() == 4
    with pytest.raises(ValidationError):
        snapshot.save()
    with pytest.raises(RevisionConflict):
        save(writer, snapshot.resource, collection=outline, expected=1)


def test_anonymous_identity_is_reused_only_when_unambiguous(writer):
    run, _ = import_upload(SimpleUploadedFile("anonymous.md", b"## Topic\nText\n\n## Repeated\nA\n\n## Repeated\nB\n"), "Books", writer)
    document = run.documents.get()
    first = document.revisions.get()
    second = revise(document, expected=1, title="Anonymous", body=first.body.replace("Text", "Changed"), user=writer)
    assert first.blocks.get(title="Topic").resource_id == second.blocks.get(title="Topic").resource_id
    before = set(first.blocks.filter(title="Repeated").values_list("resource_id", flat=True))
    after = set(second.blocks.filter(title="Repeated").values_list("resource_id", flat=True))
    assert before.isdisjoint(after)
    assert len(before) == len(after) == 2


def test_explicit_block_ids_are_scoped_to_documents(document, writer):
    run, _ = import_upload(SimpleUploadedFile("other.md", b"## Chapter [chapter]\n\nOther."), "Books", writer)
    assert document.revisions.get().blocks.get(explicit_id="chapter").resource_id != (
        run.documents.get().revisions.get().blocks.get().resource_id
    )


def test_explicit_identity_survives_reordering_and_heading_level_changes(document, writer):
    first = document.revisions.get()
    before = dict(first.blocks.values_list("explicit_id", "resource_id"))
    edited = revise(document, expected=1, title="Reordered", body=(
        "# Book\n\n## End [end]\nEnd\n\n## Chapter [chapter]\nChapter\n\n"
        "#### Deep [deep]\nDeep\n\n### Aspect [aspect]\nAspect"
    ), user=writer)
    assert dict(edited.blocks.values_list("explicit_id", "resource_id")) == before
    assert [item.explicit_id for item in edited.blocks.all()] == ["end", "chapter", "deep", "aspect"]
    assert edited.blocks.get(explicit_id="deep").level == 4


def test_removed_block_stays_addressable_but_cannot_pin_absent_revision(document, writer, folder):
    first = document.revisions.get()
    block = first.blocks.get(explicit_id="aspect").resource
    second = revise(document, expected=1, title="Reduced", body="## Only [only]\nText", user=writer)
    assert ContentResource.objects.filter(pk=block.pk).exists()
    assert block.snapshots.count() == 1 and not second.blocks.filter(resource=block).exists()
    with pytest.raises(ValidationError, match="nicht vorhanden"):
        save(writer, folder, data={
            "entries": [{"key": "old", "resource": str(block.pk), "revision": second.pk}], "links": [],
        })


@pytest.mark.parametrize("kind", ["hierarchy", "sequence", "set", "network"])
def test_all_composition_kinds_persist_repeated_resources_and_cycles(writer, folder, kind):
    data = {
        "entries": [
            {"key": "one", "resource": str(folder.pk), "position": 0},
            {"key": "two", "resource": str(folder.pk), "position": 1,
             "parent": "one" if kind == "hierarchy" else None},
        ],
        "links": [
            {"source": "one", "target": "two", "type": "reference", "reason": "Forward"},
            {"source": "two", "target": "one", "type": "reference", "reason": "Return"},
        ],
    }
    collection = save(writer, folder, kind=kind, data=data)
    assert collection.entries.count() == 2 and collection.links.count() == 2
    assert [row["depth"] for row in collection_rows(collection)] == [0, 1 if kind == "hierarchy" else 0]
    exported = collection_data(collection)
    assert {item["key"] for item in exported["entries"]} == {"one", "two"}
    assert len(exported["links"]) == 2


def test_reparent_reorder_and_remove_are_atomic_and_preserve_entry_ids(writer, folder):
    collection = save(writer, folder)
    original_id = collection.entries.get().pk
    edited = save(writer, folder, collection=collection, expected=1, data={
        "entries": [
            {"key": "child", "resource": str(folder.pk), "position": 0},
            {"key": "root", "resource": str(folder.pk), "parent": "child", "position": 0},
        ], "links": [{"source": "root", "target": "child", "type": "reference"}],
    })
    assert edited.version == 2 and edited.entries.get(key="root").pk == original_id
    assert edited.entries.get(key="root").parent.key == "child"
    save(writer, folder, collection=edited, expected=2)
    assert edited.entries.get().pk == original_id
    assert not edited.links.exists()
    with pytest.raises(RevisionConflict):
        save(writer, folder, collection=edited, expected=2, data={"entries": [], "links": []})
    edited.refresh_from_db()
    assert edited.version == 3 and edited.entries.count() == 1


@pytest.mark.parametrize("data", [
    [],
    {},
    {"entries": {}, "links": []},
    {"entries": [None], "links": []},
    {"entries": [{"key": "a", "resource": "not-uuid"}], "links": []},
    {"entries": [{"key": "a", "resource": str(uuid.UUID(int=0))}], "links": []},
    {"entries": [{"key": "a", "resource": "FOLDER", "parent": "a"}], "links": []},
    {"entries": [{"key": "a", "resource": "FOLDER", "parent": "missing"}], "links": []},
    {"entries": [{"key": "a", "resource": "FOLDER", "position": -1}], "links": []},
    {"entries": [{"key": "a", "resource": "FOLDER", "position": True}], "links": []},
    {"entries": [{"key": "a", "resource": "FOLDER", "revision": []}], "links": []},
    {"entries": [{"key": "a", "resource": "FOLDER", "bogus": 1}], "links": []},
    {"entries": [{"key": "a", "resource": "FOLDER"}, {"key": "a", "resource": "FOLDER"}], "links": []},
    {"entries": [{"key": "a", "resource": "FOLDER"}, {"key": "b", "resource": "FOLDER"}], "links": []},
    {"entries": [{"key": "a", "resource": "FOLDER", "parent": "b"},
                 {"key": "b", "resource": "FOLDER", "parent": "a"}], "links": []},
    {"entries": [], "links": [None]},
    {"entries": [], "links": [{"source": [], "target": {}, "type": "reference"}]},
    {"entries": [], "links": [{"source": "a", "target": "b", "type": "reference"}]},
    {"entries": [{"key": "root", "resource": "FOLDER"}],
     "links": [{"source": "root", "target": "root", "type": "unknown"}]},
])
def test_invalid_composition_rolls_back_everything(writer, folder, data):
    collection = save(writer, folder)
    before = collection_data(collection)
    expanded = json.loads(json.dumps(data).replace("FOLDER", str(folder.pk)))
    with pytest.raises(ValidationError):
        save(writer, folder, collection=collection, expected=1, data=expanded)
    collection.refresh_from_db()
    assert collection.version == 1 and collection_data(collection) == before


def test_cross_document_revision_is_rejected(document, writer, folder):
    revision = document.revisions.get()
    with pytest.raises(ValidationError, match="nicht zur ausgewählten Ressource"):
        save(writer, folder, data={
            "entries": [{"key": "folder", "resource": str(folder.pk), "revision": revision.pk}], "links": [],
        })


@pytest.mark.parametrize("kind", ["sequence", "set", "network"])
def test_nonhierarchical_compositions_reject_parent_links(writer, folder, kind):
    with pytest.raises(ValidationError, match="Nur Hierarchien"):
        save(writer, folder, kind=kind, data={
            "entries": [{"key": "a", "resource": str(folder.pk), "parent": "a"}], "links": [],
        })


def test_nested_collection_references_are_not_recursively_expanded(writer, folder):
    collection = save(writer, folder)
    save(writer, folder, collection=collection, expected=1, data={
        "entries": [{"key": "self", "resource": str(collection.pk)}], "links": [],
    })
    assert len(collection_rows(collection)) == 1


def test_large_depth_uses_iterative_traversal(writer, folder):
    data = {
        "entries": [
            {"key": f"n-{index}", "resource": str(folder.pk), "parent": f"n-{index - 1}" if index else None}
            for index in range(1050)
        ],
        "links": [],
    }
    collection = save(writer, folder, data=data)
    rows = collection_rows(collection)
    assert len(rows) == 1050 and rows[-1]["depth"] == 1049


def test_backfill_is_idempotent_without_rewriting_history(document, writer):
    first = document.revisions.get()
    # Legacy code may create a revision without going through the new indexing service.
    second = ContentRevision.objects.create(
        document=document, number=2, title="Legacy revision", body=BODY, parent=first, created_by=writer,
    )
    before = (second.content_sha256, second.body, document.approved_revision_id)
    stream = io.StringIO()
    call_command("index_content", stdout=stream)
    assert "1 Revisionen" in stream.getvalue()
    second.refresh_from_db()
    assert second.outline.entries.count() == 4
    assert (second.content_sha256, second.body, document.approved_revision_id) == before
    again = io.StringIO()
    call_command("index_content", stdout=again)
    assert "0 Revisionen" in again.getvalue()


def test_http_collection_roundtrip_conflict_and_readonly_outline(client, document, folder):
    response = client.post(reverse("content:collection-create"), {
        "title": "My path", "domain": "Books", "kind": "hierarchy", "expected": 0, "data": json.dumps({
            "entries": [{"key": "one", "resource": str(folder.pk), "position": 0}], "links": [],
        }),
    })
    assert response.status_code == 302
    collection = ContentCollection.objects.get(resource__title="My path")
    detail = client.get(response.url)
    assert detail.status_code == 200 and b"Topics" in detail.content
    exported = client.get(response.url, {"format": "json"}).json()
    assert exported["structure"]["entries"][0]["resource"] == str(folder.pk)
    form = BeautifulSoup(client.get(reverse("content:collection-edit", args=[collection.pk])).content, "html.parser")
    assert json.loads(form.select_one("textarea[name=data]").text)["entries"][0]["key"] == "one"
    assert client.post(reverse("content:collection-edit", args=[collection.pk]), {
        "title": "Overwrite", "domain": "Books", "kind": "set", "expected": 0,
        "data": json.dumps({"entries": [], "links": []}),
    }).status_code == 409
    assert client.get(reverse("content:collection-edit", args=[document.revisions.get().outline.pk])).status_code == 409
    assert client.post(reverse("content:collection-create"), {
        "title": "Bad", "domain": "Books", "kind": "set", "expected": 0, "data": '{"entries": [], "links": [null]}',
    }).status_code == 400
    assert not ContentResource.objects.filter(title="Bad").exists()


def test_global_relation_types_and_relations_are_extensible_and_cross_domain(client, folder):
    target = ContentResource.objects.create(kind="folder", title="Other", domain="Another")
    assert client.post(reverse("content:relation-types"), {
        "key": "questions", "label": "Hinterfragt", "description": "Stellt eine konkrete Aussage zur Diskussion.",
    }).status_code == 302
    assert client.post(reverse("content:relation-types"), {
        "key": "empty", "label": "Empty", "description": "",
    }).status_code == 400
    url = reverse("content:resource", args=[folder.pk])
    assert client.post(url, {
        "target_id": str(target.pk), "relation_type": "questions", "reason": "Andere Sichtweise",
    }).status_code == 302
    relation = ResourceRelation.objects.get()
    assert relation.target == target and relation.source == folder
    assert client.post(url, {
        "target_id": str(target.pk), "relation_type": "questions",
    }).status_code == 400
    assert ResourceRelation.objects.count() == 1
    assert client.get(reverse("content:resource", args=[target.pk])).status_code == 200
    assert client.get(reverse("content:relation-delete", args=[relation.pk])).status_code == 405
    assert client.post(reverse("content:relation-delete", args=[relation.pk])).status_code == 302
    assert not ResourceRelation.objects.exists()


def test_folder_creation_and_all_catalog_surfaces(client, document):
    result = client.post(reverse("content:folder-create"), {"title": "A folder", "domain": "Books"})
    assert result.status_code == 302
    assert ContentResource.objects.get(title="A folder").kind == "folder"
    assert client.get(result.url).status_code == 200
    for view in ("content:resources", "content:collections", "content:relation-types", "content:collection-create"):
        assert client.get(reverse(view)).status_code == 200
    for resource in ContentResource.objects.all():
        assert client.get(reverse("content:resource", args=[resource.pk])).status_code == 200
    for view in ("content:document", "content:extraction-blocks"):
        page = client.get(reverse(view, args=[document.pk]))
        assert page.status_code == 200
    outline_url = reverse("content:collection", args=[document.revisions.get().outline.pk])
    assert outline_url in client.get(reverse("content:document", args=[document.pk])).content.decode()
    assert client.get(outline_url).status_code == 200


def test_catalogs_filter_and_preserve_explicit_domain(client, folder, writer):
    other = ContentResource.objects.create(kind="folder", title="Outside domain", domain="Other")
    save(writer, folder)
    save_collection(
        collection=None, expected=0, title="Other composition", domain="Other", kind="set",
        description="", data={"entries": [], "links": []}, user=writer,
    )
    for view in ("content:resources", "content:collections"):
        response = client.get(reverse(view), {"domain": "Books"})
        assert response.status_code == 200
        soup = BeautifulSoup(response.content, "html.parser")
        assert soup.select_one('input[type=hidden][name=domain]')["value"] == "Books"
        assert "Outside domain" not in soup.get_text() and "Other composition" not in soup.get_text()
    assert client.get(reverse("content:resource", args=[other.pk])).status_code == 200


def test_unauthenticated_and_csrf_requests_cannot_mutate_graph(client, writer, folder):
    assert Client().get(reverse("content:resources")).status_code == 302
    assert Client().get(reverse("content:collections")).status_code == 302
    assert Client().post(reverse("content:folder-create"), {"title": "Denied", "domain": "Books"}).status_code == 302
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(writer)
    assert csrf.post(reverse("content:folder-create"), {"title": "Denied", "domain": "Books"}).status_code == 403
    assert not ContentResource.objects.filter(title="Denied").exists()
