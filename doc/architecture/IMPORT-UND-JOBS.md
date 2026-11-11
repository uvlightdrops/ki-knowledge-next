---
title: "Import und Jobs"
project: ki-knowledge-next
scope: architecture
purpose: "Definiert Quellidentität, Dateisystemvertrag und serielle Jobausführung."
created: "2026-11-11 06"
updated: "2026-11-11 21"
update_reason: "Lokale Prozessaufsicht, Stopvertrag und Workerstatus ergänzt"
status: active
agent_project: ki-knowledge-next
relations:
  - target: README.md
    type: parent
    reason: Architekturindex
---

# Import und Jobs

## Modell und Grenzen [modell-und-grenzen]

```yaml block-meta
updated: "2026-11-11 06"
status: active
relations:
  - target: ../features/IMPORT-UND-JOBS.md#ablauf-und-batch
    type: reference
    reason: Implementierte Auswahl und Verarbeitung des Importablaufs
```

Bereitgestellte Dateien, registrierte Originale, formatabhängige Verarbeitung,
immutable Markdown-Extraktion und redaktionelle Revision sind getrennte
Stände. Ein Job ist ein Auftrag, nicht die Quelle oder eine Revision.
Der vorhandene `ImportRun` bleibt der eindeutige fachliche Lauf für
Quelle und Pipeline-Version.

`ImportBatch` gruppiert eine explizite Auswahl und ihren Auftraggeber.
`ImportJob` enthält genau eine Datei/Quelle und eine feste Aktion:
Registrieren, vollständiger Import, Zerlegen oder Dateisystem-Abbild.
`JobAttempt` hält Nummer, Workeridentität, Beginn, Ende und Fehler eines
Versuchs fest. Teilerfolge anderer Jobs werden nicht zurückgerollt oder als
pauschaler Batch-Erfolg versteckt.

Bei Dateiauswahl wird ein SHA-256-Fingerabdruck festgehalten. Der Worker
prüft ihn vor und während der Registrierung. Eine inzwischen ersetzte Datei
führt zum Fehler, nicht zum Import anderer Bytes unter demselben Auftrag.
Neue Auswahl ist dann erforderlich. Registrierung legt die echten Bytes
als `SourceAsset` fest; weitere Schritte arbeiten ausschließlich damit.

## Dateisystem-Vertrag [dateisystem-vertrag]

```yaml block-meta
updated: "2026-11-11 06"
status: active
relations:
  - target: ../features/IMPORT-UND-JOBS.md#ablage-und-browsing
    type: reference
    reason: Sichtbare Ablage und Browsing des unveränderlichen Ausgangsstands
```

```text
DATA_DIR/DOMAIN/FILEFORMAT/FILE                     bereitgestellt
DATA_DIR/DOMAIN/orig/SOURCE-UUID/FILE                 Originalkopie
DATA_DIR/DOMAIN/md/_extractions/RUN-UUID/DOC-UUID.md   Extraktionssnapshot
DATA_DIR/DOMAIN/md/_extractions/RUN-UUID/manifest.json Herkunft
```

UUIDs verhindern Namenskollisionen und halten die Herkunft auch bei gleichen
Titeln eindeutig. `.md` enthält exakt die UTF-8-Bytes des DB-Extraktionssnapshots,
einschließlich ursprünglichem YAML-Header. Kein neuer Header, keine geratenen
Blockattribute und keine doppelte Kopie des aktuellen Editorstands.
Das JSON-Manifest enthält Pipeline, Quelle, Originalpfad, Dokumente, Locator,
Extraktionsmetadaten und Prüfsummen.

`FilesystemArtifact` verzeichnet die gesicherten Pfade und Fingerabdrücke.
Vollständige Dateien werden über temporäre Dateien und Hardlink-Publikation
ohne Überschreiben bereitgestellt; Verzeichnisse und Ziele werden ohne
Symlinkverfolgung geöffnet. Angelegte Dateien erhalten Modus `0444`.
Ein bereits vorhandenes Ziel muss bytegleich sein. Fehlende Abbilder sind
aus den DB-Snapshots reproduzierbar, veränderte werden ausdrücklich abgelehnt.

Die DB bleibt führend. DB und Dateisystem sind keine gemeinsame Transaktion:
teilweise gesicherte Dateien und Indexeinträge bleiben bei Ablagefehlern
erkennbar. Wiederholung überprüft oder ergänzt sie, ohne neue Contentrevision.
Der Manifestabschluss bezeichnet vollständige Ablage dieses Laufes.
Administratoren können Schreibrechte oder SQL umgehen; dies ist kein
manipulationssicheres Archiv und kein Aufbewahrungs-/Löschkonzept.

