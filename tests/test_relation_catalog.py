"""The same operator vocabulary governs Wiki and DB writes without rewriting history."""

import json

import pytest
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.test import Client
from django.urls import reverse

from knext.content.graph_services import collection_data, save_collection
from knext.content.models import ContentResource, RelationType, ResourceRelation
from knext.content.relation_catalog import relation_catalog, resolve_relation_type

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog_environment(settings, tmp_path):
    for name in ("workspace", "docs", "relations"):
        (tmp_path / name).mkdir()
    settings.WISSENSWIKI = {
        "WORKSPACE": str(tmp_path / "workspace"),
        "DOMAINS": [{"name": "Test", "source": str(tmp_path / "docs"),
                    "relations": str(tmp_path / "relations")}],
        "RELATION_CATALOG": {"preset": "documentation", "types": []},
    }
    user = User.objects.create_user("catalog-reader")
    client = Client()
    client.force_login(user)
    return settings, client, user


def select_preset(settings, preset, types=None):
    settings.WISSENSWIKI = {
        **settings.WISSENSWIKI,
        "RELATION_CATALOG": {"preset": preset, "types": types or []},
    }


def test_catalog_read_and_widget_do_not_materialize_db_types(catalog_environment):
    _, client, _ = catalog_environment
    before = RelationType.objects.count()
    response = client.get(reverse("wissenswiki:api"))
    assert response.status_code == 200
    keys = {item["key"] for item in response.json()["relation_types"] if item["enabled"]}
    assert {"reference", "references", "parent", "child", "depends-on"} <= keys
    assert not response.json()["blocks"]
    page = client.get(reverse("wissenswiki:graph-header"))
    assert page.status_code == 200
    for key in keys:
        assert f'value="{key}"' in page.content.decode()
    assert RelationType.objects.count() == before


def test_custom_operator_type_is_available_in_both_apis(catalog_environment):
    settings, client, _ = catalog_environment
    select_preset(settings, "basic", [{
        "key": "illuminates", "label": "Beleuchtet",
        "description": "Der Ausgang beleuchtet einen Aspekt des Ziels.", "color": "#123456",
    }])
    resource = ContentResource.objects.create(kind="folder", title="Start", domain="Test")
    target = ContentResource.objects.create(kind="folder", title="Ziel", domain="Test")
    response = client.post(reverse("content:resource", args=[resource.pk]), {
        "target_id": str(target.pk), "relation_type": "illuminates", "reason": "Kontext",
    })
    assert response.status_code == 302
    assert ResourceRelation.objects.get().relation_type_id == "illuminates"
    assert RelationType.objects.get(pk="illuminates").catalog_managed
    api = client.get(reverse("wissenswiki:api")).json()
    assert next(item for item in api["relation_types"] if item["key"] == "illuminates")["enabled"]
    first = client.post(reverse("wissenswiki:api"), data=json.dumps({
        "action": "create", "title": "Start", "text": "Starttext",
    }), content_type="application/json").json()
    second = client.post(reverse("wissenswiki:api"), data=json.dumps({
        "action": "create", "title": "Ziel", "text": "Zieltext",
    }), content_type="application/json").json()
    response = client.post(reverse("wissenswiki:api"), data=json.dumps({
        "action": "relate", "id": first["id"], "revision": first["revision"],
        "target": second["id"], "type": "illuminates",
    }), content_type="application/json")
    assert response.status_code == 200
    assert response.json()["relations"][0]["type"] == "illuminates"


def test_preset_switch_keeps_old_relations_but_disallows_new_ones(catalog_environment):
    settings, client, user = catalog_environment
    source = ContentResource.objects.create(kind="folder", title="Start", domain="Test")
    target = ContentResource.objects.create(kind="folder", title="Ziel", domain="Test")
    relation = ResourceRelation.objects.create(
        source=source, target=target, relation_type=resolve_relation_type("extends"), created_by=user,
    )
    select_preset(settings, "basic")
    assert ResourceRelation.objects.get(pk=relation.pk).relation_type_id == "extends"
    assert "extends" not in {item.key for item in relation_catalog() if item.enabled}
    response = client.post(reverse("content:resource", args=[source.pk]), {
        "target_id": str(target.pk), "relation_type": "extends",
    })
    assert response.status_code == 400
    assert client.get(reverse("content:resource", args=[source.pk])).status_code == 200
    assert RelationType.objects.filter(pk="extends").exists()


def test_disabled_collection_links_can_be_retained_not_newly_added(catalog_environment):
    settings, _, user = catalog_environment
    resource = ContentResource.objects.create(kind="folder", title="Topic", domain="Test")
    args = dict(title="Set", domain="Test", kind="set", description="", user=user)
    data = {
        "entries": [{"key": "a", "resource": str(resource.pk)}, {"key": "b", "resource": str(resource.pk)}],
        "links": [{"source": "a", "target": "b", "type": "extends"}],
    }
    collection = save_collection(collection=None, expected=0, data=data, **args)
    select_preset(settings, "basic")
    saved = save_collection(collection=collection, expected=1, data=collection_data(collection), **args)
    assert saved.links.get().relation_type_id == "extends"
    data["links"].append({"source": "b", "target": "a", "type": "extends"})
    with pytest.raises(ValidationError, match="nicht.*freigegeben"):
        save_collection(collection=saved, expected=2, data=data, **args)
    assert saved.links.count() == 1


def test_independent_db_custom_types_remain_available_and_definition_conflicts_fail(catalog_environment):
    settings, _, _ = catalog_environment
    RelationType.objects.create(key="explores", label="Erkundet", description="Erkundet das Ziel.")
    assert "explores" in {item.key for item in relation_catalog() if item.enabled}
    select_preset(settings, "basic", [{
        "key": "explores", "label": "Andere Bedeutung", "description": "Ersetzt das Ziel.",
    }])
    with pytest.raises(ValidationError, match="neuen Schlüssel"):
        relation_catalog()


def test_explicit_disabled_definition_rejected_by_resource_form(catalog_environment):
    settings, client, _ = catalog_environment
    definition = next(item for item in relation_catalog() if item.key == "reference")
    select_preset(settings, "basic", [{
        "key": definition.key, "label": definition.label, "description": definition.description,
        "enabled": False,
    }])
    source = ContentResource.objects.create(kind="folder", title="Start", domain="Test")
    target = ContentResource.objects.create(kind="folder", title="Ziel", domain="Test")
    response = client.post(reverse("content:resource", args=[source.pk]), {
        "target_id": str(target.pk), "relation_type": "reference",
    })
    assert response.status_code == 400
    assert not ResourceRelation.objects.exists()
    assert not next(item for item in client.get(reverse("wissenswiki:api")).json()["relation_types"]
                    if item["key"] == "reference")["enabled"]
