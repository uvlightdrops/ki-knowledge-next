---
title: "Import und Jobs"
project: ki-knowledge-next
scope: features
purpose: "Beschreibt Batchimport, Ablage, Jobfortschritt und Workerbedienung."
created: "2026-11-11 06"
updated: "2026-11-11 23"
update_reason: "Eigenständigen Importworker-Dienst in stackctl und dessen Bedienung beschrieben"
status: active
agent_project: ki-knowledge-next
relations:
  - target: README.md
    type: parent
    reason: Featureindex
---

# Import und Jobs

## Ablauf und Batch [ablauf-und-batch]

```yaml block-meta
updated: "2026-11-11 23"
status: active
relations:
  - target: ../architecture/IMPORT-UND-JOBS.md#modell-und-grenzen
    type: depends-on
    reason: Getrennte Quell-, Lauf-, Batch- und Jobstände
```

Unter `/content/sources/` stehen bereitgestellte Dateien und registrierte
Originalquellen in getrennten Tabellen. Die Checkbox im jeweiligen
Tabellenkopf markiert alle Einträge dieser Seite; bei teilweiser Auswahl
zeigt sie einen Zwischenstand. Aktion und Einreihungsbutton direkt unter
der Tabelle gelten ausschließlich für deren Auswahl. Ein Zähler zeigt die
markierten Einträge. Auswahlfehler erscheinen innerhalb der Oberfläche.
Ein Batch umfasst maximal 100 verschiedene
Dateien oder Quellen, nicht unsichtbar alle Treffer eines Filters.

Bei Dateien: **nur registrieren und Original sichern** oder **registrieren,
zerlegen und Markdown ablegen**. Bei registrierten Quellen: **zerlegen und
ablegen** oder **Originale und vorhandene Extraktionen ablegen/prüfen**.
Die Auswahl erzeugt eine Batchseite mit einem Job je Eintrag. Ein gestarteter
Worker führt sie aus; ein HTTP-Erfolg beim Einreihen bedeutet noch keinen
Import- oder Ablageerfolg.

Direkte Einzelaktionen für bereits vorhandene Dateien und Quellen bleiben
nutzbar. Ein Browser-Einzelupload ist nicht mehr vorhanden.
Erfolgreiche Direktzerlegung reiht automatisch einen separaten Ablagejob ein.
Ein erneuter Klick auf eine bereits zerlegte Quelle startet keinen neuen Lauf;
auf der Laufseite kann dessen Ablage ausdrücklich erneut eingereiht werden.
Registrierung allein zerlegt nichts. Die Originalkopie wird als Ablagejob
gesichert. Kein Ablauf gibt Inhalte automatisch frei.

## Ablage und Browsing [ablage-und-browsing]

```yaml block-meta
updated: "2026-11-11 06"
status: active
relations:
  - target: ../architecture/IMPORT-UND-JOBS.md#dateisystem-vertrag
    type: depends-on
    reason: Bytegleiche Originale, Markdown-Snapshots und Manifest
```

Für eine Quelle der Domäne `ki:platon` wird der Datenbaumordner `platon`
verwendet:

```text
platon/orig/QUELL-ID/original.epub
platon/md/_extractions/LAUF-ID/DOKUMENT-ID.md
platon/md/_extractions/LAUF-ID/manifest.json
```

Ein EPUB-Lauf kann mehrere Markdown-Dateien erzeugen. Die Dateien enthalten
den unveränderlichen Ausgangsstand, nicht spätere Editorrevisionen.
Originale bleiben zusätzlich in der DB gespeichert; die bereitgestellte
EPUB-Datei wird nicht verschoben oder gelöscht. Das Manifest enthält
Quellfingerabdruck, Pipeline, Kapitelbezüge und Extraktionsmetadaten.

Die Laufseite verlinkt Dokumente, Ausgangssnapshots und eine neue
**Blöcke-/Metadatenansicht**. Diese zeigt Dokumentfrontmatter, Adaptermetadaten,
Einleitung und H2-Blöcke mit vorhandenen IDs; lokale `yaml block-meta`-
Abschnitte bleiben direkt im Block sichtbar. Fehlende Attribute werden nicht
automatisch ergänzt. Das Wissensnetz kann dieselben `.md`-Dateien lesen;
neu materialisierte Datenbaum-Domänen werden auch im Webprozess verfügbar.

Erzeugte Dateien sind schreibgeschützt (`0444`). Wiederholung verifiziert
vorhandene Dateien und rekonstruiert fehlende. Veränderte Dateien werden
nicht überschrieben. Die Dateisystem-Ablage erzeugt keine neue
redaktionelle Revision und ändert keine Freigabe.

## Listen und Zählwerte [listen-und-zaehlwerte]

```yaml block-meta
updated: "2026-11-11 17"
status: active
relations:
  - target: ../architecture/IMPORT-UND-JOBS.md#ansichten-und-rechte
    type: depends-on
    reason: Umfang, Inventurgrenzen und gemeinsame Rechte
```

