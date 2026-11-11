"""Read-only extraction/history and explicit revision-based restore."""

from difflib import unified_diff
import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST

from .forms import ApprovalForm
from .importers.base import ImportFailure
from .models import ContentDocument, ContentRevision, ExtractionSnapshot
from .rendering import render_revision
from .services import RevisionConflict, restore
from .markdown_document import split_markdown
from .outline import parse_outline


@login_required
@require_GET
def revision(request: HttpRequest, pk, number: int) -> HttpResponse:
    item = get_object_or_404(
        ContentRevision.objects.select_related("document__run__source", "parent", "created_by")
        .defer("document__run__source__data"), document_id=pk, number=number,
    )
    if request.GET.get("format") == "markdown":
        return _markdown(item.yaml_header + item.body, f"{pk}-r{number}.md")
    previous = item.parent
    before = previous.yaml_header + previous.body if previous else ""
    diff = "\n".join(unified_diff(
        before.splitlines(), (item.yaml_header + item.body).splitlines(),
        fromfile=f"Revision {previous.number}" if previous else "Leer",
        tofile=f"Revision {item.number}", lineterm="",
    ))
    return render(request, "content/revision.html", {
        "revision": item, "document": item.document, "body_html": render_revision(item),
        "diff": diff, "restore_form": ApprovalForm(initial={"expected": item.document.revision_number}),
    })


@login_required
@require_POST
def restore_revision(request: HttpRequest, pk, number: int) -> HttpResponse:
    item = get_object_or_404(ContentDocument, pk=pk)
    form = ApprovalForm(request.POST)
    if not form.is_valid():
        return HttpResponse("Ungültige aktuelle Revisionsnummer.", status=400)
    try:
        restore(item, expected=form.cleaned_data["expected"], number=number, user=request.user)
    except RevisionConflict as error:
        return HttpResponse(str(error), status=409)
    except (ImportFailure, ValidationError) as error:
        return HttpResponse(str(error), status=400)
    messages.success(request, "Historischer Stand als neue Revision übernommen; Freigabe unverändert.")
    return redirect("content:document", pk=pk)


@login_required
@require_GET
def extraction(request: HttpRequest, pk) -> HttpResponse:
    item = get_object_or_404(
        ExtractionSnapshot.objects.select_related("document__run__source")
        .defer("document__run__source__data"), document_id=pk,
    )
    if request.GET.get("format") == "markdown":
        return _markdown(item.markdown, f"{pk}-extraction.md")
    return render(request, "content/extraction.html", {"extraction": item, "document": item.document})


@login_required
@require_GET
def extraction_blocks(request: HttpRequest, pk) -> HttpResponse:
    item = get_object_or_404(ExtractionSnapshot.objects.select_related("document"), document_id=pk)
    parsed = split_markdown(item.markdown)
    try:
        intro, blocks = parse_outline(parsed.body)
    except ImportFailure as error:
        return HttpResponse(str(error), status=400)
    return render(request, "content/blocks.html", {
        "extraction": item, "document": item.document,
        "frontmatter": json.dumps(parsed.frontmatter, ensure_ascii=False, indent=2, sort_keys=True),
        "adapter_metadata": json.dumps(item.metadata, ensure_ascii=False, indent=2, sort_keys=True),
        "intro": intro, "blocks": blocks,
    })


def _markdown(text: str, filename: str) -> HttpResponse:
    return HttpResponse(text, content_type="text/markdown; charset=utf-8", headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
    })
