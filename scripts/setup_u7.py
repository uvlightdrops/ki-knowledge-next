#!/usr/bin/env python3
"""Prepare and activate a first ki-knowledge-next installation on Uberspace 7."""

from __future__ import annotations

import getpass
import http.client
import json
import os
import re
import secrets
import shutil
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
from collections.abc import Callable
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
SIBLINGS = {
    "stackctl": "https://github.com/uvlightdrops/stackctl.git",
    "yaml_cfg_wizard": "https://github.com/uvlightdrops/yaml-cfg-wizard.git",
    "wissenswiki-core": "https://github.com/uvlightdrops/wissenswiki-core.git",
    "wissenswiki-django": "https://github.com/uvlightdrops/wissenswiki-django.git",
}


class SetupError(Exception):
    """The installation cannot safely proceed."""


class SetupAnswers:
    """Keep non-secret answers as editable defaults across setup attempts."""

    def __init__(self) -> None:
        self.path = ROOT / ".setup-u7-answers.json"
        self.values: dict[str, str] = {}
        if self.path.exists():
            saved = json.loads(self.path.read_text(encoding="utf-8"))
            keys = {"domain", "port", "workspace", "data"}
            if not isinstance(saved, dict) or set(saved) - keys or any(
                not isinstance(value, str) for value in saved.values()
            ):
                raise SetupError(f"Ungültige Eingabedatei: {self.path}")
            self.values = saved
            print(f"Gespeicherte Eingaben als Vorgaben geladen: {self.path}")

    def ask(self, key: str, label: str, default: str,
            validate: Callable[[str], str]) -> str:
        """Validate and persist each answer before the next setup step."""
        default = self.values.get(key, default)
        while True:
            hint = f" [{default}]" if default else ""
            value = input(f"{label}{hint}: ").strip() or default
            try:
                value = validate(value)
            except (SetupError, ValueError) as exc:
                print(f"Ungültige Eingabe: {exc}", file=sys.stderr)
                continue
            self.values[key] = value
            self.save()
            return value

    def save(self) -> None:
        """Atomically replace the private answer file, never credentials."""
        temporary: Path | None = None
        try:
            with tempfile.NamedTemporaryFile(
                mode="w", encoding="utf-8", dir=ROOT,
                prefix=".setup-u7-answers.", suffix=".tmp", delete=False,
            ) as stream:
                temporary = Path(stream.name)
                json.dump(self.values, stream, ensure_ascii=False, indent=2)
            os.replace(temporary, self.path)
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)


def web_port(value: str) -> str:
    """Validate the private web port before remembering it."""
    port = int(value)
    if not 1024 <= port <= 65535:
        raise SetupError("Webport muss zwischen 1024 und 65535 liegen.")
    return str(port)


def run(*command: str, capture: bool = False) -> str:
    """Run a command without invoking a shell."""
    try:
        result = subprocess.run(
            command, cwd=ROOT, check=True, text=True,
            stdout=subprocess.PIPE if capture else None,
        )
    except (OSError, subprocess.CalledProcessError) as exc:
        raise SetupError(f"Befehl fehlgeschlagen: {command[0]} ({exc})") from exc
    return result.stdout if capture else ""


def confirm(message: str) -> None:
    """Require an explicit interactive confirmation."""
    if input(f"{message} [ja/Nein] ").strip().lower() != "ja":
        raise SetupError("Abgebrochen; keine weiteren Schritte ausgeführt.")


