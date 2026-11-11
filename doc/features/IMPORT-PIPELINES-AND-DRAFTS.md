---
title: "Importpipelines und Entwürfe"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: features
purpose: "Beschreibt die implementierten Importformate, Verarbeitungsläufe und freigabegebundene HTML-/ZIP-Ausgabe."
created: "2026-11-09T18:13:00+01:00"
updated: "2026-11-11 17"
update_reason: "Einzelupload entfernt und statische Ausgabe auf eigener OUTPUT-Seite beschrieben"
status: active
relations:
  - target: "README.md"
    type: parent
    reason: "Featureindex"
  - target: "../architecture/KNOWLEDGE-DOMAIN-AND-LIFECYCLE.md"
    type: depends-on
    reason: "Fachliche Domänengrenzen und Zustände"
  - target: "../architecture/CMS-AND-PUBLISHING.md"
    type: reference
    reason: "CMS-Abwägung und Ausgabegrenzen"
  - target: "../architecture/QUELLEN-UND-TEXTWERKSTATT.md"
    type: depends-on
    reason: "Verbindliches Quellen-, Extraktions- und Revisionsmodell"
  - target: "QUELLEN-UND-TEXTWERKSTATT.md"
    type: reference
    reason: "Bedienung der Quellenregistrierung und Revisionshistorie"
  - target: "../architecture/AUSGABE-UND-PUBLIKATION.md"
    type: depends-on
    reason: "Publikationsgrenze und spätere hierarchische Ausgabe"
---

# Importpipelines und Entwürfe

## Umfang [scope]

```yaml block-meta
updated: "2026-11-11 17"
status: active
relations: []
```

Diese Beschreibung dokumentiert die vorhandenen Adapter, Dateibestandsimporte,
Laufzustände und statischen Downloads. Bedienung von Registrierung und
Textbearbeitung steht in [Quellen und Textwerkstatt](QUELLEN-UND-TEXTWERKSTATT.md).

Die Pipeline erzeugt aus einer Quelle zunächst extrahierte und normalisierte
Arbeitsdaten. Sie darf daraus nicht automatisch einen bestätigten
Wissensbestand oder eine veröffentlichte Seite machen. Das übergeordnete
[Domänen- und Lebenszykluskonzept](../architecture/KNOWLEDGE-DOMAIN-AND-LIFECYCLE.md)
beschreibt die Systemgrenzen.

## Import-Prototyp [import-prototype]

```yaml block-meta
updated: "2026-11-11 17"
status: active
relations: []
```

**Implementierter Stand, noch kein produktiver Gesamtworkflow:** Die
Django-App `knext.content` stellt unter `/content/` eine gemeinsame
Importwerkbank mit Anmeldung bereit. Das Wissensnetz bleibt unverändert.
Dieser Prototyp verwendet bewusst noch kein Wagtail; die CMS-Entscheidung
bleibt davon unabhängig.

Dateien und registrierte Quellen werden unter `/content/sources/` per
Mehrfachauswahl für Importjobs eingereiht. Einzeldatei-Uploadformular und
Upload-Endpunkt sind entfernt. Originale werden in der Datenbank gespeichert,
nicht in einem öffentlichen Uploadordner. Das führende
[Quellen- und Revisionsmodell](../architecture/QUELLEN-UND-TEXTWERKSTATT.md)
trennt Original, Extraktion, Arbeitsstand und Freigabe.

## Formatadapter [format-adapters]

```yaml block-meta
updated: "2026-11-11 17"
status: active
relations: []
```

Die `DocumentImporterRegistry` wählt formatbezogene Adapter. Die Registry-
Struktur orientiert sich am alten `ki_knowledge/infosite/importer.py`.
Der eigenständige EPUB-Parser und seine synthetischen Tests wurden aus
`ki_knowledge/integrations/epub_ingest.py` beziehungsweise
`tests/test_epub_ingest.py` übernommen, ohne das Altprojekt als Abhängigkeit.
Fehler werden nicht, wie beim alten einfachen PDF-Importer, als erfolgreicher
Inhalt zurückgegeben.

