"""Shared filtered lists, bounded batch submissions and explicit job control."""

import logging
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_GET, require_POST

from knext.domains import domain_aliases

from .file_catalog import file_catalog
from .artifacts import read_artifact
from .importers.base import ImportFailure
from .jobs import cancel_job, cancel_jobs, enqueue_paths, enqueue_run, enqueue_sources, retry_job, worker_running
from .models import FilesystemArtifact, ImportBatch, ImportJob, ImportRun, SourceAsset
from .services import RevisionConflict

logger = logging.getLogger(__name__)


def progress_context(query):
    counts = dict(query.order_by().values("status").annotate(total=Count("pk")).values_list("status", "total"))
    total = sum(counts.values())
    pending = counts.get("queued", 0) + counts.get("running", 0)
    try:
        running = worker_running()
        error = ""
    except OSError as failure:
        logger.exception("Importworkerstatus konnte nicht gelesen werden.")
        running, error = None, f"Workerstatus nicht prüfbar: {failure}"
    return {
        "worker_running": running, "worker_error": error,
        "job_counts": [(label, counts.get(value, 0)) for value, label in ImportJob.Status.choices],
        "job_total": total, "job_finished": total - pending,
    }


def filter_query(request, query, domain_field="domain"):
    if request.active_domain:
        query = query.filter(**{domain_field + "__in": domain_aliases(request.active_domain)})
    return query


def page_context(request, query, **extra):
    return {
        "page_obj": Paginator(query, 50).get_page(request.GET.get("page")),
        "filter_query": request.GET.urlencode(),
        "pagination_query": _pagination_query(request), **extra,
    }


def _pagination_query(request):
    query = request.GET.copy()
    query.pop("page", None)
    return query.urlencode()


@login_required
@require_GET
def files(request):
    try:
        catalog, errors, summary = file_catalog()
    except ImportFailure as error:
        return render(request, "content/files.html", {"error": str(error)}, status=422)
    if request.active_domain:
        names = domain_aliases(request.active_domain)
        catalog = [file for file in catalog if file.domain in names]
        summary = [row for row in summary if row["domain"] in names]
    for key in ["area", "format"]:
        value = request.GET.get(key, "")
        if value:
            catalog = [file for file in catalog if getattr(file, key) == value]
    search = request.GET.get("q", "").casefold()
    catalog = [file for file in catalog if search in file.relative_path.casefold()]
    return render(request, "content/files.html", page_context(
        request, catalog, summary=summary, errors=errors,
        total_files=sum(row["files"] for row in summary), total_bytes=sum(row["bytes"] for row in summary),
    ))


@login_required
@require_GET
def jobs(request):
    query = filter_query(request, ImportJob.objects.select_related("batch", "source", "run").defer("source__data"))
    if request.GET.get("status"):
        query = query.filter(status=request.GET["status"])
    if request.GET.get("kind"):
        query = query.filter(kind=request.GET["kind"])
    if request.GET.get("q"):
        query = query.filter(Q(relative_path__icontains=request.GET["q"]) | Q(source__filename__icontains=request.GET["q"]))
    return render(request, "content/jobs.html", page_context(
        request, query.order_by("-created_at"), statuses=ImportJob.Status, kinds=ImportJob.Kind,
        **progress_context(query),
    ))


@login_required
@require_GET
def job(request, pk):
    item = get_object_or_404(ImportJob.objects.select_related("batch", "source", "run").defer("source__data"), pk=pk)
    return render(request, "content/job.html", {
        "job": item, "attempts": item.history.all(),
        **progress_context(ImportJob.objects.filter(pk=pk)),
    })


@login_required
@require_GET
def batch(request, pk):
    item = get_object_or_404(ImportBatch, pk=pk)
    return render(request, "content/batch.html", {
        "batch": item, **page_context(request, item.jobs.select_related("batch", "source", "run").defer("source__data")),
        **progress_context(item.jobs.all()),
    })


