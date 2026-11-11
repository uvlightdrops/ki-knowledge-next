---
project: ki-knowledge-next
scope: Einrichtung und Start des neuen Django-Projekts
created: null
updated: "2026-11-11 22"
update_reason: Gemeinsamen lokalen Start von Webserver und Importworker beschrieben
status: draft
agent_project: ki-knowledge
relations:
  - target: "doc/README.md"
    type: child
    reason: "Produktkonzepte und Featurebeschreibungen"
  - target: "doc/architecture/QUELLEN-UND-TEXTWERKSTATT.md"
    type: reference
    reason: "Quellenregistrierung, immutable Extraktion und Revisionsworkflow"
---

# ki-knowledge-next

Ein frisches Django-Projekt (Arbeitstitel), in dem ki-knowledge neu aufgebaut wird.
Die Wiki-Funktionen kommen als App aus `../wissenswiki-django`.
Konzept: `../ki-knowledge/doc/architecture/WEITERENTWICKLUNG.md`, Abschnitt `fresh-django`.

## Einrichtung [setup]

```yaml block-meta
updated: "2026-11-11 22"
status: active
relations: []
```

```bash
python3 -m venv .venv
.venv/bin/pip install -e ../yaml_cfg_wizard -e ../stackctl -e ../wissenswiki-core -e '../wissenswiki-django[test]' -e '.[test,deploy]'
.venv/bin/python manage.py migrate
.venv/bin/python manage.py createsuperuser
./start                      # http://127.0.0.1:8780/
```

`./start` betreibt Webserver und separaten Importworker gemeinsam; Strg+C
stoppt beide. Bei direktem IDE-/Django-Start zusätzlich
`.venv/bin/python manage.py content_worker` ausführen. Job- und Batchseiten
zeigen Workerstatus und aktualisieren den Fortschritt automatisch.

`./start --lan 192.168.1.20` macht das Projekt unter
`http://192.168.1.20:8780/` im vertrauenswürdigen LAN erreichbar; die IP durch
die LAN-Adresse dieses Rechners ersetzen. Der Modus lauscht auf `0.0.0.0`
und ergänzt die konkrete IP sowie localhost in der Hostfreigabe nur für
diesen Start. Kein Wildcard-Host, keine Änderung an Konfigurationsdateien.
Firewall und WLAN-Clientisolation können den Zugriff weiterhin verhindern.
Der Entwicklerserver ist nicht für Internetzugriff geeignet.

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

Die Quellenansicht `/content/sources/` zeigt Dateien unter
`paths.data/DOMAIN/FILEFORMAT/DATEI` zunächst nur als bereitgestellt.
Registrierung speichert die Originalbytes unveränderlich; erst „In Markdown
zerlegen“ erzeugt einen Extraktionssnapshot und den Ausgangsentwurf.
Die Textwerkstatt bearbeitet ausschließlich den Text, nicht den separat
erhaltenen YAML-Header. Speichern und Wiederherstellen erzeugen neue,
verkettete Revisionen; die Freigabe bleibt an ihren konkreten Stand gebunden.
Historische Fassungen, Vorgängervergleich und Markdown-Downloads sind
verfügbar. Modell und Grenzen:
[Quellen und Textwerkstatt](doc/architecture/QUELLEN-UND-TEXTWERKSTATT.md).
Vor der ersten Migration bestehender Daten eine SQLite-Sicherung erstellen;
`content.0004` ergänzt die Herkunft vorhandener Revisionen und ist nicht
automatisch rückgängig ausführbar.