| Adapter | Heute unterstützt | Sichtbare Einschränkung |
|---|---|---|
| `TextImporter` | `.md`, `.markdown`, `.txt`; UTF-8 mit optionalem BOM | Markdown-Frontmatter separat vom Editortext; Textdateien wörtlich |
| `HtmlImporter` | Lokale `.html` und `.htm` | Lesbarer Text; keine aktiven Inhalte, Medien oder Layoutübernahme |
| `StructuredImporter` | CSV/TSV, JSON, YAML | Werteorientierte Vorschau, noch keine fachliche Feldzuordnung; CSV bis 10.000 Zeilen und 100 Spalten |
| `PdfImporter` | `.pdf` mit Textebene und Seitenmarkern | Maximal 200 Seiten; keine OCR, verschlüsselte oder reine Bild-PDFs schlagen mit Hinweis fehl |
| `DocxImporter` | `.docx` mit Absätzen, Überschriften und Tabellen | Keine Bilder, Kommentare oder Layouttreue; Tabellen nach Absatztext |
| `SpreadsheetImporter` | `.xlsx`, ein Dokument je Blatt | Gespeicherte Zellwerte, keine Formelberechnung; insgesamt 10.000 Zeilen, 100 Spalten je Blatt |
| `EpubImporter` | Textuelle EPUB-2/3-Kapitel in Lesereihenfolge | Ein Dokument je Kapitel, Herkunft erhalten; Medien fehlen, Kapitelverknüpfungen noch nicht für die Ausgabe umgeschrieben |

Quelldateien sind auf 10 MiB begrenzt, Ergebnisse auf insgesamt zwei Millionen
Zeichen und 300 Dokumente je Lauf. ZIP-basierte Formate werden vor Verarbeitung
auf Eintragszahl, entpackte Größe und Kompressionsverhältnis geprüft.
Nichtendliche Zahlen wie `.nan` und `.inf` in Markdown-Frontmatter werden
als Importfehler gemeldet, statt ungültige JSON-Metadaten zu speichern.
Das ist kein Ersatz für isolierte Worker oder harte Laufzeit-/Speicherlimits.
Scans, Bild-OCR, ODS, alte binäre Office-Formate, Ontologien, Jira-Anbindung
und Webabruf sind noch nicht implementiert.

## Pipeline-Lebenszyklus [pipeline-lifecycle]

```yaml block-meta
updated: "2026-11-11 17"
status: active
relations:
- target: ../architecture/KNOWLEDGE-DOMAIN-AND-LIFECYCLE.md#lifecycle
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

Vor dem Lauf steht die Bereitstellung einer Datei; sie ist noch kein
Datenbankimport. Die Verarbeitung wird danach nachvollziehbar dargestellt:

1. Quelle registrieren und Typ/Größe prüfen.
2. Adapter und Pipeline-Version bestimmen.
3. Extraktion und Normalisierung ausführen.
4. Ergebnis mit Herkunft, Warnungen und Prüfvorschau speichern.
5. Fehler oder unvollständige Ergebnisse zur Korrektur markieren.
6. Redaktionell in der Revisionslinie weiterarbeiten und nach Prüfung freigeben.

Im implementierten Prototyp entstehen Extraktionssnapshot und Ausgangsentwurf
gemeinsam bei erfolgreicher Zerlegung. Das ist keine menschliche Prüfung
oder Freigabe; diese bleibt ausdrücklich separat.

Direkte Zerlegung bereits registrierter Quellen bleibt synchron im HTTP-Request;
Dateibestandsimporte laufen
über den separaten [DB-Worker](IMPORT-UND-JOBS.md). Ein Lauf besitzt die
Zustände bereit, wird verarbeitet, extrahiert oder fehlgeschlagen sowie
Versuchszähler und Fehler-/Warnungsausgabe. Derselbe Quellstand, dasselbe
Format und dieselbe Pipeline-Version verwenden den vorhandenen Lauf.
Eine neue Version erzeugt einen eigenen Lauf, ohne alte Dokumente zu ändern.
Batchauswahl, Queue und Worker sind implementiert. Unterbrochene
Workerjobs werden mit ihren Versuchen zur Prüfung markiert und können
ausdrücklich wiederholt werden; synchron gestartete Alt-Läufe werden dabei
nicht automatisch übernommen. Erfolgreiche Direktzerlegungen erzeugen einen
separaten Job zur Ablage des unveränderlichen Markdown-Ausgangsstands.

## Entwürfe und Review [drafts-and-review]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations:
- target: ../architecture/KNOWLEDGE-DOMAIN-AND-LIFECYCLE.md#collaboration
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

Die Dokumentansicht zeigt Domäne, Quellstelle, Pipelinewarnungen, aktuelle
Revision und bestehenden Freigabestand. Nutzer mit `content.publish_content`
können die aktuelle Revision ausdrücklich freigeben; spätere Bearbeitung
verändert diese Freigabe nicht.

Editor, Historie und Konfliktverhalten sind in
[Quellen und Textwerkstatt](QUELLEN-UND-TEXTWERKSTATT.md) beschrieben.
Alle angemeldeten Nutzer teilen denselben Bestand. Getrennte Review-Rollen,
Domänen-ACLs, Mandantentrennung und KI-Vorschläge sind noch nicht verfügbar.

## Fehler und Wiederaufnahme [failure-handling]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations: []
```

