---
project: ki-knowledge-next
scope: Einrichtung und Start des neuen Django-Projekts
created: null
updated: "2026-11-10 15"
update_reason: Gemeinsames Hauptmenü für Import, Wiki und Administration dokumentiert
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

Nach Anmeldung ist der Import-Prototyp unter `/content/` erreichbar; das
Wissensnetz bleibt unter `/wiki/graph-header/`. Bei einer bereits laufenden
Instanz ohne Autoreload den Prozess nach Installation und Migration neu starten.
Ein gemeinsames Burgermenü links oben verbindet Import, Wissensnetz,
Arbeitsraum und Netz-Einstellungen; für Staff-Nutzer auch die Administration.
Die Domänenleiste bleibt separat, die aktuelle Domäne wird beim Wechsel
zwischen Netz und Netz-Einstellungen mitgenommen. Escape oder ein Klick
außerhalb schließt das Menü. Statische HTML-Ausgaben enthalten dieses
interne App-Menü nicht.
Die Originaldateien und Revisionen des Prototyps liegen in der SQLite-Datenbank
unter `var/`, getrennt von den Markdown-Domänen.

Uploads unterstützen Markdown, UTF-8-Text, HTML, CSV/TSV, JSON/YAML, PDF mit
Textebene, DOCX, XLSX und EPUB. Der Ablauf führt über Entwurf und explizite
Freigabe zum einzelnen HTML-Dokument oder zum ZIP einer statischen Domänen-Site.
Zur Freigabe ist `content.publish_content` nötig; Superuser besitzen diese
Berechtigung bereits. Alle angemeldeten Nutzer teilen im Prototyp die
Inhalte, daher noch nicht für einen mandantengetrennten Betrieb verwenden.
Formatgrenzen, Datenmodell und offene Ausbaustufen stehen im
[Importkonzept](doc/features/IMPORT-PIPELINES-AND-DRAFTS.md#import-prototyp-import-prototype).

## Konfiguration [configuration]

| Variable | Standard |
|----------|----------|
| `KI_NEXT_WORKSPACE` | `~/dev_wiki` |
| `KI_NEXT_DOC` / `KI_NEXT_DOC_RELATIONS` | `doc/` / `var/doc-relations/` |
| `KI_NEXT_DATA` / `KI_NEXT_DATA_RELATIONS` | `~/dev_data/ki-knowledge` / `~/dev_wiki_rel_ki` |
| `KI_NEXT_VAR` | `var/` (Datenbank, Secret Key) |
| `KI_NEXT_DEBUG`, `KI_NEXT_ALLOWED_HOSTS` | `1`, `localhost,127.0.0.1` |

Die Markdown-Domänen von ki-knowledge erscheinen mit dem Präfix `ki:`.
Die Seiten werden mit einer strengen Content-Security-Policy ausgeliefert.
Die Domäne „Dokumentation“ liest standardmäßig Markdown-Dateien aus dem
Verzeichnis `doc/` dieses Repositories und speichert Domänenbeziehungen
getrennt unter `var/doc-relations/`. Konzeptänderungen erscheinen nach dem
Speichern in der Site; `KI_NEXT_DOC` und `KI_NEXT_DOC_RELATIONS` können beide
Pfade weiterhin überschreiben.

## Tests [tests]

```bash
.venv/bin/python -m pytest -q
node --test tests/navigation.test.cjs
```