Dateibestandsimporte unterstützen Markdown, UTF-8-Text, HTML, CSV/TSV, JSON/YAML, PDF mit
Textebene, DOCX, XLSX und EPUB. Dateien werden über die Batch-Auswahl unter
`/content/sources/` für Importjobs eingereiht; es gibt keinen Browser-Einzelupload.
Der Ablauf führt über Entwurf und explizite
Freigabe zum einzelnen HTML-Dokument oder zum ZIP einer statischen Domänen-Site
unter `/content/output/`.
Zur Freigabe ist `content.publish_content` nötig; Superuser besitzen diese
Berechtigung bereits. Alle angemeldeten Nutzer teilen im Prototyp die
Inhalte, daher noch nicht für einen mandantengetrennten Betrieb verwenden.
Formatgrenzen, Datenmodell und offene Ausbaustufen stehen im
[Importkonzept](doc/features/IMPORT-PIPELINES-AND-DRAFTS.md#import-prototyp-import-prototype).

## Konfiguration [configuration]

Django und `stackctl` verwenden jetzt denselben Loader `knext.config.load_config`
auf Basis von `yaml-cfg-wizard`. Das paketierte Schema
`knext/schema/next.schema.yaml` definiert die Appfelder und ihre Defaults.
Unbekannte Felder und ungültige Typen führen zu einem expliziten Fehler.
Der erste Schritt umfasst Host-Settings und den lokalen Django-Dienst;
KI-Schema und Web-Konfigurationseditor sind noch nicht angeschlossen.

Priorität von niedrig nach hoch:
Schema-Defaults → `config/defaults/*.yaml` → `ki.yaml` →
ausgewähltes Profile → ausgewählte Stage → `config/runtime/runtime.yaml` →
bisherige `KI_NEXT_*` → `KI_CFG_*` → projektlokale `creds.yaml`.
Es werden keine Konfigurationen aus Nachbarprojekten oder `~/.config/ki`
eingelesen. Relative Datenpfade beziehen sich auf dieses Repository,
nicht auf das Arbeitsverzeichnis des aufrufenden Prozesses.

Eine optionale lokale `ki.yaml` kann beispielsweise so aussehen:

```yaml
apps:
  ki_knowledge_next:
    django:
      allowed_hosts: [localhost, "127.0.0.1", "192.168.1.20"]
stack:
  services:
    django:
      port: 8780
```

Stage und Profile werden über `KI_STAGE` / `KI_PROFILE` oder die lokalen
Marker `config/stages/.active_stage` / `config/profiles/.active_profile`
gewählt. Ohne Auswahl wird kein solcher Layer geladen.
`KI_STAGE=dev-local` aktiviert die mitgelieferte lokale Stage.
Eine ausdrücklich gewählte, fehlende Stage ist ein Fehler.

```bash
.venv/bin/python -m knext.config       # validiert, ohne Werte/Secrets auszugeben
.venv/bin/python -m stackctl spec      # aufgelöster Dienstplan, keine Dienste starten
.venv/bin/python -m stackctl run django
```

`stackctl run django` läuft im Vordergrund, ohne automatische Migrationen.
Vor dem ersten Start `manage.py migrate` ausführen. Der Readiness-Endpunkt
`/health/ready/` ist ohne Anmeldung erreichbar und liefert erst dann HTTP 200,
wenn die Datenbank erreichbar ist und keine Migrationen ausstehen; sonst
HTTP 503 ohne interne Details. Die Prüfung umfasst noch keine externen
Markdown-Quellen oder zukünftigen KI-Dienste.
`./start [adresse:port]` und der IDE-Start funktionieren weiterhin wie zuvor;
`./start` führt weiterhin die Migrationen aus und nutzt seinen eigenen
Adressparameter, nicht den Stack-Port.

| YAML-Feld unter `apps.ki_knowledge_next` | Bisherige Variable | Standard |
|---|---|---|
| `paths.workspace` | `KI_NEXT_WORKSPACE` | `~/dev_wiki` |
| `paths.documentation` / `paths.document_relations` | `KI_NEXT_DOC` / `KI_NEXT_DOC_RELATIONS` | `doc/` / unter `paths.var`: `doc-relations/` |
| `paths.data` / `paths.data_relations` | `KI_NEXT_DATA` / `KI_NEXT_DATA_RELATIONS` | `~/dev_data/ki-knowledge` / `~/dev_wiki_rel_ki` |
| `paths.var` | `KI_NEXT_VAR` | `var/` mit Datenbank und lokalem Secret Key |
| `django.debug` / `django.allowed_hosts` | `KI_NEXT_DEBUG` / `KI_NEXT_ALLOWED_HOSTS` | `true` / `[localhost, "127.0.0.1"]` |
| `django.static_root` | — | unter `paths.var`: `static/` |

Die bisherigen Variablen funktionieren mit einer Übergangswarnung.
Neue skalare Overrides können etwa
`KI_CFG_STACK__SERVICES__DJANGO__PORT=8782` oder
`KI_CFG_APPS__KI_KNOWLEDGE_NEXT__DJANGO__DEBUG=true` verwenden.
Listen wie `allowed_hosts` in YAML setzen.

`ki.yaml`, Runtime-Layer, Marker und `creds.yaml` sind Git-ignoriert.
Geheime Werte gehören in `creds.yaml`, zum Beispiel unter
`apps.ki_knowledge_next.django.secret_key`; keine aufgelöste
Gesamtkonfiguration veröffentlichen. Im lokalen Debugbetrieb wird der
bisherige Schlüssel unter `var/secret_key` weiterverwendet.
Bei `debug: false` ist jetzt ein expliziter Secret Key erforderlich; ein
automatisch erzeugter Entwicklungsschlüssel wird dafür nicht akzeptiert.
Das lokale Stackprofil ist **kein Produktionsdeployment**: Produktionsserver,
TLS-/Proxy-Settings, Backups und Restore folgen als eigener Schritt.

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
