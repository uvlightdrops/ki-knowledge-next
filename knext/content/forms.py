"""Forms for explicitly scoped uploads and optimistic revision editing."""

from django import forms
from wissenswiki.config import registry

from .importers.base import MAX_TEXT_CHARS, MAX_UPLOAD_BYTES
from .importers.registry import DocumentImporterRegistry


class UploadForm(forms.Form):
    domain = forms.ChoiceField(label="Domäne")
    file = forms.FileField(label="Quelldatei")

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields["domain"].choices = [(name, name) for name in registry().domains]
        self.fields["file"].widget.attrs["accept"] = ",".join(DocumentImporterRegistry().extensions)

    def clean_file(self):
        upload = self.cleaned_data["file"]
        if upload.size > MAX_UPLOAD_BYTES:
            raise forms.ValidationError("Maximal 10 MiB pro Datei.")
        return upload


class RevisionForm(forms.Form):
    expected = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
    title = forms.CharField(label="Titel", max_length=255)
    body = forms.CharField(
        label="Inhalt (Markdown)", max_length=MAX_TEXT_CHARS,
        widget=forms.Textarea(attrs={"rows": 24, "spellcheck": "false"}),
    )


class ApprovalForm(forms.Form):
    expected = forms.IntegerField(min_value=1, widget=forms.HiddenInput)
