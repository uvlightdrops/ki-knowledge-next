"""Settings for local development; paths can be overridden with ``KI_NEXT_*`` variables."""

import os
import secrets
from pathlib import Path

from django.utils.csp import CSP

BASE_DIR = Path(__file__).resolve().parent.parent
HOME = Path.home()


def _env_path(name: str, default: Path) -> str:
    return str(Path(os.environ.get(name, default)).expanduser())


VAR_DIR = Path(_env_path("KI_NEXT_VAR", BASE_DIR / "var"))
VAR_DIR.mkdir(parents=True, exist_ok=True)


def _secret_key() -> str:
    path = VAR_DIR / "secret_key"
    if not path.exists():
        path.write_text(secrets.token_urlsafe(50))
        path.chmod(0o600)
    return path.read_text().strip()


SECRET_KEY = _secret_key()
DEBUG = os.environ.get("KI_NEXT_DEBUG", "1") == "1"
ALLOWED_HOSTS = [host for host in os.environ.get("KI_NEXT_ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if host]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "wissenswiki_core",
    "wissenswiki",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

SECURE_CSP = {
    "default-src": [CSP.SELF],
    "object-src": [CSP.NONE],
    "base-uri": [CSP.NONE],
    "frame-ancestors": [CSP.NONE],
}

ROOT_URLCONF = "knext.urls"
WSGI_APPLICATION = "knext.wsgi.application"

TEMPLATES = [{
    "BACKEND": "django.template.backends.django.DjangoTemplates",
    "DIRS": [],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
    ]},
}]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": VAR_DIR / "db.sqlite3"}}

LANGUAGE_CODE = "de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "admin:login"

# Same data as ./start-wiki in ki-knowledge plus its Markdown domains (former --ki-domains).
WISSENSWIKI = {
    "WORKSPACE": _env_path("KI_NEXT_WORKSPACE", HOME / "dev_wiki"),
    "DOMAINS": [{
        "name": "Dokumentation",
        "source": _env_path("KI_NEXT_DOC", BASE_DIR.parent / "ki-knowledge" / "doc"),
        "relations": _env_path("KI_NEXT_DOC_RELATIONS", HOME / "dev_wiki_rel"),
    }],
    "MARKDOWN_DATA": {
        "root": _env_path("KI_NEXT_DATA", HOME / "dev_data" / "ki-knowledge"),
        "relations": _env_path("KI_NEXT_DATA_RELATIONS", HOME / "dev_wiki_rel_ki"),
        "subdir": "md",
        "prefix": "ki:",
        "lenient": True,
    },
}
