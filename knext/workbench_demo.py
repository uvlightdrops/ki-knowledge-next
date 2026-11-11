"""Original Textwerkstatt UI with synthetic, read-only demonstration data."""

import hashlib
import json
from importlib.resources import files

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.csp import CSP
from django.views.decorators.cache import never_cache
from django.views.decorators.csp import csp_override


def _documents():
    text = (
        "# Textwerkstatt-Demo\n\n"
        "Dies ist ein synthetischer Beispieltext, kein importiertes Dokument.\n\n"
        "Quellen bleiben unverändert. Arbeitskopien erhalten nachvollziehbare Revisionen.\n"
    )
    documents = []
    for number, kind, title in [
        (1, "reference", "Demo: unveränderliche Referenz"),
        (2, "draft", "Demo: Arbeitskopie (nur lokaler Editorpuffer)"),
    ]:
        document_id = f"00000000-0000-4000-8000-{number:012d}"
        revision_id = f"10000000-0000-4000-8000-{number:012d}"
        annotation = {
            "id": f"20000000-0000-4000-8000-{number:012d}",
            "document_id": document_id, "document_title": title, "revision_id": revision_id,
            "title": "Beispielmarkierung", "category": "concept", "tags": ["demo"],
            "note": "Synthetische Markierung zur Ansicht der Originaloberfläche.",
            "version": 1, "etag": '"1"', "archived": False, "stale": False,
            "start": text.index("Quellen"), "end": text.index("Quellen") + len("Quellen"),
            "exact": "Quellen", "prefix": text[:text.index("Quellen")][-32:],
            "suffix": text[text.index("Quellen") + len("Quellen"):][:32],
            "representation": "markdown-source-v1", "offset_unit": "unicode-codepoints",
        }
        documents.append({
            "id": document_id, "title": title, "kind": kind, "version": 1, "etag": '"1"',
            "head_revision_id": revision_id,
            "origin_revision_id": "10000000-0000-4000-8000-000000000001" if number == 2 else None,
            "revision": {
                "id": revision_id, "text": text, "parent_id": None, "cause": "demo",
                "created_at": "2026-11-11T05:00:00+01:00",
                "content_sha256": hashlib.sha256(text.encode()).hexdigest(),
            },
            "annotations": [annotation], "historical_annotations": [], "relations": [],
        })
    return documents


@login_required
@never_cache
@csp_override({
    "default-src": [CSP.SELF],
    "style-src": [CSP.SELF, CSP.UNSAFE_INLINE],
    "font-src": [CSP.SELF, "data:"],
    "worker-src": [CSP.SELF, "blob:"],
    "object-src": [CSP.NONE],
    "base-uri": [CSP.NONE],
    "frame-ancestors": [CSP.NONE],
})
def workbench_demo(request):
    manifest = json.loads(files("knext.content").joinpath(
        "static/django_site/workbench/manifest.json",
    ).read_text())
    entry = manifest["src/main.tsx"]
    return render(request, "workbench_demo.html", {
        "workbench_script": "django_site/workbench/" + entry["file"],
        "workbench_styles": ["django_site/workbench/" + css for css in entry["css"]],
        "bootstrap": {
            "domain": "UI-Demo", "apiBase": "/workbench/demo-api/",
            "canCapture": True, "offsetUnit": "unicode-codepoints",
        },
    })


def _error(message, status):
    return JsonResponse({"error": {"message": message}}, status=status)


@never_cache
def demo_api(request, resource):
    if not request.user.is_authenticated:
        return _error("Bitte anmelden, um die UI-Demo zu öffnen.", 401)
    if request.method not in {"GET", "HEAD"}:
        response = _error(
            "UI-Demo ohne Schreibzugriff: Änderungen, Archivierung und KI-Aufrufe "
            "werden nicht gespeichert oder ausgeführt.", 405,
        )
        response["Allow"] = "GET, HEAD"
        return response
    if request.GET.get("domain") != "UI-Demo":
        return _error("Diese API stellt ausschließlich synthetische UI-Demo-Daten bereit.", 400)
    documents = _documents()
    if resource == "sources":
        return JsonResponse({"sources": [{
            "id": "30000000-0000-4000-8000-000000000001",
            "title": "Demo-Quelle (synthetisch)", "folder": "UI-Demo/md",
            "relative": "beispiel.md", "registered": True,
        }], "excluded": []})
    if resource == "documents":
        return JsonResponse({"documents": [] if request.GET.get("archived") == "1" else documents})
    if resource == "annotations":
        return JsonResponse({"annotations": [] if request.GET.get("archived") == "1"
                             else [d["annotations"][0] for d in documents]})
    if resource == "relations":
        return JsonResponse({"relations": []})
    if resource == "conversations":
        if request.GET.get("document_id") not in {d["id"] for d in documents}:
            return _error("Unbekanntes Demo-Dokument.", 404)
        return JsonResponse({"conversations": []})
    if resource == "provider":
        return _error("KI ist in dieser UI-Demo nicht verbunden. Es wird kein Provider aufgerufen.", 501)
    for document in documents:
        base = "documents/" + document["id"]
        if resource in {base, base + "/revisions/" + document["revision"]["id"]}:
            return JsonResponse(document)
        if resource == base + "/revisions":
            return JsonResponse({"revisions": [document["revision"]]})
        if resource == base + "/proposals":
            return JsonResponse({"proposals": []})
    return _error("Unbekannte Ressource der UI-Demo.", 404)
