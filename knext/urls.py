from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView

from .health import ready
from .workbench_demo import demo_api, workbench_demo
from .domains import manage_domains, select_domain

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="wissenswiki:workspace")),
    path("health/ready/", ready, name="readiness"),
    path("favicon.ico", lambda request: HttpResponse(status=204)),
    path("admin/", admin.site.urls),
    path("wiki/", include(("knext.wiki", "wissenswiki"), namespace="wissenswiki")),
    path("content/", include("knext.content.urls")),
    path("workbench/", workbench_demo, name="workbench-demo"),
    path("workbench/demo-api/<path:resource>", demo_api, name="workbench-demo-api"),
    path("domains/", manage_domains, name="domains"),
    path("domains/select/", select_domain, name="select-domain"),
]
