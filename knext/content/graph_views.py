"""Authenticated resource catalog, typed relations and contextual compositions."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET, require_http_methods, require_POST
from django.views.generic import ListView

from knext.domains import domain_aliases

from .graph_forms import CollectionForm, FolderForm, RelationTypeForm, ResourceRelationForm
from .graph_services import collection_data, collection_rows, save_collection
from .models import ContentCollection, ContentResource, ResourceRelation
from .relation_catalog import relation_catalog, resolve_relation_type
from .outline import parse_outline
from .services import RevisionConflict


class ResourceListView(LoginRequiredMixin, ListView):
    template_name = "content/resources.html"
    context_object_name = "resources"
    paginate_by = 50

    def get_queryset(self):
        items = ContentResource.objects.select_related("document")
        if self.request.active_domain:
            items = items.filter(domain__in=domain_aliases(self.request.active_domain))
        if self.request.GET.get("q"):
            items = items.filter(title__icontains=self.request.GET["q"])
        if self.request.GET.get("kind") in ContentResource.Kind.values:
            items = items.filter(kind=self.request.GET["kind"])
        return items

    def get_context_data(self, **kwargs):
        query = self.request.GET.copy()
        query.pop("page", None)
        return super().get_context_data(kinds=ContentResource.Kind.choices, pagination_query=query.urlencode(), **kwargs)


class CollectionListView(LoginRequiredMixin, ListView):
    template_name = "content/collections.html"
    context_object_name = "collections"
    paginate_by = 30

    def get_queryset(self):
        items = ContentCollection.objects.select_related("resource", "source_revision")
        if self.request.active_domain:
            items = items.filter(resource__domain__in=domain_aliases(self.request.active_domain))
        if self.request.GET.get("q"):
            items = items.filter(resource__title__icontains=self.request.GET["q"])
        if self.request.GET.get("origin") == "custom":
            items = items.filter(source_revision__isnull=True)
        return items

    def get_context_data(self, **kwargs):
        query = self.request.GET.copy()
        query.pop("page", None)
        return super().get_context_data(pagination_query=query.urlencode(), **kwargs)


@login_required
@require_GET
def collection(request, pk):
    item = get_object_or_404(ContentCollection.objects.select_related("resource", "source_revision"), pk=pk)
    if request.GET.get("format") == "json":
        return JsonResponse({
            "id": str(item.pk), "title": item.resource.title, "domain": item.resource.domain,
            "kind": item.kind, "version": item.version, "description": item.description,
            "source_revision": item.source_revision_id, "structure": collection_data(item),
        }, json_dumps_params={"ensure_ascii": False, "indent": 2})
    intro = parse_outline(item.source_revision.body)[0] if item.source_revision_id else ""
    try:
        rows = collection_rows(item)
    except ValidationError as error:
        return HttpResponse("; ".join(error.messages), status=409)
    return render(request, "content/collection.html", {
        "collection": item, "rows": rows, "intro": intro,
        "links": item.links.select_related("source__resource", "target__resource", "relation_type"),
    })


@login_required
@require_http_methods(["GET", "POST"])
def edit_collection(request, pk=None):
    item = get_object_or_404(ContentCollection.objects.select_related("resource"), pk=pk) if pk else None
    if item and item.source_revision_id:
        return HttpResponse("Quellgliederungen sind schreibgeschützt. Bitte eine eigene Zusammenstellung anlegen.", status=409)
    if request.method == "POST":
        form = CollectionForm(request.POST)
        if form.is_valid():
            try:
                saved = save_collection(collection=item, user=request.user, **form.cleaned_data)
            except ValidationError as error:
                form.add_error("data", error)
            except RevisionConflict as error:
                form.add_error(None, str(error))
                return render(request, "content/collection_edit.html", {"form": form, "collection": item}, status=409)
            else:
                messages.success(request, "Zusammenstellung gespeichert; keine Veröffentlichung.")
                return redirect("content:collection", pk=saved.pk)
    else:
        form = CollectionForm.for_collection(item, collection_data(item)) if item else CollectionForm(initial={
            "domain": domain_aliases(request.active_domain)[-1] if request.active_domain else "",
        })
    return render(request, "content/collection_edit.html", {"form": form, "collection": item},
                  status=400 if request.method == "POST" else 200)


@login_required
@require_http_methods(["GET", "POST"])
def resource(request, pk):
    item = get_object_or_404(ContentResource.objects.select_related("document"), pk=pk)
    form = ResourceRelationForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                relation = ResourceRelation(
                    source=item, target=form.cleaned_data["target_id"], created_by=request.user,
                    relation_type=resolve_relation_type(form.cleaned_data["relation_type"]),
                    reason=form.cleaned_data["reason"],
                )
                relation.full_clean()
                relation.save()
        except ValidationError as error:
            form.add_error(None, error)
        except IntegrityError:
            form.add_error(None, "Diese Relation existiert bereits.")
        else:
            messages.success(request, "Relation gespeichert.")
            return redirect("content:resource", pk=pk)
    return render(request, "content/resource.html", {
        "resource": item, "form": form,
        "snapshots": item.snapshots.select_related("revision").order_by("-revision__number"),
        "outgoing": item.outgoing_relations.select_related("target", "relation_type"),
        "incoming": item.incoming_relations.select_related("source", "relation_type"),
    }, status=400 if request.method == "POST" else 200)


@login_required
@require_POST
def delete_relation(request, pk):
    item = get_object_or_404(ResourceRelation, pk=pk)
    source_id = item.source_id
    item.delete()
    messages.success(request, "Relation entfernt.")
    return redirect("content:resource", pk=source_id)


@login_required
@require_http_methods(["GET", "POST"])
def relation_types(request):
    form = RelationTypeForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                form.save()
        except IntegrityError:
            form.add_error("key", "Dieser Schlüssel existiert bereits.")
        else:
            messages.success(request, "Relationstyp mit Definition angelegt.")
            return redirect("content:relation-types")
    return render(request, "content/relation_types.html", {
        "form": form, "types": relation_catalog(),
    }, status=400 if request.method == "POST" else 200)


@login_required
@require_http_methods(["GET", "POST"])
def create_folder(request):
    form = FolderForm(request.POST if request.method == "POST" else None)
    if request.method == "POST" and form.is_valid():
        item = form.save(commit=False)
        item.kind = ContentResource.Kind.FOLDER
        item.full_clean()
        item.save()
        return redirect("content:resource", pk=item.pk)
    return render(request, "content/folder_edit.html", {"form": form},
                  status=400 if request.method == "POST" else 200)
