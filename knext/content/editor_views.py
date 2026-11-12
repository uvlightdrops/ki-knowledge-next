"""Editor-first text workshop using the existing revision and outline services."""

from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods, require_POST

from .forms import EditorRestoreForm, RevisionForm
from .ai_service import public_settings
from .ai_models import TextProposal
from .importers.base import ImportFailure
from .models import ContentDocument, ContentRevision
from .outline import parse_outline
from .rendering import render_revision
from .services import RevisionConflict, restore, revise
from .views import DocumentListView


class EditorListView(DocumentListView):
    template_name = "content/editor_index.html"


class WideEditorListView(EditorListView):
    extra_context = {"editor_wide": True, "editor_route": "content:editor-wide"}


def _outline(body: str) -> list[dict]:
    """Use the same heading boundaries as persisted content resources."""
    _, blocks = parse_outline(body)
    return [
        {"title": block.title, "level": block.level, "start": block.start_line,
         "end": block.end_line, "parent": block.parent}
        for block in blocks
    ]


def _context(document: ContentDocument, form: RevisionForm | None = None, *, user=None, wide=False) -> dict:
    revision = document.revisions.get(number=document.revision_number)
    previous = document.revisions.filter(number__lt=revision.number).select_related(
        "created_by",
    ).defer("body", "metadata", "frontmatter", "yaml_header").order_by("-number")
    return {
        "document": document, "revision": revision,
        "form": form if form is not None else RevisionForm(initial={
            "expected": revision.number, "title": revision.title, "body": revision.body,
        }),
        "body_html": render_revision(revision),
        "editor_saved": {"body": revision.body, "title": revision.title},
        "editor_outline": _outline(revision.body),
        "backups": previous,
        "previous": previous.first(),
        "ai": public_settings(),
        "ai_pending": _pending(document, user) if user is not None else None,
        "editor_wide": wide,
        "editor_route": "content:editor-wide" if wide else "content:editor",
        "editor_list_route": "content:editor-wide-index" if wide else "content:editor-index",
        "editor_restore_route": "content:editor-wide-restore" if wide else "content:editor-restore",
        "editor_other_route": "content:editor" if wide else "content:editor-wide",
    }


def _render_editor(request, document, form=None, *, wide=False, status=200):
    template = "content/editor_wide.html" if wide else "content/editor.html"
    return render(request, template, _context(document, form, user=request.user, wide=wide), status=status)


def _pending(document: ContentDocument, user) -> dict | None:
    proposal = TextProposal.objects.filter(document=document, created_by=user, status="ready").first()
    if proposal is None:
        return None
    return {
        "id": str(proposal.pk), "body": proposal.base_body, "title": proposal.title,
        "expected": str(proposal.expected), "start": proposal.start, "end": proposal.end,
        "text": proposal.text, "instruction": proposal.instruction, "context": proposal.context,
        "provider": proposal.provider, "model": proposal.model,
        "accept_url": reverse("content:ai-accept", args=[proposal.pk]),
        "discard_url": reverse("content:ai-discard", args=[proposal.pk]),
    }


@login_required
@require_http_methods(["GET", "POST"])
def editor(request: HttpRequest, pk: UUID, wide=False) -> HttpResponse:
    document = get_object_or_404(ContentDocument.objects.select_related(
        "run__source", "approved_revision",
    ).defer("run__source__data"), pk=pk)
    form = None
    if request.method == "POST":
        form = RevisionForm(request.POST)
        if form.is_valid():
            try:
                revise(document, user=request.user, **form.cleaned_data)
            except (ImportFailure, ValidationError) as error:
                form.add_error("body", str(error))
                return _render_editor(request, document, form, wide=wide, status=400)
            except RevisionConflict as error:
                form.add_error(None, str(error))
                document.refresh_from_db()
                return _render_editor(request, document, form, wide=wide, status=409)
            messages.success(request, "Arbeitsstand gespeichert. Frühere Stände bleiben als Sicherungen erhalten.")
            return redirect("content:editor-wide" if wide else "content:editor", pk=pk)
        return _render_editor(request, document, form, wide=wide, status=400)
    return _render_editor(request, document, wide=wide)


@login_required
@require_POST
def preview(request: HttpRequest) -> JsonResponse:
    form = RevisionForm(request.POST)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)
    try:
        outline = _outline(form.cleaned_data["body"])
    except ImportFailure as error:
        return JsonResponse({"error": str(error)}, status=400)
    return JsonResponse({
        "html": render_revision(ContentRevision(
            title=form.cleaned_data["title"], body=form.cleaned_data["body"],
        )), "outline": outline,
    })


@login_required
@require_POST
def restore_backup(request: HttpRequest, pk: UUID, wide=False) -> HttpResponse:
    document = get_object_or_404(ContentDocument.objects.select_related(
        "run__source", "approved_revision",
    ).defer("run__source__data"), pk=pk)
    form = RevisionForm(request.POST)
    backup = EditorRestoreForm(request.POST)
    if not backup.is_valid():
        form.add_error(None, "Ungültiger Wiederherstellungsauftrag. Bitte Arbeitsstand und Sicherung prüfen.")
        return _render_editor(request, document, form, wide=wide, status=400)
    try:
        restore(document, expected=backup.cleaned_data["expected"],
                number=backup.cleaned_data["number"], user=request.user)
    except RevisionConflict as error:
        form.add_error(None, str(error))
        document.refresh_from_db()
        return _render_editor(request, document, form, wide=wide, status=409)
    except (ImportFailure, ValidationError) as error:
        form.add_error(None, str(error))
        return _render_editor(request, document, form, wide=wide, status=400)
    messages.success(request, "Sicherungsstand wiederhergestellt. Der bisherige Arbeitsstand bleibt erhalten.")
    return redirect("content:editor-wide" if wide else "content:editor", pk=pk)
