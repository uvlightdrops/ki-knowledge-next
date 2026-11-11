"""Host-managed domains and a persistent, personal browsing context."""

import os
import re
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from django import forms
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import DatabaseError, IntegrityError, transaction
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils.deprecation import MiddlewareMixin
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST
from wissenswiki.config import registry
from wissenswiki_core.domains import DocumentDomain
from wissenswiki_core.registry import Registry
from wissenswiki_core.workspace import Workspace, WorkspaceError

from .content.models import ActiveDomain, FilesystemArtifact, ManagedDomain
from .content.relation_catalog import relation_catalog


def domain_registry():
    configured = registry()
    try:
        catalog = relation_catalog()
    except ValidationError as error:
        raise ImproperlyConfigured("Relationenkatalog: " + "; ".join(error.messages)) from error
    workspace = Workspace(configured.workspace.root, relation_catalog=catalog) if configured.workspace else None
    current = Registry(workspace, {
        name: DocumentDomain(
            domain.source, domain.storage.root, lenient=domain.lenient, relation_catalog=catalog,
        ) for name, domain in configured.domains.items()
    }, relation_catalog=catalog)
    for domain in ManagedDomain.objects.all():
        config = settings.WISSENSWIKI.get("MARKDOWN_DATA")
        if not config:
            raise ImproperlyConfigured("Verwaltete Domänen benötigen MARKDOWN_DATA.")
        source = Path(config["root"]).expanduser() / domain.folder / config.get("subdir", "md")
        relations = Path(config["relations"]).expanduser() / domain.folder
        if source.is_symlink() or source.parent.is_symlink() or relations.is_symlink():
            raise ImproperlyConfigured("Verwaltete Domänen dürfen keine Symlinks verwenden.")
        existing = current.domains.get(domain.name)
        if existing is not None and existing.source != source.resolve():
            raise ImproperlyConfigured(f"Domäne {domain.name} ist mit unterschiedlichen Quellen definiert.")
        if not relations.is_dir():
            raise ImproperlyConfigured(f"Beziehungsverzeichnis für {domain.name} fehlt.")
        current.domains[domain.name] = DocumentDomain(source, relations, lenient=True, relation_catalog=catalog)
    config = settings.WISSENSWIKI.get("MARKDOWN_DATA")
    if config:
        # A worker has its own registry cache; expose newly materialized domains in the web process too.
        folders = {
            path.split("/")[0] for path in
            FilesystemArtifact.objects.filter(kind="markdown").values_list("relative_path", flat=True)
        }
        for folder in sorted(folders):
            name = config.get("prefix", "") + folder
            if name not in current.domains:
                current.domains[name] = DocumentDomain(
                    Path(config["root"]).expanduser() / folder / "md",
                    Path(config["relations"]).expanduser() / folder, lenient=True, relation_catalog=catalog,
                )
    return current


def domain_aliases(name):
    """Existing imports used registry names; provisioned sources use the folder."""
    if not name:
        return []
    config = settings.WISSENSWIKI.get("MARKDOWN_DATA", {})
    prefix = config.get("prefix", "")
    managed = ManagedDomain.objects.filter(name=name).first()
    if managed:
        return list(dict.fromkeys([name, managed.folder]))
    source = domain_registry().domains[name].source
    root = Path(config["root"]).expanduser().resolve() if config else None
    if prefix and name.startswith(prefix) and root and source.is_relative_to(root):
        return [name, name.removeprefix(prefix)]
    return [name]


