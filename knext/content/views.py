"""Authenticated import workbench, draft editor and explicit publication endpoints."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F, OuterRef, Subquery, Value
from django.db.models.functions import Coalesce, Greatest, Length, Lower, StrIndex, Substr
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, ListView, TemplateView
from knext.domains import domain_aliases

from .forms import ApprovalForm, DocumentListFilterForm, RevisionForm
from .importers.base import ImportFailure
from .models import ContentDocument, ImportRun, SourceRegistration
from .rendering import build_site, render_output, render_revision
from .services import RevisionConflict, approve, process_run, revise


class WorkbenchView(LoginRequiredMixin, ListView):
    template_name = "content/index.html"
    context_object_name = "runs"
    paginate_by = 30

    def get_queryset(self):
        runs = ImportRun.objects.select_related("source").defer("source__data").prefetch_related("documents")
        if self.request.active_domain:
            runs = runs.filter(source__domain__in=domain_aliases(self.request.active_domain))
        if self.request.GET.get("q"):
            runs = runs.filter(source__filename__icontains=self.request.GET["q"])
        if self.request.GET.get("status"):
            runs = runs.filter(status=self.request.GET["status"])
        return runs

    def get_context_data(self, **kwargs):
        query = self.request.GET.copy()
        query.pop("page", None)
        return super().get_context_data(
            statuses=ImportRun.Status,
            pagination_query=query.urlencode(), **kwargs,
        )


class OutputView(LoginRequiredMixin, TemplateView):
    template_name = "content/output_index.html"

    def get_context_data(self, **kwargs):
        approved = ContentDocument.objects.filter(approved_revision__isnull=False)
        if self.request.active_domain:
            approved = approved.filter(run__source__domain__in=domain_aliases(self.request.active_domain))
        return super().get_context_data(
            domains=approved.order_by("run__source__domain")
            .values_list("run__source__domain", flat=True).distinct(), **kwargs,
        )


class DocumentListView(LoginRequiredMixin, ListView):
    template_name = "content/documents.html"
    context_object_name = "documents"
    paginate_by = 30
    columns = (
        ("q", "title", "Titel"),
        ("domain_q", "run__source__domain", "Domäne"),
        ("folder", "source_folder", "Ordner"),
        ("filename", "run__source__filename", "Dateiname"),
        ("revision", "revision_number", "Arbeitsstand"),
        ("approved", "approved_revision__number", "Freigabe"),
    )

    def get_queryset(self):
        registrations = SourceRegistration.objects.filter(
            source_id=OuterRef("run__source_id"),
        ).order_by("-registered_at", "-pk")
        documents = ContentDocument.objects.select_related(
            "run__source", "approved_revision",
        ).defer("run__source__data").annotate(
            registered_path=Coalesce(Subquery(registrations.values("relative_path")[:1]), Value("")),
        ).annotate(
            source_folder=Substr(
                "registered_path", StrIndex("registered_path", Value("/")) + 1,
                # Registration paths are DOMAIN/FOLDER/FILENAME; omit domain and basename.
                Greatest(Length("registered_path") - StrIndex("registered_path", Value("/"))
                         - Length("run__source__filename") - 1, Value(0)),
            ),
        )
        if self.request.active_domain:
            documents = documents.filter(run__source__domain__in=domain_aliases(self.request.active_domain))
        self.filter_form = DocumentListFilterForm(self.request.GET)
        if not self.filter_form.is_valid():
            return documents.none()
        return self._ordered_documents(self._filtered_documents(documents))

    def _filtered_documents(self, documents):
        for parameter, field, _ in self.columns:
            value = self.filter_form.cleaned_data[parameter]
            if value not in ("", None):
                if parameter == "approved":
                    documents = documents.filter(approved_revision__isnull=value == "no")
                else:
                    lookup = field if parameter == "revision" else field + "__icontains"
                    documents = documents.filter(**{lookup: value})
        return documents

    def _ordered_documents(self, documents):
        sort = self.request.GET.get("sort", "")
        column = next((item for item in self.columns if item[0] == sort.lstrip("-")), None)
        if column is None:
            return documents.order_by("-created_at", "id")
        expression = F(column[1]) if column[0] in {"revision", "approved"} else Lower(column[1])
        order = expression.desc(nulls_last=True) if sort.startswith("-") else expression.asc(nulls_last=True)
        return documents.order_by(order, "id")

    def get_context_data(self, **kwargs):
        query = self.request.GET.copy()
        query.pop("page", None)
        columns = []
        for parameter, _, label in self.columns:
            current = self.request.GET.get("sort", "")
            query["sort"] = "-" + parameter if current == parameter else parameter
            columns.append({
                "label": label, "filter": self.filter_form[parameter], "url": "?" + query.urlencode(),
                "direction": "ascending" if current == parameter else
                    "descending" if current == "-" + parameter else "none",
            })
        query = self.request.GET.copy()
        query.pop("page", None)
        return super().get_context_data(
            columns=columns, filter_form=self.filter_form,
            pagination_query=query.urlencode(), **kwargs,
        )


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
            except ImportFailure as error:
                form.add_error("body", str(error))
                return render(request, "content/document.html", _document_context(item, form), status=400)
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