def domain_name(value: str) -> str:
    """Validate a concrete ASCII hostname, never a URL or wildcard."""
    value = value.strip().lower()
    labels = value.split(".")
    if len(value) > 253 or len(labels) < 2 or any(
        not re.fullmatch(r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?", label)
        for label in labels
    ):
        raise SetupError("Eine konkrete Domain ohne Schema, Port oder Pfad angeben.")
    return value


def request(domain: str, path: str, *, secure: bool, headers: dict[str, str] | None = None):
    """Perform one request without following redirects or using environment proxies."""
    connection_type = http.client.HTTPSConnection if secure else http.client.HTTPConnection
    connection = connection_type(domain, timeout=15)
    try:
        connection.request("GET", path, headers=headers or {})
        response = connection.getresponse()
        return response.status, dict(response.getheaders()), response.read()
    finally:
        connection.close()


def check_redirect(domain: str, path: str) -> None:
    """Require HTTP requests to redirect to the same HTTPS host and path."""
    status, headers, _ = request(domain, path, secure=False, headers={"X-Forwarded-Proto": "http"})
    location = urlsplit(headers.get("Location", ""))
    if status not in {301, 302, 307, 308} or (
        location.scheme != "https" or location.netloc.lower() != domain or location.path != path
    ):
        raise SetupError("HTTP wird nicht unverändert auf HTTPS derselben Domain umgeleitet.")


def backend_conflicts(domain: str, listing: str) -> bool:
    """Detect existing explicit backends for the domain."""
    return any(
        token == domain or token.startswith(domain + "/")
        for line in listing.splitlines()
        for token in line.split()[:1]
    )


def verify_proxy(domain: str, open_ports: set[int]) -> None:
    """Probe the real proxy with a temporary, narrowly scoped backend."""
    path = "/.well-known/ki-next-probe-" + secrets.token_hex(16)

    class Probe(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            data = json.dumps(self.headers.get_all("X-Forwarded-Proto", [])).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(data)

        def log_message(self, format: str, *args: object) -> None:
            return

    with HTTPServer(("0.0.0.0", 0), Probe) as server:
        port = server.server_address[1]
        if port in open_ports:
            raise SetupError("Der temporäre Prüfport ist öffentlich freigegeben.")
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        route = domain + path
        installed = False
        try:
            listing = run("uberspace", "web", "backend", "list", capture=True)
            if any(line.split()[:1] == [route] for line in listing.splitlines()):
                raise SetupError("Die temporäre Prüfrouting-Adresse existiert bereits.")
            run("uberspace", "web", "backend", "set", route, "--http", "--port", str(port))
            installed = True
            check_redirect(domain, path)
            for spoof in (None, "http", "https, http", "http, https"):
                headers = {} if spoof is None else {"X-Forwarded-Proto": spoof}
                status, _, body = request(domain, path, secure=True, headers=headers)
                if status != 200 or json.loads(body) != ["https"]:
                    raise SetupError(
                        "Der HTTPS-Proxy überschreibt X-Forwarded-Proto nicht zuverlässig; "
                        "keine Aktivierung. Uberspace-Support nach einem sicheren Proxyvertrag fragen."
                    )
        finally:
            try:
                if installed:
                    run("uberspace", "web", "backend", "del", route)
            finally:
                server.shutdown()
                thread.join()


def preflight(domain: str, port: int, static_root: Path, var_root: Path) -> None:
    """Reject existing installations and unverified host settings."""
    if sys.version_info < (3, 12):
        raise SetupError("Python 3.12 oder neuer ist erforderlich.")
    for executable in ("git", "uberspace", "supervisorctl"):
        if not shutil.which(executable):
            raise SetupError(f"{executable} fehlt; bitte auf dem U7-Host ausführen.")
    if any(name.startswith(("KI_CFG_", "KI_NEXT_")) or name in {"KI_STAGE", "KI_PROFILE"} for name in os.environ):
        raise SetupError("KI_CFG_*/KI_NEXT_*/KI_STAGE/KI_PROFILE vor der Einrichtung aus der Umgebung entfernen.")
    for path in (ROOT / ".venv", ROOT / "ki.yaml", ROOT / "creds.yaml", var_root, static_root):
        if path.exists() or path.is_symlink():
            raise SetupError(f"Ersteinrichtung überschreibt keinen vorhandenen Pfad: {path}")
    for path in (ROOT / "config/runtime/runtime.yaml", ROOT / "config/stages/.active_stage",
                 ROOT / "config/profiles/.active_profile"):
        if path.exists() or path.is_symlink():
            raise SetupError(f"Vorhandener Konfigurationslayer: {path}")
    listing = run("uberspace", "web", "backend", "list", capture=True)
    print(listing)
    if backend_conflicts(domain, listing):
        raise SetupError("Für diese Domain existiert bereits ein explizites Backend; eigene Domain verwenden.")
    port_lines = [line.strip() for line in run("uberspace", "port", "list", capture=True).splitlines() if line.strip()]
    if any(not line.isdigit() or not 1 <= int(line) <= 65535 for line in port_lines):
        raise SetupError("Unerwartete Ausgabe von uberspace port list; offene Ports manuell prüfen.")
    open_ports = {int(line) for line in port_lines}
    if port in open_ports:
        raise SetupError("Der Webport ist öffentlich freigegeben; einen privaten Port wählen.")
    with socket.socket() as test_socket:
        try:
            test_socket.bind(("0.0.0.0", port))
        except OSError as exc:
            raise SetupError(f"Webport {port} ist nicht verfügbar.") from exc
    confirm("Temporäres Prüfbackend auf der gewählten Domain einrichten und danach entfernen?")
    verify_proxy(domain, open_ports)


def install_packages() -> Path:
    """Create the project venv and install project and sibling checkouts."""
    for directory, url in SIBLINGS.items():
        path = ROOT.parent / directory
        if not path.exists():
            run("git", "clone", "--", url, str(path))
        elif not (path / ".git").exists():
            raise SetupError(f"Vorhandener Geschwisterpfad ist kein Git-Checkout: {path}")
    run(sys.executable, "-m", "venv", str(ROOT / ".venv"))
    python = ROOT / ".venv/bin/python"
    packages = [item for name in SIBLINGS for item in ("-e", str(ROOT.parent / name))]
    run(str(python), "-m", "pip", "install", *packages, "-e", f"{ROOT}[deploy]")
    run(str(python), "-m", "pip", "check")
    run(str(python), "-c",
        "from stackctl.spec import Service; assert 'stop_timeout' in Service.__dataclass_fields__, "
        "'stackctl mit stop_timeout erforderlich'")
    return python


def write_private(path: Path, contents: str) -> None:
    """Create a private file exclusively without overwriting existing data."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(contents)


def write_config(domain: str, port: int, static_root: Path, var_root: Path,
                 workspace: Path, data: Path) -> None:
    """Write the first-install configuration and independent secret."""
    home = Path.home()
    quote = json.dumps
    config = f"""apps:
  ki_knowledge_next:
    paths:
      var: {quote(str(var_root))}
      workspace: {quote(str(workspace))}
      data: {quote(str(data))}
      data_relations: {quote(str(home / 'ki/relations/data'))}
      document_relations: {quote(str(home / 'ki/relations/documentation'))}
    django:
      debug: false
      allowed_hosts: [{quote(domain)}, "127.0.0.1"]
      static_root: {quote(str(static_root))}
      https_proxy: true
stack:
  target: supervisord
  services:
    django:
      host: "0.0.0.0"
      port: {port}
      command: ["{{python}}", "-m", "gunicorn", "knext.wsgi:application", "--bind", "{{host}}:{{port}}", "--workers", "1", "--threads", "2", "--timeout", "120"]
    import-worker:
      stop_timeout: 300
"""
    write_private(ROOT / "ki.yaml", config)
    write_private(ROOT / "creds.yaml", f"apps:\n  ki_knowledge_next:\n    django:\n"
                  f"      secret_key: {quote(secrets.token_urlsafe(64))}\n")


def activate(python: Path, domain: str, port: int) -> None:
    """Start the two services and, after confirmation, assign the domain."""
    run(str(python), "-m", "stackctl", "start")
    run(str(python), "-m", "stackctl", "status")
    print(run("uberspace", "web", "backend", "list", capture=True))
    confirm(f"Domain {domain} auf Next umstellen und /static an Apache übergeben?")
    if backend_conflicts(domain, run("uberspace", "web", "backend", "list", capture=True)):
        raise SetupError("Routing hat sich geändert; keine Domainzuordnung vorgenommen.")
    run("uberspace", "web", "backend", "set", domain + "/static", "--apache")
    run("uberspace", "web", "backend", "set", domain, "--http", "--port", str(port))
    status, _, body = request(domain, "/health/ready/", secure=True)
    if status != 200 or json.loads(body) != {"status": "ready"}:
        raise SetupError("HTTPS-Readiness fehlgeschlagen; Routing und Dienste manuell prüfen.")
    print("Einrichtung abgeschlossen. Anmeldung, Staticfiles und Importjob auf dem Host prüfen.")


def check_deploy(python: Path) -> None:
    """Allow only the two intentionally unused HSTS preload recommendations."""
    command = [str(python), "manage.py", "check", "--deploy", "--fail-level", "WARNING"]
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    output = result.stdout + result.stderr
    print(output, end="")
    checks = set(re.findall(r"(?m)^.*\(([a-zA-Z0-9_.]+)\)", output))
    allowed = {"security.W005", "security.W021"}
    if result.returncode and not (result.returncode == 1 and checks and checks <= allowed):
        raise SetupError("Django-Deployprüfung fehlgeschlagen; gemeldete Prüfungen beheben.")
    if checks & allowed:
        print("HSTS-Subdomains und Preload bleiben bewusst deaktiviert; eigene Domains separat prüfen.")


def main() -> int:
    """Run the interactive first installation."""
    os.umask(0o077)
    try:
        answers = SetupAnswers()
        domain = answers.ask("domain", "Bereits eingerichtete eigene U7-Domain", "", domain_name)
        port = int(answers.ask("port", "Privater Webport", "8780", web_port))
        account = getpass.getuser()
        public_base = Path("/var/www/virtual") / account
        document_root = public_base / domain
        if not document_root.is_dir() or not document_root.resolve().is_relative_to(public_base.resolve()):
            raise SetupError(f"Domain-DocumentRoot fehlt oder zeigt nach außen: {document_root}")
        static_root = document_root / "static"
        var_root = Path.home() / "ki/var/ki-knowledge-next"
        workspace = Path(answers.ask(
            "workspace", "Wiki-Arbeitsverzeichnis", str(Path.home() / "ki/wiki"), private_path,
        ))
        data = Path(answers.ask(
            "data", "Datenverzeichnis", str(Path.home() / "ki/data"), private_path,
        ))
        preflight(domain, port, static_root, var_root)
        for directory in (workspace, data):
            if not directory.exists():
                confirm(f"Neues leeres Verzeichnis {directory} anlegen?")
                directory.mkdir(mode=0o700, parents=True)
        python = install_packages()
        write_config(domain, port, static_root, var_root, workspace, data)
        run(str(python), "-m", "knext.config")
        check_deploy(python)
        run(str(python), "manage.py", "migrate", "--noinput")
        old_umask = os.umask(0o022)
        try:
            run(str(python), "manage.py", "collectstatic", "--noinput")
        finally:
            os.umask(old_umask)
        run(str(python), "manage.py", "createsuperuser")
        activate(python, domain, port)
        return 0
    except (KeyboardInterrupt, EOFError):
        print("\nU7-Einrichtung abgebrochen; gültige Eingaben bleiben gespeichert.", file=sys.stderr)
        return 1
    except (SetupError, OSError, ValueError, http.client.HTTPException, ssl.SSLError) as exc:
        print(f"U7-Einrichtung fehlgeschlagen: {exc}", file=sys.stderr)
        print("Vorhandene Teilstände prüfen; kein automatischer Rollback.", file=sys.stderr)
        print("Gespeicherte Eingaben werden beim nächsten Start als Vorgaben angeboten.", file=sys.stderr)
        return 1


def private_path(value: str) -> str:
    """Validate a private data root without replacing existing content."""
    path = Path(value).expanduser()
    if not path.is_absolute() or not path.resolve().is_relative_to(Path.home().resolve()):
        raise SetupError("Ein absoluter Pfad innerhalb des Home-Verzeichnisses ist erforderlich.")
    if path.exists() and not path.is_dir():
        raise SetupError(f"Kein Verzeichnis: {path}")
    return str(path)


if __name__ == "__main__":
    raise SystemExit(main())
