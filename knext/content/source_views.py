"""Explicit provision, register and extract steps before workshop editing."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_POST
from knext.domains import domain_aliases

from .forms import RegisterSourceForm
from .importers.base import ImportFailure
from .inventory import provisioned_files, register_provisioned
from .models import SourceAsset
from .services import extract_source
from .jobs import enqueue_sources
from .job_views import page_context
from .models import ImportJob


@login_required
@require_GET
def inventory(request: HttpRequest) -> HttpResponse:
    try:
        files = provisioned_files()
    except ImportFailure as error:
        return render(request, "content/inventory.html", {"error": str(error)}, status=422)
    sources = SourceAsset.objects.defer("data").order_by("-created_at")
    if request.active_domain:
        names = domain_aliases(request.active_domain)
        files = [file for file in files if file.domain in names]
        sources = sources.filter(domain__in=names)
    search = request.GET.get("q", "")
    if search:
        files = [file for file in files if search.casefold() in file.relative_path.casefold()]
        sources = sources.filter(filename__icontains=search)
    if request.GET.get("format"):
        value = request.GET["format"].lstrip(".")
        files = [file for file in files if file.format == value]
        sources = sources.filter(format="." + value)
    if request.GET.get("registered") == "yes":
        files = [file for file in files if file.registration]
    elif request.GET.get("registered") == "no":
        files = [file for file in files if not file.registration]
    source_query = request.GET.copy()
    source_query.pop("sources_page", None)
    return render(request, "content/inventory.html", {
        **page_context(request, files),
        "sources": Paginator(sources, 50).get_page(request.GET.get("sources_page")),
        "sources_query": source_query.urlencode(),
    })


@login_required
@require_POST
def register(request: HttpRequest) -> HttpResponse:
    form = RegisterSourceForm(request.POST)
    if not form.is_valid():
        return HttpResponse("Ungültiger relativer Quellpfad.", status=400)
    try:
        source, created = register_provisioned(form.cleaned_data["relative_path"], request.user)
    except ImportFailure as error:
        return render(request, "content/inventory.html", {"error": str(error)}, status=422)
    messages.success(request, "Originalquelle registriert; noch nicht zerlegt." if created else
                     "Identische Originalbytes und Format bereits registriert; keine Änderungen.")
    enqueue_sources([source], ImportJob.Kind.MATERIALIZE, request.user)
    return redirect("content:source", pk=source.pk)


@login_required
@require_GET
def source(request: HttpRequest, pk) -> HttpResponse:
    item = get_object_or_404(SourceAsset.objects.defer("data"), pk=pk)
    return render(request, "content/source.html", {
        "source": item, "runs": item.runs.prefetch_related("documents"),
        "registrations": item.registrations.all(),
    })


@login_required
@require_POST
def extract(request: HttpRequest, pk) -> HttpResponse:
    item = get_object_or_404(SourceAsset, pk=pk)
    run, created = extract_source(item, request.user)
    if not created:
        messages.info(request, "Dieser Pipeline-Lauf existiert bereits; vorhandene Ergebnisse bleiben unverändert.")
    return redirect("content:run", pk=run.pk)