| URL / Navigation | Filter und Darstellung |
|---|---|
| `/content/files/` · Dateibestand | Mengen und Bytes je Domäne/Bereich/Formatordner; Dateiliste mit Pfadsuche, Bereich und Format |
| `/content/sources/` · Quellen | Pfad/Name, Format und registrierter Stand; paginierte Bereitstellung und registrierte Quellen, Batchwahl |
| `/content/` · Importläufe | Dateiname und Laufstatus; Einstieg in Dateibestand und Batchwahl |
| `/content/output/` · Statische Ausgabe | Freigegebene Domänen und HTML-Site-ZIP-Downloads |
| `/content/documents/` · Textwerkstatt | Titel und Freigabestand |
| `/content/jobs/` · Importjobs | Status, Aktion, Pfadsuche; Batch-, Quell- und Laufbezüge |

Die persönliche Domänenwahl filtert diese Listen. Dateimengen zählen
bereitgestellte Dateien, `orig`-Dateien und Extraktionsdateien getrennt;
JSON-Manifeste zählen als Dateien. Mengen sind kein Beleg für erfolgreiche
Registrierung oder aktuelle Inhaltsgleichheit. Der Artefaktindex verlinkt
nachvollziehbare DB-Quellen und Läufe.

Die Inventur liest keine Originalinhalte. Unlesbare Teilbäume werden
als Fehler mit unvollständigen Zählwerten angezeigt; Symlinks und versteckte
Dateien werden ausgelassen. Die Grenze liegt bei 5000 Einträgen und 20 Ebenen
innerhalb der bekannten Format-/Originalbereiche. Das ist keine vollständige
Inventur beliebiger alter Verwaltungsverzeichnisse.

## Worker und Fehler [worker-und-fehler]

```yaml block-meta
updated: "2026-11-11 23"
status: active
relations:
  - target: ../architecture/IMPORT-UND-JOBS.md#worker-und-zustaende
    type: depends-on
    reason: Queuezustände, Sperre und nachvollziehbare Versuche
  - target: KONFIGURATION-UND-START.md#lokaler-start
    type: reference
    reason: Gemeinsame lokale Prozesssteuerung
```

`./start` startet Django und einen separaten Importworker gemeinsam.
In `stackctl` sind `django` und `import-worker` eigenständige Dienste:
`stackctl start` startet beide, `stackctl start import-worker` nur den Worker.
Status und Logs stehen mit `stackctl status import-worker` und
`stackctl logs import-worker` bereit. `stackctl run django` startet allein
den Webserver.

Bei direktem Django-/IDE-Start den Worker zusätzlich im selben
Konfigurationskontext starten:

```bash
.venv/bin/python manage.py content_worker
```

Für einen endlichen Lauf:

```bash
.venv/bin/python manage.py content_worker --once
.venv/bin/python manage.py content_worker --job JOB-UUID
```

`--once` arbeitet die wartende Queue ab und endet, wenn sie leer ist.
`--job` führt nur den angegebenen wartenden Job aus. Pro DB/`VAR_DIR`
darf nur ein Worker laufen; ein zweiter meldet die bestehende Sperre.
Ohne Worker bleiben Jobs wartend. Jobliste, Batch und Jobdetails prüfen die
aktive Betriebssystemsperre; eine zurückgebliebene Sperrdatei zählt nicht als
laufender Worker. Das bestätigt einen aktiven Workerprozess, nicht die
Reaktionszeit einer gerade laufenden Extraktion.

Dieselben Seiten zeigen Wartende, Laufende, Abgeschlossene, Fehler und
Abbrüche sowie die Zahl beendeter Jobs. Auf der Batchseite beziehen sich die
Zähler auf den gesamten Batch, in der Jobliste auf den gewählten Filter.
Mit JavaScript werden Status, Fehler und Ergebnisse alle drei Sekunden
aktualisiert; ohne JavaScript die Seite neu laden. Verbindungsfehler werden
angezeigt, statt den zuletzt gelesenen Stand als aktuell auszugeben.

SIGTERM oder Strg+C lässt den aktuellen Job auslaufen und verhindert den
nächsten Claim. Bei erzwungenem Abbruch bleibt die Wiederaufnahme prüfpflichtig.

Jobdetails zeigen festgelegten Quellfingerabdruck, Pipeline, Ergebniswege
und jeden Versuch mit Workeridentität, Zeiten und Fehler. Auftraggeber
oder Staff können fehlgeschlagene Jobs erneut einreihen und wartende
abbrechen. Laufende Jobs werden nicht gewaltsam abgebrochen.

Jobliste und Batchansicht bieten Checkboxen und „Alle wartenden Jobs dieser
Seite markieren / abwählen“. „Markierte Jobs abbrechen“ beendet die explizite
Auswahl gemeinsam; abgeschlossene und laufende Jobs sind nicht auswählbar.
Die Auswahl bleibt bei automatischen Aktualisierungen erhalten. Nicht
angezeigte Folgeseiten werden nicht mit ausgewählt. Ist ein markierter Job
inzwischen gestartet, wird der gesamte Abbruch abgelehnt; Auswahl
aktualisieren. Jobnachweise bleiben erhalten, Originale werden nicht gelöscht.

Ein neu gestarteter Worker markiert unterbrochene eigene Jobs zur Prüfung;
sie werden nicht blind automatisch wiederholt. Bei geänderter Quelldatei
neu auswählen; bei veränderter Ablagedatei administrativ prüfen.
Erfolgreiche Extraktionen bleiben erhalten, auch wenn nur die Ablage
fehlgeschlagen ist. Eine Wiederholung nutzt denselben Extraktionsstand.