Die Laufansicht zeigt konkrete Importfehler und Adapterwarnungen.
Ungültige Extraktion erzeugt keine teilweise gespeicherte Dokumentserie.
Die registrierte Quelle bleibt bei einem Extraktionsfehler bestehen.

„Verarbeitung erneut versuchen“ ist nur bei fehlgeschlagenen Läufen der
aktuellen Pipeline möglich. Ein laufender oder abgeschlossener Lauf wird
nicht erneut beansprucht. Eine abgelöste Pipeline lässt sich nicht mit neuem
Code unter altem Versionsnamen wiederholen; die Quelle wird stattdessen mit
der aktuellen Version zerlegt.
Es gibt noch keine automatische Retryplanung oder Abbruch-/Pausefunktion.

## Statische Ausgabe [static-output]

```yaml block-meta
updated: "2026-11-11 17"
status: active
relations:
- target: ../architecture/AUSGABE-UND-PUBLIKATION.md#publikationskomposition
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
- target: ../architecture/CMS-AND-PUBLISHING.md#publishing-model
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

Die Dokumentansicht bietet die freigegebene Revision als einzelne HTML-Datei
an. Die eigene OUTPUT-Seite unter `/content/output/` bietet für Domänen mit
freigegebenen Dokumenten einen Site-ZIP-Download und berücksichtigt die
persönliche Domänenwahl. Ohne Freigaben zeigt sie einen ausdrücklichen Leerstand.

Das ZIP enthält `index.html`, flach angeordnete Seiten mit stabilen
Dokument-UUID-Dateinamen und `manifest.json`. Das Manifest benennt
Revisions-IDs/-nummern, Revisions-/Extraktions-/Quellprüfsummen, Pipeline
und Freigabezeitpunkt. Ohne Freigabe erscheint ein Dokument nicht im Export;
bei neueren Entwürfen wird weiterhin die ältere freigegebene Fassung verwendet.

HTML wird vor Anzeige von unerlaubten Tags, Attributen und URL-Protokollen
bereinigt. Statische Ausgaben enthalten weder Editor noch internes App-Menü.
Die Dateien lassen sich unabhängig von Django ausliefern; der Download
überträgt sie nicht automatisch auf einen Webserver.

Seitenhierarchie, Suche, Assetübernahme, Baum-/PDF-Export und automatisierte
Publikation fehlen noch. EPUB-Kapitellinks sind noch nicht für vollständige
Site-Navigation umgeschrieben. Das spätere Zielbild steht in
[Ausgabe und Publikation](../architecture/AUSGABE-UND-PUBLIKATION.md);
die [CMS-Einordnung](../architecture/CMS-AND-PUBLISHING.md) bleibt davon getrennt.
