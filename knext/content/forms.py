"""Forms for source registration and optimistic revision editing."""

from django import forms
from .importers.base import ImportFailure, MAX_TEXT_CHARS
from .markdown_document import split_markdown


class DocumentListFilterForm(forms.Form):
    q = forms.CharField(label="Dokument", required=False, max_length=255)
    domain_q = forms.CharField(label="Domäne", required=False, max_length=150)
    folder = forms.CharField(label="Ordner", required=False, max_length=1000)
    filename = forms.CharField(label="Dateiname", required=False, max_length=255)
    revision = forms.IntegerField(label="Arbeitsstand", required=False, min_value=1)
    approved = forms.ChoiceField(label="Freigabe", required=False, choices=[
        ("", "Alle"), ("yes", "Freigegeben"), ("no", "Nicht freigegeben"),
    ])


class RevisionForm(forms.Form):
    expected = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    title = forms.CharField(label="Titel", max_length=255)
    body = forms.CharField(
        label="Inhalt (Markdown, ohne YAML-Header)", max_length=MAX_TEXT_CHARS, strip=False,
        widget=forms.Textarea(attrs={"rows": 24, "spellcheck": "false"}),
    )

    def clean_body(self) -> str:
        body = self.cleaned_data["body"]
        try:
            if split_markdown(body).header:
                raise ImportFailure("YAML-Header werden getrennt verwaltet und gehören nicht in den Texteditor.")
        except ImportFailure as error:
            raise forms.ValidationError(str(error)) from error
        if not body.strip():
            raise forms.ValidationError("Markdown-Inhalt darf nicht leer sein.")
        return body


class ApprovalForm(forms.Form):
    expected = forms.IntegerField(min_value=1, widget=forms.HiddenInput)


class EditorRestoreForm(ApprovalForm):
    number = forms.IntegerField(min_value=1)

    def clean(self) -> dict:
        cleaned = super().clean()
        if "number" in cleaned and "expected" in cleaned and cleaned["number"] >= cleaned["expected"]:
            raise forms.ValidationError("Bitte einen früheren Sicherungsstand wählen.")
        return cleaned


class RegisterSourceForm(forms.Form):
    relative_path = forms.CharField(max_length=1000, widget=forms.HiddenInput)
