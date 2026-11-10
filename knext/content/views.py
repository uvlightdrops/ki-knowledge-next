"""Authenticated import workbench, draft editor and explicit publication endpoints."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, FormView, ListView

from .forms import ApprovalForm, RevisionForm, UploadForm
from .importers.base import ImportFailure
from .importers.registry import DocumentImporterRegistry
from .models import ContentDocument, ImportRun
from .rendering import build_site, render_output, render_revision
from .services import RevisionConflict, approve, import_upload, process_run, revise


class WorkbenchView(LoginRequiredMixin, ListView):
    template_name = "content/index.html"
    context_object_name = "runs"
    paginate_by = 30

    def get_queryset(self):
        return ImportRun.objects.select_related("source").defer("source__data").prefetch_related("documents")

    def get_context_data(self, **kwargs):
        return super().get_context_data(
            form=UploadForm(), extensions=DocumentImporterRegistry().extensions,
            domains=ContentDocument.objects.filter(approved_revision__isnull=False)
            .order_by("run__source__domain").values_list("run__source__domain", flat=True).distinct(), **kwargs,
        )


class ImportView(LoginRequiredMixin, FormView):
    form_class = UploadForm
    template_name = "content/upload.html"

    def form_valid(self, form):
        try:
            run, created = import_upload(
                form.cleaned_data["file"], form.cleaned_data["domain"], self.request.user,
            )
        except ImportFailure as error:
            form.add_error("file", str(error))
            return self.form_invalid(form)
        if not created:
            messages.info(self.request, "Identische Quelle bereits erfasst; vorhandener Lauf wird angezeigt.")
        return redirect("content:run", pk=run.pk)


class RunView(LoginRequiredMixin, DetailView):
    queryset = ImportRun.objects.select_related("source").defer("source__data").prefetch_related("documents")
    template_name = "content/run.html"
    context_object_name = "run"


@login_required
@require_POST
def retry(request: HttpRequest, pk) -> HttpResponse:
    run = get_object_or_404(ImportRun, pk=pk)
    if run.status != ImportRun.Status.FAILED:
        return HttpResponse("Nur fehlgeschlagene Läufe können wiederholt werden.", status=409)
    try:
        process_run(run, request.user)
    except RevisionConflict as error:
        return HttpResponse(str(error), status=409)
    return redirect("content:run", pk=run.pk)


def _document_context(document: ContentDocument, form=None) -> dict:
    revision = document.revisions.get(number=document.revision_number)
    return {
        "document": document, "revision": revision,
        "form": form if form is not None else RevisionForm(initial={
            "expected": revision.number, "title": revision.title, "body": revision.body,
        }),
        "approval_form": ApprovalForm(initial={"expected": revision.number}),
        "body_html": render_revision(revision),
        "history": document.revisions.select_related("created_by").defer("body", "metadata"),
    }


@login_required
def document(request: HttpRequest, pk) -> HttpResponse:
    item = get_object_or_404(ContentDocument.objects.select_related(
        "run__source", "approved_revision",
    ).defer("run__source__data"), pk=pk)
    if request.method == "POST":
        form = RevisionForm(request.POST)
        if form.is_valid():
            try:
                revise(item, user=request.user, **form.cleaned_data)
            except RevisionConflict as error:
                form.add_error(None, str(error))
                item.refresh_from_db()
                return render(request, "content/document.html", _document_context(item, form), status=409)
            messages.success(request, "Neue Entwurfsrevision gespeichert. Bestehende Freigabe bleibt unverändert.")
            return redirect("content:document", pk=item.pk)
        return render(request, "content/document.html", _document_context(item, form), status=400)
    if request.method != "GET":
        return HttpResponse(status=405, headers={"Allow": "GET, POST"})
    return render(request, "content/document.html", _document_context(item))


@login_required
@require_POST
def approve_revision(request: HttpRequest, pk) -> HttpResponse:
    item = get_object_or_404(ContentDocument, pk=pk)
    form = ApprovalForm(request.POST)
    if not form.is_valid():
        return HttpResponse("Ungültige Revisionsnummer.", status=400)
    try:
        approve(item, expected=form.cleaned_data["expected"], user=request.user)
    except RevisionConflict as error:
        return HttpResponse(str(error), status=409)
    messages.success(request, "Diese Revision ist für die Ausgabe freigegeben.")
    return redirect("content:document", pk=item.pk)


@login_required
def download(request: HttpRequest, pk) -> HttpResponse:
    item = get_object_or_404(ContentDocument.objects.select_related(
        "approved_revision", "run__source",
    ).defer("run__source__data"), pk=pk)
    if item.approved_revision is None:
        return HttpResponse("Keine freigegebene Revision vorhanden.", status=409)
    return HttpResponse(render_output(item.approved_revision), content_type="text/html; charset=utf-8",
                        headers={"Content-Disposition": f'attachment; filename="{item.pk}.html"'})


@login_required
def site_download(request: HttpRequest) -> HttpResponse:
    domain = request.GET.get("domain", "")
    if not domain or not ContentDocument.objects.filter(
        run__source__domain=domain, approved_revision__isnull=False,
    ).exists():
        return HttpResponse("Keine freigegebenen Inhalte in dieser Domäne.", status=404)
    return HttpResponse(build_site(domain), content_type="application/zip",
                        headers={"Content-Disposition": 'attachment; filename="knowledge-site.zip"'})
