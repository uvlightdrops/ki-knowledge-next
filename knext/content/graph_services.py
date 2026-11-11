"""Atomic indexing and conflict-aware composition updates."""

import uuid
from collections import Counter

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import F
from django.utils import timezone

from .models import (
    BlockSnapshot, CollectionEntry, CollectionLink, ContentCollection, ContentDocument,
    ContentResource, ContentRevision, RelationType,
)
from .outline import parse_outline
from .relation_catalog import resolve_relation_type
from .services import RevisionConflict


@transaction.atomic
def index_revision(revision: ContentRevision) -> ContentCollection:
    """Idempotently derive a revision-bound outline without rewriting source content."""
    document = ContentDocument.objects.select_for_update().get(pk=revision.document_id)
    existing = ContentCollection.objects.filter(source_revision=revision).first()
    if existing:
        return existing
    _, blocks = parse_outline(revision.body)
    domain = document.run.source.domain
    resource, _ = ContentResource.objects.get_or_create(
        document=document, local_key="",
        defaults={"kind": "document", "domain": domain, "title": document.title},
    )
    if document.revision_number == revision.number:
        ContentResource.objects.filter(pk=resource.pk).update(title=revision.title)
    collection = ContentCollection.objects.create(
        resource=ContentResource.objects.create(
            kind="collection", domain=domain, title=f"{revision.title[:220]} · Revision {revision.number}",
        ),
        kind="hierarchy", source_revision=revision, created_by=revision.created_by,
        description="Aus dem Markdown dieser Revision abgeleitete Quellgliederung.",
    )
    previous_id = revision.restored_from_id or revision.parent_id
    previous = list(BlockSnapshot.objects.filter(revision_id=previous_id).select_related("resource"))
    prior_counts = Counter(item.title for item in previous if not item.explicit_id)
    counts = Counter(item.title for item in blocks if not item.explicit_id)
    reusable = {
        item.title: item.resource for item in previous
        if not item.explicit_id and prior_counts[item.title] == counts[item.title] == 1
    }
    entries = []
    for position, block in enumerate(blocks):
        block_resource = _block_resource(document, domain, block, reusable)
        if document.revision_number == revision.number:
            ContentResource.objects.filter(pk=block_resource.pk).update(title=block.title)
        BlockSnapshot.objects.create(
            resource=block_resource, revision=revision, title=block.title,
            explicit_id=block.explicit_id, level=block.level, start_line=block.start_line,
            end_line=block.end_line, body=block.body,
        )
        entries.append(CollectionEntry.objects.create(
            collection=collection, key=f"b-{block_resource.pk.hex}", resource=block_resource,
            revision=revision, parent=entries[block.parent] if block.parent is not None else None,
            position=position,
        ))
    return collection


def _block_resource(document, domain: str, block, reusable: dict) -> ContentResource:
    if block.explicit_id:
        resource, _ = ContentResource.objects.get_or_create(
            document=document, local_key="id:" + block.explicit_id,
            defaults={"kind": "block", "domain": domain, "title": block.title},
        )
        return resource
    if block.title in reusable:
        return reusable[block.title]
    return ContentResource.objects.create(
        document=document, kind="block", domain=domain, title=block.title, local_key="auto:" + str(uuid.uuid4()),
    )


def collection_data(collection: ContentCollection) -> dict:
    return {
        "entries": [{
            "key": item.key, "resource": str(item.resource_id),
            "parent": item.parent.key if item.parent_id else None,
            "position": item.position, "revision": item.revision_id,
        } for item in collection.entries.select_related("parent")],
        "links": [{
            "source": link.source.key, "target": link.target.key,
            "type": link.relation_type_id, "reason": link.reason,
        } for link in collection.links.select_related("source", "target").order_by("pk")],
    }


