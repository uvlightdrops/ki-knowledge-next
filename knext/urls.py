from django.contrib import admin
from django.http import HttpResponse
from django.urls import include, path
from django.views.generic import RedirectView

urlpatterns = [
    path("", RedirectView.as_view(pattern_name="wissenswiki:workspace")),
    path("favicon.ico", lambda request: HttpResponse(status=204)),
    path("admin/", admin.site.urls),
    path("wiki/", include("wissenswiki.urls")),
]
