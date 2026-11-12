"""Host navigation shared by content, embedded wiki and Django administration."""

from urllib.parse import urlencode

from django.http import HttpRequest
from django.urls import reverse


# Entries associate detail and action views with their nearest navigable area.
GROUPS = (
    ("input", "INPUT", (
        ("content:index", "Inhalte", {"content:index", "content:run", "content:retry", "content:materialize"}, False),
        ("content:inventory", "Quellen", {"content:inventory", "content:register-source", "content:source", "content:extract-source"}, False),
        ("content:files", "Dateien", {"content:files", "content:artifact"}, False),
        ("content:jobs", "Jobs", {"content:jobs", "content:job", "content:batch", "content:job-control", "content:enqueue-batch"}, False),
    )),
    ("intern", "INTERN", (
        ("content:documents", "Werkstatt", {"content:documents", "content:document", "content:revision", "content:extraction", "content:restore", "content:approve", "content:download", "content:extraction-blocks"}, False),
        ("content:editor-index", "Editor · Entwurf", {"content:editor-index", "content:editor", "content:editor-restore", "content:editor-preview"}, False),
        ("content:editor-wide-index", "Editor breit · Entwurf", {"content:editor-wide-index", "content:editor-wide", "content:editor-wide-restore"}, False),
        ("content:collections", "Zusammenstellungen", {"content:collections", "content:collection", "content:collection-edit", "content:collection-create"}, False),
        ("content:resources", "Ressourcen", {"content:resources", "content:resource", "content:folder-create"}, False),
        ("content:relation-types", "Beziehungstypen", {"content:relation-types", "content:relation-delete"}, False),
        ("wissenswiki:graph-header", "Wissensnetz", {"wissenswiki:graph", "wissenswiki:graph-header"}, True),
        ("wissenswiki:workspace", "Arbeitsraum", {"wissenswiki:workspace"}, False),
        ("workbench-demo", "Demo", {"workbench-demo"}, False),
    )),
    ("output", "OUTPUT", (
        ("content:output", "Statische Ausgabe", {"content:output", "content:site-download"}, False),
    )),
    ("admin", "Administration", (
        ("admin:index", "Django-Administration", set(), False),
    )),
    ("settings", "Einstellungen", (
        ("domains", "Domänen", {"domains"}, False),
        ("wissenswiki:settings", "Netz-Einstellungen", {"wissenswiki:settings"}, True),
    )),
)


def navigation(request: HttpRequest) -> dict:
    match = request.resolver_match
    current = match.view_name if match else ""
    domain = getattr(request, "active_domain", "")
    groups = []
    for key, label, entries in GROUPS:
        if key == "admin" and not request.user.is_staff:
            continue
        items = []
        for name, title, views, contextual in entries:
            active = current in views or (key == "admin" and current.startswith("admin:"))
            href = reverse(name)
            if contextual and domain:
                href += "?" + urlencode({"domain": domain})
            items.append({"label": title, "href": href, "active": active})
        groups.append({"key": key, "label": label, "href": items[0]["href"],
                       "active": any(item["active"] for item in items), "items": items})
    workshop_context = current in {
        "content:collections", "content:collection", "content:collection-edit", "content:collection-create",
        "content:resources", "content:resource", "content:folder-create", "content:relation-types",
        "content:relation-delete",
    }
    return {
        "app_available_domains": getattr(request, "available_domains", []),
        "app_active_domain": domain,
        "app_workspace_theme": current == "wissenswiki:workspace",
        "app_navigation_groups": groups,
        "app_workshop_context": workshop_context,
    }