def _validate_shape(data: dict, kind: str) -> tuple[list[dict], list[dict]]:
    if not isinstance(data, dict) or set(data) != {"entries", "links"}:
        raise ValidationError("Struktur muss genau entries und links enthalten.")
    entries, links = data["entries"], data["links"]
    if not isinstance(entries, list) or not isinstance(links, list) or len(entries) > 5000 or len(links) > 10000:
        raise ValidationError("Maximal 5000 Einträge und 10000 Kanten als Listen angeben.")
    keys, positions = {}, set()
    for item in entries:
        if not isinstance(item, dict) or set(item) - {"key", "resource", "parent", "position", "revision"}:
            raise ValidationError("Eintrag enthält unbekannte Felder oder ist kein Objekt.")
        key, parent, position = item.get("key"), item.get("parent"), item.get("position", 0)
        if not isinstance(key, str) or not isinstance(parent, (str, type(None))):
            raise ValidationError("Einträge brauchen Textschlüssel und parent als Schlüssel oder null.")
        if key in keys:
            raise ValidationError(f"Doppelter Eintragsschlüssel: {key}")
        if type(position) is not int or position < 0:
            raise ValidationError("position muss eine nichtnegative ganze Zahl sein.")
        if parent is not None and kind != ContentCollection.Kind.HIERARCHY:
            raise ValidationError("Nur Hierarchien dürfen Elterneinträge enthalten.")
        if kind in {"sequence", "hierarchy"} and (parent, position) in positions:
            raise ValidationError("Geschwister brauchen unterschiedliche Positionen.")
        positions.add((parent, position))
        keys[key] = parent
    _validate_parents(keys)
    return entries, links


def _validate_parents(parents: dict[str, str | None]) -> None:
    visited = set()
    for key in parents:
        path, current = set(), key
        while current is not None and current not in visited:
            if current not in parents:
                raise ValidationError(f"Unbekannter Elterneintrag: {current}")
            if current in path:
                raise ValidationError("Elterneinträge dürfen keinen Zyklus bilden.")
            path.add(current)
            current = parents[current]
        visited.update(path)


def _entry_values(item: dict) -> dict:
    try:
        resource_id = uuid.UUID(str(item.get("resource", "")))
    except (ValueError, AttributeError) as error:
        raise ValidationError("resource muss eine gültige Ressourcen-UUID sein.") from error
    try:
        resource = ContentResource.objects.get(pk=resource_id)
    except ContentResource.DoesNotExist as error:
        raise ValidationError(f"Ressource {resource_id} existiert nicht.") from error
    revision_id = item.get("revision")
    if revision_id is not None and (type(revision_id) is not int or revision_id < 1):
        raise ValidationError("revision muss eine Revisionsdatenbank-ID oder null sein.")
    try:
        revision = ContentRevision.objects.get(pk=revision_id) if revision_id is not None else None
    except ContentRevision.DoesNotExist as error:
        raise ValidationError(f"Revision {revision_id} existiert nicht.") from error
    return {"resource": resource, "revision": revision, "position": item.get("position", 0)}


@transaction.atomic
def save_collection(*, collection: ContentCollection | None, expected: int, title: str, domain: str,
                    kind: str, description: str, data: dict, user) -> ContentCollection:
    """Validate the complete composition and persist it as one optimistic update."""
    entries, links = _validate_shape(data, kind)
    if collection is None:
        resource = ContentResource(kind="collection", domain=domain, title=title)
        resource.full_clean()
        resource.save()
        collection = ContentCollection(resource=resource, kind=kind, description=description, created_by=user)
        collection.full_clean()
        collection.save()
    else:
        changed = ContentCollection.objects.filter(
            pk=collection.pk, version=expected, source_revision__isnull=True,
        ).update(version=F("version") + 1, kind=kind, description=description, updated_at=timezone.now())
        if not changed:
            raise RevisionConflict("Zusammenstellung geändert oder Quellgliederung schreibgeschützt. Bitte neu laden.")
        collection.refresh_from_db()
        collection.resource.title, collection.resource.domain = title, domain
        collection.resource.full_clean()
        collection.resource.save()
        collection.full_clean()
    historical_links = {
        (link.source.key, link.target.key, str(link.source.resource_id),
         str(link.target.resource_id), link.relation_type_id): link.relation_type
        for link in collection.links.select_related("source", "target", "relation_type")
    }
    _save_entries(collection, entries)
    _save_links(collection, links, historical_links)
    return collection