class DomainContextMiddleware(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if not request.user.is_authenticated or request.path.startswith("/health/"):
            return None
        current = domain_registry()
        request.available_domains = list(current.domains)
        selected = ActiveDomain.objects.filter(user=request.user).values_list("name", flat=True).first() or ""
        if selected and selected not in current.domains:
            messages.warning(request, f"Die ausgewählte Domäne {selected} ist nicht mehr verfügbar. Bitte neu wählen.")
            selected = ""
        match = request.resolver_match.view_name
        if match in {
            "content:index", "content:output", "content:documents", "content:inventory",
            "content:files", "content:jobs",
            "content:collections", "content:resources",
            "wissenswiki:graph", "wissenswiki:graph-header", "wissenswiki:settings",
        } and request.GET.get("domain"):
            candidate = request.GET["domain"]
            if candidate not in current.domains:
                prefix = settings.WISSENSWIKI.get("MARKDOWN_DATA", {}).get("prefix", "")
                candidate = prefix + candidate
            if candidate not in current.domains:
                return HttpResponse("Unbekannte Domäne; bitte über die Navigation auswählen.", status=400)
            selected = candidate
            if candidate != request.GET["domain"] and match.startswith("wissenswiki:") and request.method in {"GET", "HEAD"}:
                query = request.GET.copy()
                query["domain"] = candidate
                return redirect(request.path + "?" + query.urlencode())
        request.active_domain = selected
        if selected and match in {
            "wissenswiki:graph", "wissenswiki:graph-header", "wissenswiki:settings",
        } and not request.GET.get("domain") and request.method in {"GET", "HEAD"}:
            query = request.GET.copy()
            query["domain"] = selected
            return redirect(request.path + "?" + query.urlencode())
        return None


class DomainForm(forms.Form):
    folder = forms.RegexField(
        r"^[A-Za-z0-9][A-Za-z0-9_-]{0,99}$", max_length=100, label="Domänenverzeichnis",
        help_text="Buchstaben, Ziffern, Bindestrich oder Unterstrich; unter DATA_DIR/NAME/md.",
        error_messages={"invalid": "Bitte einen einfachen Verzeichnisnamen ohne Pfade oder Sonderzeichen verwenden."},
    )


def create_domain(folder, user):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]{0,99}", folder):
        raise ValueError("Ungültiger Domänenverzeichnisname.")
    config = settings.WISSENSWIKI.get("MARKDOWN_DATA")
    if not config:
        raise ValueError("MARKDOWN_DATA ist nicht konfiguriert; keine Datenwurzel für neue Domänen.")
    name = config.get("prefix", "") + folder
    if len(name) > 150 or name in domain_registry().domains:
        raise ValueError("Domänenname ist zu lang oder bereits vorhanden.")
    subdir = config.get("subdir", "md")
    if not subdir or subdir.startswith(".") or "/" in subdir or "\\" in subdir:
        raise ValueError("MARKDOWN_DATA.subdir muss ein einfacher Verzeichnisname sein.")
    root = Path(config["root"]).expanduser()
    relations_root = Path(config["relations"]).expanduser()
    source_path = (root / folder / subdir).resolve()
    relations_path = (relations_root / folder).resolve()
    if source_path.is_relative_to(relations_path) or relations_path.is_relative_to(source_path):
        raise ValueError("Quellen und Beziehungsverzeichnis müssen getrennt sein.")
    relations_root.mkdir(parents=True, exist_ok=True)
    relations = relations_root / folder
    if relations.exists() or relations.is_symlink():
        raise ValueError("Beziehungsverzeichnis existiert bereits; es wird nicht überschrieben.")
    source = root / folder
    made_source = made_relations = False
    root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    relations_fd = None
    try:
        relations_fd = os.open(relations_root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        with transaction.atomic():
            domain = ManagedDomain.objects.create(name=name, folder=folder, created_by=user)
            os.mkdir(folder, dir_fd=root_fd)
            made_source = True
            folder_fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW, dir_fd=root_fd)
            try:
                os.mkdir(subdir, dir_fd=folder_fd)
            finally:
                os.close(folder_fd)
            os.mkdir(folder, dir_fd=relations_fd)
            made_relations = True
    except (OSError, DatabaseError):
        if made_relations:
            relations.rmdir()
        if made_source:
            if (source / subdir).is_dir():
                (source / subdir).rmdir()
            source.rmdir()
        raise
    finally:
        os.close(root_fd)
        if relations_fd is not None:
            os.close(relations_fd)
    registry.cache_clear()
    return domain


@login_required
def manage_domains(request):
    form = DomainForm(request.POST if request.method == "POST" else None)
    if request.method == "POST":
        if not request.user.is_staff:
            return HttpResponse("Nur Administratoren dürfen Domänen anlegen.", status=403)
        if form.is_valid():
            try:
                created = create_domain(form.cleaned_data["folder"], request.user)
            except (ValueError, OSError, IntegrityError, WorkspaceError) as error:
                form.add_error(None, f"Domäne konnte nicht angelegt werden: {error}")
            else:
                messages.success(request, f"Domäne {created.name} angelegt; noch keine Quellen registriert.")
                return redirect("domains")
        return render(request, "domains.html", {"form": form}, status=400)
    if request.method != "GET":
        return HttpResponse(status=405, headers={"Allow": "GET, POST"})
    return render(request, "domains.html", {"form": form})


@login_required
@require_POST
def select_domain(request):
    name = request.POST.get("domain", "")
    if name and name not in domain_registry().domains:
        return HttpResponse("Unbekannte Domäne; die Auswahl wurde nicht gespeichert.", status=400)
    target = request.POST.get("next", "/content/")
    if not url_has_allowed_host_and_scheme(target, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
        return HttpResponse("Ungültiges Rücksprungziel.", status=400)
    parts = urlsplit(target)
    query = [(key, value) for key, value in parse_qsl(parts.query) if key not in {"domain", "page"}]
    ActiveDomain.objects.update_or_create(user=request.user, defaults={"name": name})
    return redirect(urlunsplit((parts.scheme, parts.netloc, parts.path, urlencode(query), parts.fragment)))
