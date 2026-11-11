"""One effective operator vocabulary for Wiki and DB relation writes."""

from django.conf import settings
from django.core.exceptions import ValidationError
from wissenswiki_core.relations import RelationDefinition, build_catalog

from .models import RelationType


def relation_catalog() -> tuple[RelationDefinition, ...]:
    """Include operator definitions and independently defined historical DB types."""
    configured = build_catalog(settings.WISSENSWIKI.get("RELATION_CATALOG"))
    definitions = {item.key: item for item in configured}
    stored = list(RelationType.objects.order_by("key"))
    for item in stored:
        if item.key in definitions and item.description != definitions[item.key].description:
            raise ValidationError(
                f"Die gespeicherte Definition von {item.key} weicht vom Betreiberkatalog ab; "
                "einen neuen Schlüssel verwenden statt bestehende Beziehungen umzudeuten."
            )
    historical = tuple(
        RelationDefinition(
            key=item.key, label=item.label, description=item.description,
            color="gray", enabled=not item.catalog_managed,
        )
        for item in stored if item.key not in definitions
    )
    return (*configured, *historical)


def resolve_relation_type(key: str) -> RelationType:
    """Materialize a permitted definition only while writing a relation."""
    definition = next((item for item in relation_catalog() if item.key == key), None)
    if definition is None or not definition.enabled:
        raise ValidationError(f"Relationstyp nicht für neue Beziehungen freigegeben: {key}")
    item, created = RelationType.objects.get_or_create(
        key=key, defaults={
            "label": definition.label, "description": definition.description,
            "catalog_managed": True,
        },
    )
    if not created and item.description != definition.description:
        raise ValidationError(
            f"Die gespeicherte Definition von {key} weicht vom Betreiberkatalog ab; "
            "bestehende Beziehungen dürfen nicht umgedeutet werden."
        )
    return item
