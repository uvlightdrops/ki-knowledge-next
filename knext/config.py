"""Project-local YAML resolution shared by Django and stackctl."""

import os
import re
import warnings
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft7Validator
from ki_core.schema_manager import get_schema_path
from wissenswiki_core.relations import build_catalog
from yaml_cfg_wizard import ConfigResolver
from yaml_cfg_wizard.core import (
    load_yaml_file,
    merge_with_replacement,
    strip_replace_markers,
)
from yaml_cfg_wizard.schema_utils import scaffold_skeleton_from_schema

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCHEMA_FILE = Path(__file__).resolve().parent / "schema" / "next.schema.yaml"
APP = "ki_knowledge_next"
LEGACY_PATHS = {
    "KI_NEXT_VAR": "var",
    "KI_NEXT_WORKSPACE": "workspace",
    "KI_NEXT_DOC": "documentation",
    "KI_NEXT_DOC_RELATIONS": "document_relations",
    "KI_NEXT_DATA": "data",
    "KI_NEXT_DATA_RELATIONS": "data_relations",
}


class ConfigurationError(ValueError):
    """Configuration cannot be used; messages never include setting values."""


def _selected_layer(root: Path, group: str, variable: str) -> list[Path]:
    directory = root / "config" / group
    marker = directory / f".active_{group[:-1]}"
    name = os.environ.get(variable, "").strip()
    if not name and marker.is_file():
        name = marker.read_text(encoding="utf-8").strip()
    if not name:
        return []
    if not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]*", name):
        raise ConfigurationError(f"{variable}: ungueltiger Layername; nur Buchstaben, Ziffern, _ und -.")
    for suffix in (".yaml", ".yml"):
        candidate = directory / f"{name}{suffix}"
        if candidate.is_file():
            return [candidate]
    raise ConfigurationError(f"{variable}: ausgewaehlter Layer fehlt in {directory}.")


def _legacy_overrides() -> dict[str, Any]:
    values: dict[str, Any] = {"paths": {}, "django": {}}
    for variable, field in LEGACY_PATHS.items():
        if variable in os.environ:
            values["paths"][field] = os.environ[variable]
    if "KI_NEXT_DEBUG" in os.environ:
        if os.environ["KI_NEXT_DEBUG"] not in {"0", "1"}:
            raise ConfigurationError("KI_NEXT_DEBUG muss 0 oder 1 sein; alternativ YAML django.debug verwenden.")
        values["django"]["debug"] = os.environ["KI_NEXT_DEBUG"] == "1"
    if "KI_NEXT_ALLOWED_HOSTS" in os.environ:
        values["django"]["allowed_hosts"] = [
            host.strip() for host in os.environ["KI_NEXT_ALLOWED_HOSTS"].split(",") if host.strip()
        ]
    used = [name for name in (*LEGACY_PATHS, "KI_NEXT_DEBUG", "KI_NEXT_ALLOWED_HOSTS") if name in os.environ]
    if used:
        warnings.warn(
            "KI_NEXT_* ist veraltet; Werte in YAML oder KI_CFG_APPS__KI_KNOWLEDGE_NEXT__... uebertragen.",
            FutureWarning, stacklevel=3,
        )
    return {"apps": {APP: values}}


class _Resolver(ConfigResolver):
    def _runtime_layers(self) -> list[dict[str, Any]]:
        return [*super()._runtime_layers(), _legacy_overrides()]


def _check_yaml_files(root: Path, selected: list[Path]) -> None:
    files = [
        root / "ki.yaml", root / "creds.yaml",
        root / "config" / "runtime" / "runtime.yaml", *selected,
    ]
    defaults = root / "config" / "defaults"
    files.extend([*defaults.glob("*.yaml"), *defaults.glob("*.yml")])
    for path in files:
        if path.exists():
            value = yaml.safe_load(path.read_text(encoding="utf-8"))
            if value is not None and not isinstance(value, dict):
                raise ConfigurationError(f"YAML-Wurzel muss ein Mapping sein: {path}")


def _validate(payload: dict[str, Any], schema: dict[str, Any]) -> None:
    error = next(Draft7Validator(schema).iter_errors(payload), None)
    if error is not None:
        path = ".".join(str(part) for part in error.absolute_path) or "<root>"
        raise ConfigurationError(
            f"Konfiguration bei {path}: Schema-Regel {error.validator} verletzt. YAML und KI_CFG_* pruefen."
        )
    django = payload["apps"][APP]["django"]
    try:
        build_catalog(payload["apps"][APP]["relation_catalog"])
    except ValueError as error:
        raise ConfigurationError(f"Relationenkatalog: {error}") from error
    if not django["debug"] and not django["secret_key"].strip():
        raise ConfigurationError(
            "Bei debug=false muss apps.ki_knowledge_next.django.secret_key explizit gesetzt sein "
            "(creds.yaml oder KI_CFG_*)."
        )


def load_config(root: Path | None = None) -> dict[str, Any]:
    """Resolve only this project's files; credentials override environment values."""
    root = (root or PROJECT_ROOT).resolve()
    try:
        schema = load_yaml_file(SCHEMA_FILE)
        if not schema:
            raise ConfigurationError(f"Konfigurationsschema fehlt: {SCHEMA_FILE}")
        shared = load_yaml_file(get_schema_path())
        for key in ("llm", "http"):
            schema["properties"][key] = shared["properties"][key]
        schema["properties"]["llm"]["properties"]["provider"]["default"] = "openai"
        for provider in ("openai", "ki"):
            schema["properties"]["llm"]["properties"]["providers"]["properties"][provider]["properties"]["api_key"].update(
                {"writeOnly": True, "x-secret": True},
            )
        profiles = _selected_layer(root, "profiles", "KI_PROFILE")
        stages = _selected_layer(root, "stages", "KI_STAGE")
        _check_yaml_files(root, [*profiles, *stages])
        resolver = _Resolver(
            defaults=[root / "ki.yaml"],
            defaults_dir=root / "config" / "defaults",
            profiles=profiles,
            stage=stages,
            runtime_file=root / "config" / "runtime" / "runtime.yaml",
            env_prefix="KI_CFG_",
            replace_sections=True,
        )
        payload = merge_with_replacement(
            scaffold_skeleton_from_schema(schema),
            resolver.resolve(preserve_replace_markers=True),
        )
        payload = strip_replace_markers(merge_with_replacement(payload, load_yaml_file(root / "creds.yaml")))
    except yaml.YAMLError:
        raise ConfigurationError(f"Ungueltiges YAML unter {root}; Konfigurationsdateien pruefen.") from None
    except OSError:
        raise ConfigurationError(f"Konfiguration unter {root} nicht lesbar; Dateirechte pruefen.") from None
    except ValueError as exc:
        if isinstance(exc, ConfigurationError):
            raise
        raise ConfigurationError(f"Ungueltige Konfigurationsstruktur unter {root}; YAML und KI_CFG_* pruefen.") from None
    _validate(payload, schema)
    return payload


def resolve_path(value: str, root: Path = PROJECT_ROOT) -> Path:
    """Interpret relative paths against the project, never the caller's cwd."""
    path = Path(value).expanduser()
    return path if path.is_absolute() else root / path


def main() -> int:
    """Validate configuration without printing credentials or resolved values."""
    try:
        load_config()
    except ConfigurationError as exc:
        print(f"Konfiguration ungueltig: {exc}")
        return 1
    print("Konfiguration gueltig. Werte und Zugangsdaten werden nicht ausgegeben.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
