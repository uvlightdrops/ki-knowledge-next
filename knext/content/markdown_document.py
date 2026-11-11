"""Separate YAML document metadata from editor text without rewriting the header."""

import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any

import yaml

from .importers.base import ImportFailure


class _HeaderLoader(yaml.SafeLoader):
    def construct_mapping(self, node, deep=False):
        pairs = self.construct_pairs(node, deep=deep)
        result = {}
        for key, value in pairs:
            if not isinstance(key, str) or key in result:
                raise ImportFailure("YAML-Header braucht eindeutige Textschlüssel.")
            result[key] = value
        return result


@dataclass(frozen=True)
class MarkdownDocument:
    body: str
    header: str = ""
    frontmatter: dict[str, Any] | None = None


def _json_value(value: Any, depth: int = 0, budget: list[int] | None = None) -> Any:
    budget = budget if budget is not None else [10_000]
    budget[0] -= 1
    if budget[0] < 0:
        raise ImportFailure("YAML-Header enthält zu viele Werte oder Alias-Erweiterungen.")
    if depth > 30:
        raise ImportFailure("YAML-Header ist zu tief verschachtelt oder enthält zyklische Referenzen.")
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise ImportFailure("YAML-Header braucht Textschlüssel.")
        return {key: _json_value(item, depth + 1, budget) for key, item in value.items()}
    if isinstance(value, list):
        return [_json_value(item, depth + 1, budget) for item in value]
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if value is None or isinstance(value, (str, bool, int, float)):
        return value
    raise ImportFailure("YAML-Header enthält einen nicht unterstützten Datentyp.")


def split_markdown(text: str) -> MarkdownDocument:
    """Keep the original header including comments and delimiters, with a JSON-safe view."""
    if not re.match(r"\A---[ \t]*(?:\r?\n|$)", text):
        return MarkdownDocument(text, frontmatter={})
    match = re.match(r"\A---[ \t]*\r?\n(.*?)^(?:---|\.\.\.)[ \t]*(?:\r?\n|$)", text, re.S | re.M)
    if not match:
        raise ImportFailure("YAML-Header ist nicht mit --- oder ... abgeschlossen.")
    if len(match.group(1).encode("utf-8")) > 128 * 1024:
        raise ImportFailure("YAML-Header überschreitet 128 KiB.")
    try:
        parsed = yaml.load(match.group(1), Loader=_HeaderLoader)
        if parsed is None:
            parsed = {}
        if not isinstance(parsed, dict):
            raise ImportFailure("Der YAML-Header muss ein Mapping sein.")
        parsed = _json_value(parsed)
        json.dumps(parsed, allow_nan=False)
    except ImportFailure:
        raise
    except (yaml.YAMLError, ValueError, TypeError, RecursionError) as error:
        raise ImportFailure("Ungültiger YAML-Header; bitte Struktur und Werte prüfen.") from error
    return MarkdownDocument(text[match.end():], text[:match.end()], parsed)


def revision_digest(title: str, body: str, header: str, metadata: dict) -> str:
    """Hash the versioned content, original header and extraction provenance."""
    value = json.dumps(
        {"title": title, "body": body, "header": header, "metadata": metadata},
        ensure_ascii=False, sort_keys=True, allow_nan=False, separators=(",", ":"),
    )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()