def _save_entries(collection: ContentCollection, entries: list[dict]) -> None:
    collection.links.all().delete()
    # Detach first, so reparenting cannot delete or retain stale containment.
    collection.entries.update(parent=None)
    saved = {}
    for item in entries:
        entry = collection.entries.filter(key=item["key"]).first() or CollectionEntry(
            collection=collection, key=item["key"],
        )
        for field, value in _entry_values(item).items():
            setattr(entry, field, value)
        entry.full_clean()
        entry.save()
        saved[entry.key] = entry
    collection.entries.exclude(key__in=saved).delete()
    for item in entries:
        parent = item.get("parent")
        if parent is not None:
            entry = saved[item["key"]]
            entry.parent = saved[parent]
            entry.full_clean()
            entry.save(update_fields=["parent"])


def _save_links(collection: ContentCollection, links: list[dict],
                historical_links: dict[tuple[str, str, str, str, str], RelationType]) -> None:
    entries = {item.key: item for item in collection.entries.all()}
    for item in links:
        if not isinstance(item, dict) or set(item) - {"source", "target", "type", "reason"}:
            raise ValidationError("Kante braucht source, target, type und optional reason.")
        source, target, relation_type = item.get("source"), item.get("target"), item.get("type")
        if not all(isinstance(value, str) for value in (source, target, relation_type)):
            raise ValidationError("Kantenschlüssel und Relationstyp müssen Text sein.")
        if source not in entries or target not in entries:
            raise ValidationError("Kantenende fehlt in der Zusammenstellung.")
        if not isinstance(item.get("reason", ""), str):
            raise ValidationError("Kantenbegründung muss Text sein.")
        kind = historical_links.get(
            (source, target, str(entries[source].resource_id), str(entries[target].resource_id), relation_type)
        )
        if kind is None:
            kind = resolve_relation_type(relation_type)
        link = CollectionLink(
            collection=collection, source=entries[source], target=entries[target],
            relation_type=kind, reason=item.get("reason", ""),
        )
        link.full_clean()
        link.save()


def collection_rows(collection: ContentCollection) -> list[dict]:
    """Flatten arbitrarily deep outlines iteratively, without recursive templates."""
    children = {}
    pinned_titles = {
        (snapshot.resource_id, snapshot.revision_id): snapshot.title
        for snapshot in BlockSnapshot.objects.filter(
            revision_id__in=collection.entries.exclude(revision=None).values("revision_id"),
            resource_id__in=collection.entries.values("resource_id"),
        )
    }
    for entry in collection.entries.select_related("resource", "revision", "parent"):
        children.setdefault(entry.parent_id, []).append(entry)
    rows, stack, seen = [], [(entry, 0) for entry in reversed(children.get(None, []))], set()
    while stack:
        entry, depth = stack.pop()
        if entry.pk in seen:
            raise ValidationError("Gespeicherte Gliederung enthält einen Elternzyklus.")
        seen.add(entry.pk)
        title = pinned_titles.get((entry.resource_id, entry.revision_id))
        rows.append({
            "entry": entry, "depth": depth,
            "title": title if title is not None else (
                entry.revision.title if entry.revision_id else entry.resource.title
            ),
        })
        stack.extend((child, depth + 1) for child in reversed(children.get(entry.pk, [])))
    if len(seen) != sum(len(items) for items in children.values()):
        raise ValidationError("Gespeicherte Gliederung enthält unerreichbare Einträge.")
    return rows
