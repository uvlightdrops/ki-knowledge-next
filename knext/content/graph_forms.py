"""Explicit forms for shared graph editing in the authenticated prototype."""

from django import forms

from .models import ContentCollection, ContentResource, RelationType
from .relation_catalog import relation_catalog


class CollectionForm(forms.Form):
    title = forms.CharField(label="Titel", max_length=255)
    domain = forms.CharField(label="Domäne", max_length=150)
    kind = forms.ChoiceField(label="Form", choices=ContentCollection.Kind.choices)
    description = forms.CharField(label="Beschreibung", required=False, widget=forms.Textarea(attrs={"rows": 3}))
    expected = forms.IntegerField(min_value=0, widget=forms.HiddenInput, initial=0)
    data = forms.JSONField(
        label="Einträge und Querverweise", widget=forms.Textarea(attrs={"rows": 22}),
        initial={"entries": [], "links": []},
        help_text="Ressourcen-UUIDs stehen im Katalog; parent verweist auf einen lokalen key.",
    )

    @classmethod
    def for_collection(cls, collection, data):
        return cls(initial={
            "title": collection.resource.title, "domain": collection.resource.domain,
            "kind": collection.kind, "description": collection.description, "expected": collection.version,
            "data": data,
        })


class FolderForm(forms.ModelForm):
    class Meta:
        model = ContentResource
        fields = ["title", "domain"]
        labels = {"title": "Ordnername", "domain": "Domäne"}


class RelationTypeForm(forms.ModelForm):
    def clean_key(self) -> str:
        key = self.cleaned_data["key"]
        if any(item.key == key for item in relation_catalog()):
            raise forms.ValidationError("Dieser Schlüssel ist bereits im effektiven Relationenkatalog definiert.")
        return key

    class Meta:
        model = RelationType
        fields = ["key", "label", "description"]
        labels = {"key": "Stabiler Schlüssel", "label": "Bezeichnung"}
        widgets = {"description": forms.Textarea(attrs={"rows": 4})}


class ResourceRelationForm(forms.Form):
    target_id = forms.UUIDField(label="Zielressource (UUID)")
    relation_type = forms.ChoiceField(label="Relationstyp")
    reason = forms.CharField(
        label="Begründung", required=False, widget=forms.Textarea(attrs={"rows": 3}),
    )

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["relation_type"].choices = [
            (item.key, f"{item.label} ({item.key})") for item in relation_catalog() if item.enabled
        ]

    def clean_target_id(self) -> ContentResource:
        value = self.cleaned_data["target_id"]
        try:
            return ContentResource.objects.get(pk=value)
        except ContentResource.DoesNotExist as error:
            raise forms.ValidationError("Zielressource existiert nicht; bitte Katalog prüfen.") from error
