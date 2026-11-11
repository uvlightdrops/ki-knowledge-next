"""Sanitized previews and portable HTML from explicitly approved revisions."""

import io
import json
from zipfile import ZIP_DEFLATED, ZipFile

from bs4 import BeautifulSoup
from django.template.loader import render_to_string
from django.utils.safestring import mark_safe
from wissenswiki_core.rendering import render_markdown as render_core_markdown

from .models import ContentDocument, ContentRevision

def render_markdown(body: str) -> str:
    return mark_safe(render_core_markdown(body))


def render_revision(revision: ContentRevision) -> str:
    """The surrounding page owns the document title; keep source Markdown unchanged."""
    soup = BeautifulSoup(render_markdown(revision.body), "html.parser")
    first = soup.find(recursive=False)
    if first and first.name == "h1" and first.get_text().strip() == revision.title.strip():
        first.decompose()
    return mark_safe(str(soup))


def render_output(revision: ContentRevision, navigation: list[dict] | None = None) -> str:
    return render_to_string("content/output.html", {
        "revision": revision, "document": revision.document,
        "body_html": render_revision(revision), "navigation": navigation or [],
    })


def build_site(domain: str) -> bytes:
    """Create an attachment only; never deploy or include unapproved drafts."""
    documents = list(ContentDocument.objects.filter(
        run__source__domain=domain, approved_revision__isnull=False,
    ).select_related("approved_revision", "run__source", "extraction").defer("run__source__data").order_by("created_at", "id"))
    navigation = [
        {"href": f"{document.pk}.html", "title": document.approved_revision.title}
        for document in documents
    ]
    output = io.BytesIO()
    with ZipFile(output, "w", ZIP_DEFLATED) as archive:
        archive.writestr("index.html", render_to_string("content/site_index.html", {
            "domain": domain, "navigation": navigation,
        }))
        for document in documents:
            archive.writestr(f"{document.pk}.html", render_output(document.approved_revision, navigation))
        archive.writestr("manifest.json", json.dumps({
            "schema": "ki-knowledge-site-v1", "domain": domain, "documents": [{
                "file": f"{document.pk}.html", "document": str(document.pk),
                "revision": document.approved_revision.number,
                "revision_id": document.approved_revision.pk,
                "revision_sha256": document.approved_revision.content_sha256,
                "extraction_sha256": document.extraction.sha256,
                "source_sha256": document.run.source.sha256,
                "pipeline": document.run.pipeline_version,
                "approved_at": document.approved_at.isoformat(),
            } for document in documents],
        }, ensure_ascii=False, indent=2))
    return output.getvalue()