Die Markdown-Ablage liegt innerhalb der bestehenden Domänenquelle und ist
mit Wissenswiki und Dateitools lesbar. Erzeugte `_extractions`-Bäume werden
aus der Bereitstellungsinventur ausgeschlossen, damit keine rekursive
Reimportpipeline entsteht. Originaldateien werden nicht verschoben.

## Worker und Zustände [worker-und-zustaende]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
  - target: ../features/IMPORT-UND-JOBS.md#worker-und-fehler
    type: reference
    reason: Bedienung und Wiederaufnahme der DB-Queue
```

```text
queued → running → succeeded
                → failed → queued (ausdrückliche Wiederholung)
queued → cancelled
```

Ein eigener Django-Managementprozess arbeitet die DB-Queue seriell ab.
Eine nicht blockierende POSIX-Dateisperre unter `VAR_DIR/content-worker.lock`
schützt gegen zwei Worker derselben Datenbank. Sie gilt über die ganze
Workerlaufzeit. Jobclaim und Versuchsanlage geschehen atomar; Extraktion und
Dateischreiben nicht innerhalb einer langen Queue-DB-Transaktion.

Der lokale Starter beaufsichtigt Web und Worker als getrennte Prozesse
derselben Konfiguration. Unerwartetes Ende eines Dienstes beendet den
gemeinsamen Betrieb ausdrücklich. SIGTERM/SIGINT verhindert neue Claims,
ohne einen begonnenen Job zu unterbrechen. Ein erzwungener Stop bleibt über
den bestehenden Wiederaufnahmevertrag nachvollziehbar.

Die Webansichten lesen die aktive Betriebssystemsperre für die
Workerverfügbarkeit und die DB für Fortschritt und Ergebnisse. Dieser
Single-Host-Nachweis benötigt keine persistierten Heartbeats; er bestätigt
Prozessaktivität, nicht das Vorankommen einer einzelnen Extraktion.

`ImportRun.processing_job` kennzeichnet nur vom Worker übernommene
Verarbeitung. Nach einem Prozessabbruch markiert der nächste Worker unter
derselben Sperre laufende Jobs/Versuche als fehlgeschlagen beziehungsweise
`interrupted`. Nur deren eigene noch laufende Imports werden freigegeben.
Synchron im Web gestartete Imports werden dabei nicht übernommen.
Keine Zeitheuristik stiehlt einem langsamen, noch lebenden Worker den Auftrag.

Erwartete Import-, Dateisystem- und Konfliktfehler werden dauerhaft
aufgezeichnet und protokolliert. Unerwartete Programmfehler beenden den
Worker mit Traceback; die nächste Wiederaufnahme macht die Unterbrechung
sichtbar. Keine unbegrenzten automatischen Wiederholungen. Derselbe
Quell-/Pipeline-Lauf und unveränderte Dateisystemziele sind idempotent.
Eine geänderte Pipeline wird nicht unter dem alten Jobvertrag ausgeführt.

Dies ist eine lokale beziehungsweise Single-Host-Queue: Alle Worker müssen
dieselbe DB und denselben lokalen Sperrpfad verwenden. Ein Multi-Host-Cluster,
Leases, Prioritäten, Scheduler, harte Zeit-/Speicherlimits und Abbruch aktiver
Extraktionen sind nicht umgesetzt. Für diese Stufe ist keine Redis-/Celery-
Infrastruktur erforderlich.

## Standardansichten und Rechte [ansichten-und-rechte]

```yaml block-meta
updated: "2026-11-11 06"
status: active
relations:
  - target: ../features/IMPORT-UND-JOBS.md#listen-und-zaehlwerte
    type: reference
    reason: Gemeinsame Filter-, Listen- und Mengenansichten
```

Dateibestand, Quellen, Läufe, Dokumente und Jobs verwenden wenige tabellarische
Ansichten mit Filtern und Pagination. Die persönliche Domänenwahl ist deren
gemeinsamer Kontext, keine Zugriffskontrolle. Alle angemeldeten Nutzer können
den gemeinsamen Bestand lesen und Importjobs erstellen; nur Auftraggeber
oder Staff steuern Wiederholung und Abbruch.

Die Dateiinventur liest Namen und Größen in bekannten Format- und
`orig`-Verzeichnissen. Symlinks, versteckte Dateien und unbekannte
Verzeichnisbereiche werden nicht verfolgt; 5000 Einträge und 20 Ebenen
begrenzen den Scan. Unlesbare Teilbäume liefern ausdrücklich unvollständige
Zählwerte statt einer scheinbar vollständigen Null.

Der Admin zeigt Jobs, Versuche und Artefaktnachweise nur lesend.
Web-POSTs sind CSRF-geschützt. Rohdateien oder Pfade werden nicht unter einer
öffentlichen statischen URL ausgeliefert; authentifizierte Ansichten und
DB-Snapshots beziehungsweise verifizierte Manifeste liefern die Inhalte.