@login_required
@require_POST
def enqueue_batch(request):
    kind = request.POST.get("kind", "")
    try:
        if kind in {ImportJob.Kind.REGISTER, ImportJob.Kind.IMPORT}:
            result = enqueue_paths(request.POST.getlist("paths"), kind, request.user)
        else:
            values = list(dict.fromkeys(request.POST.getlist("sources")))
            if not 0 < len(values) <= 100:
                raise ImportFailure("Bitte 1 bis 100 Quellen auswählen.")
            try:
                ids = [uuid.UUID(value) for value in values]
            except ValueError as error:
                raise ImportFailure("Ungültige Quellenauswahl.") from error
            sources = SourceAsset.objects.filter(pk__in=ids)
            if sources.count() != len(ids):
                raise ImportFailure("Mindestens eine ausgewählte Quelle existiert nicht mehr.")
            result = enqueue_sources(sources, kind, request.user)
    except ImportFailure as error:
        messages.error(request, str(error))
        url = reverse("content:inventory")
        return redirect(f"{url}?{request.GET.urlencode()}" if request.GET else url)
    messages.success(request, "Batch eingereiht. Workerstatus und Fortschritt stehen auf der Batchseite.")
    return redirect("content:batch", pk=result.pk)


@login_required
@require_POST
def control(request, pk):
    item = get_object_or_404(ImportJob.objects.select_related("batch"), pk=pk)
    if item.batch.created_by_id != request.user.pk and not request.user.is_staff:
        return HttpResponse("Nur Auftraggeber oder Administratoren dürfen Jobs steuern.", status=403)
    try:
        action = request.POST.get("action")
        if action == "retry":
            retry_job(item)
        elif action == "cancel":
            cancel_job(item)
        else:
            return HttpResponse("Unbekannte Jobaktion.", status=400)
    except RevisionConflict as error:
        return HttpResponse(str(error), status=409)
    return redirect("content:job", pk=item.pk)


@login_required
@require_POST
def cancel_selected(request):
    values = list(dict.fromkeys(request.POST.getlist("jobs")))
    if not 0 < len(values) <= 100:
        return HttpResponse("Bitte 1 bis 100 wartende Jobs auswählen.", status=400)
    try:
        ids = [uuid.UUID(value) for value in values]
        batch_id = uuid.UUID(request.POST["batch"]) if request.POST.get("batch") else None
    except ValueError:
        return HttpResponse("Ungültige Job- oder Batchauswahl.", status=400)
    try:
        count = cancel_jobs(ids, request.user, batch_id=batch_id)
    except PermissionError as error:
        return HttpResponse(str(error), status=403)
    except ImportFailure as error:
        return HttpResponse(str(error), status=400)
    except RevisionConflict as error:
        return HttpResponse(str(error), status=409)
    messages.success(request, f"{count} wartende Jobs abgebrochen.")
    if batch_id:
        return redirect("content:batch", pk=batch_id)
    url = reverse("content:jobs")
    return redirect(f"{url}?{request.GET.urlencode()}" if request.GET else url)


@login_required
@require_POST
def materialize(request, pk):
    run = get_object_or_404(ImportRun, pk=pk)
    if run.status != ImportRun.Status.SUCCEEDED:
        return HttpResponse("Nur erfolgreiche Extraktionen können gesichert werden.", status=409)
    result = enqueue_run(run, request.user)
    return redirect("content:batch", pk=result.pk)


@login_required
@require_GET
def artifact(request, pk):
    item = get_object_or_404(FilesystemArtifact, pk=pk)
    # Serve the immutable DB snapshot, not a potentially administrator-edited local file.
    if item.kind == "markdown":
        document_id = item.relative_path.rsplit("/", 1)[1].removesuffix(".md")
        snapshot = item.run.documents.get(pk=document_id).extraction
        return HttpResponse(snapshot.markdown, content_type="text/markdown; charset=utf-8")
    if item.kind == "manifest":
        try:
            raw = read_artifact(item)
        except (ImportFailure, OSError) as error:
            return HttpResponse(f"Manifest nicht verifizierbar: {error}", status=409)
        return HttpResponse(raw, content_type="application/json")
    response = HttpResponse(bytes(item.source.data), content_type="application/octet-stream")
    response["Content-Disposition"] = f'attachment; filename="{item.source.pk}{item.source.format}"'
    return response
