"""Thin host adapter adding managed domains to the shared wiki renderer/API."""

from urllib.parse import quote

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.middleware.csrf import get_token
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.templatetags.static import static
from django.urls import path, reverse
from django.views.decorators.http import require_http_methods
from wissenswiki_core.pages import PageUrls, render_page
from wissenswiki_core.service import ApiError, api_get, api_post

from .domains import domain_registry


def _urls():
    return PageUrls(
        api=reverse("wissenswiki:api"), static=static(""),
        workspace=reverse("wissenswiki:workspace"), graph=reverse("wissenswiki:graph"),
        graph_header=reverse("wissenswiki:graph-header"), settings=reverse("wissenswiki:settings"),
    )


@login_required
def page(request, page):
    current = domain_registry()
    if current.workspace is None:
        if page == "workspace":
            return redirect("wissenswiki:graph")
        if not request.GET.get("domain"):
            return redirect(request.path + "?domain=" + quote(next(iter(current.domains)), safe=""))
    return HttpResponse(render_page(
        page, urls=_urls(), token=get_token(request), path=request.path,
        workspace_enabled=current.workspace is not None, domains=current.domains,
        relation_catalog=current.relation_catalog,
        app_navigation=render_to_string("navigation.html", request=request),
    ))


@login_required
@require_http_methods(["GET", "POST"])
def api(request):
    try:
        current = domain_registry()
        if request.method == "GET":
            data = api_get(current, request.GET.get("domain", ""))
        else:
            data = api_post(current, request.body, request.content_type)
    except ApiError as error:
        return JsonResponse({"error": str(error)}, status=error.status,
                            json_dumps_params={"ensure_ascii": False})
    return JsonResponse(data, json_dumps_params={"ensure_ascii": False})


urlpatterns = [
    path("", page, {"page": "workspace"}, name="workspace"),
    path("api", api, name="api"),
    path("graph/", page, {"page": "graph"}, name="graph"),
    path("graph-header/", page, {"page": "graph-header"}, name="graph-header"),
    path("settings/", page, {"page": "settings"}, name="settings"),
]
