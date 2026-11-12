"""Django settings backed by the project's validated YAML configuration."""

import secrets

from django.utils.csp import CSP

from .config import APP, PROJECT_ROOT, load_config, resolve_path

BASE_DIR = PROJECT_ROOT
CONFIG = load_config()
APP_CONFIG = CONFIG["apps"][APP]
PATHS = APP_CONFIG["paths"]
DJANGO_CONFIG = APP_CONFIG["django"]

VAR_DIR = resolve_path(PATHS["var"])
VAR_DIR.mkdir(parents=True, exist_ok=True)

DOC_RELATIONS_DIR = (
    resolve_path(PATHS["document_relations"]) if PATHS["document_relations"] else VAR_DIR / "doc-relations"
)
if not PATHS["document_relations"]:
    DOC_RELATIONS_DIR.mkdir(parents=True, exist_ok=True)


def _secret_key() -> str:
    path = VAR_DIR / "secret_key"
    if not path.exists():
        path.write_text(secrets.token_urlsafe(50))
        path.chmod(0o600)
    return path.read_text().strip()


SECRET_KEY = DJANGO_CONFIG["secret_key"] or _secret_key()
DEBUG = DJANGO_CONFIG["debug"]
ALLOWED_HOSTS = DJANGO_CONFIG["allowed_hosts"]
if DJANGO_CONFIG["https_proxy"]:
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
    SECURE_SSL_REDIRECT = True
    SECURE_REDIRECT_EXEMPT = [r"^health/ready/$"]
    SECURE_HSTS_SECONDS = 31536000
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "wissenswiki_core",
    "wissenswiki",
    "knext.content",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.csp.ContentSecurityPolicyMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "knext.domains.DomainContextMiddleware",
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
    "DIRS": [BASE_DIR / "knext" / "templates"],
    "APP_DIRS": True,
    "OPTIONS": {"context_processors": [
        "django.template.context_processors.request",
        "django.contrib.auth.context_processors.auth",
        "django.contrib.messages.context_processors.messages",
        "knext.navigation.navigation",
    ]},
}]

DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": VAR_DIR / "db.sqlite3"}}

LANGUAGE_CODE = "de"
TIME_ZONE = "Europe/Berlin"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = (
    resolve_path(DJANGO_CONFIG["static_root"]) if DJANGO_CONFIG["static_root"] else VAR_DIR / "static"
)
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
LOGIN_URL = "admin:login"
WISSENSWIKI_NAVIGATION_TEMPLATE = "navigation.html"

# Same data as ./start-wiki in ki-knowledge plus its Markdown domains (former --ki-domains).
WISSENSWIKI = {
    "RELATION_CATALOG": APP_CONFIG["relation_catalog"],
    "WORKSPACE": str(resolve_path(PATHS["workspace"])),
    "DOMAINS": [{
        "name": "Dokumentation",
        "source": str(resolve_path(PATHS["documentation"])),
        "relations": str(DOC_RELATIONS_DIR),
    }],
    "MARKDOWN_DATA": {
        "root": str(resolve_path(PATHS["data"])),
        "relations": str(resolve_path(PATHS["data_relations"])),
        "subdir": "md",
        "prefix": "ki:",
        "lenient": True,
    },
}
