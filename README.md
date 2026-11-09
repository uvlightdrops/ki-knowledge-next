---
project: ki-knowledge-next
scope: Einrichtung und Start des neuen Django-Projekts
created: null
updated: "2026-11-09 09"
update_reason: Erste Fassung
status: draft
agent_project: ki-knowledge
---

# ki-knowledge-next

Ein frisches Django-Projekt (Arbeitstitel), in dem ki-knowledge neu aufgebaut wird.
Die Wiki-Funktionen kommen als App aus `../wissenswiki-django`.
Konzept: `../ki-knowledge/doc/architecture/WEITERENTWICKLUNG.md`, Abschnitt `fresh-django`.

## Einrichtung [setup]

```bash
python3 -m venv .venv
.venv/bin/pip install -e ../wissenswiki-core -e '../wissenswiki-django[test]' -e '.[test]'
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
./start                      # http://127.0.0.1:8780/
```

`./start 0.0.0.0:8780` macht das Projekt im LAN erreichbar; dazu `KI_NEXT_ALLOWED_HOSTS` um die IP ergänzen.

## Konfiguration [configuration]

| Variable | Standard |
|----------|----------|
| `KI_NEXT_WORKSPACE` | `~/dev_wiki` |
| `KI_NEXT_DOC` / `KI_NEXT_DOC_RELATIONS` | `../ki-knowledge/doc` / `~/dev_wiki_rel` |
| `KI_NEXT_DATA` / `KI_NEXT_DATA_RELATIONS` | `~/dev_data/ki-knowledge` / `~/dev_wiki_rel_ki` |
| `KI_NEXT_VAR` | `var/` (Datenbank, Secret Key) |
| `KI_NEXT_DEBUG`, `KI_NEXT_ALLOWED_HOSTS` | `1`, `localhost,127.0.0.1` |

Die Markdown-Domänen von ki-knowledge erscheinen mit dem Präfix `ki:`.
Die Seiten werden mit einer strengen Content-Security-Policy ausgeliefert.

## Tests [tests]

```bash
.venv/bin/python -m pytest -q
```
