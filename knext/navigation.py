"""Host navigation shared by content, embedded wiki and Django administration."""

from urllib.parse import urlencode

from django.http import HttpRequest
from django.urls import reverse


def navigation(request: HttpRequest) -> dict:
    match = request.resolver_match
    current = match.view_name if match else ""
    domain = request.GET.get("domain", "")
    entries = [
        ("content:index", "Import und Inhalte", current.startswith("content:"), False),
        ("wissenswiki:graph-header", "Wissensnetz",
         current in {"wissenswiki:graph", "wissenswiki:graph-header"}, True),
        ("wissenswiki:workspace", "Arbeitsraum", current == "wissenswiki:workspace", False),
        ("wissenswiki:settings", "Netz-Einstellungen", current == "wissenswiki:settings", True),
    ]
    if request.user.is_staff:
        entries.append(("admin:index", "Administration", current.startswith("admin:"), False))
    return {"app_navigation_items": [{
        "label": label, "active": active,
        "href": reverse(name) + ("?" + urlencode({"domain": domain}) if contextual and domain else ""),
    } for name, label, active, contextual in entries]}
