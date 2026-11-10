from django.urls import path

from . import views

app_name = "content"

urlpatterns = [
    path("", views.WorkbenchView.as_view(), name="index"),
    path("import/", views.ImportView.as_view(), name="import"),
    path("runs/<uuid:pk>/", views.RunView.as_view(), name="run"),
    path("runs/<uuid:pk>/retry/", views.retry, name="retry"),
    path("documents/<uuid:pk>/", views.document, name="document"),
    path("documents/<uuid:pk>/approve/", views.approve_revision, name="approve"),
    path("documents/<uuid:pk>/download/", views.download, name="download"),
    path("export/", views.site_download, name="site-download"),
]
