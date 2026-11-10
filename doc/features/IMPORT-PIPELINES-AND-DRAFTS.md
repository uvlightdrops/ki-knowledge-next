---
title: "Importpipelines und Entwürfe"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: features
purpose: "Beschreibt die gewünschten Nutzerabläufe für heterogene Quellen, pipelinebasierte Verarbeitung, gemeinsame Entwürfe und kontrollierte Veröffentlichung."
created: "2026-11-09T18:13:00+01:00"
updated: "2026-11-10T20:10:00+01:00"
update_reason: "Ungültige nichtendliche Zahlen in Markdown-Metadaten als Importfehler abgegrenzt"
status: draft
semantic_blocks:
  - scope
  - import-prototype
  - format-adapters
  - pipeline-lifecycle
  - drafts-and-review
  - failure-handling
  - static-output
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
---

# Importpipelines und Entwürfe

## Umfang [scope]

Das Feature führt Quellen von der Erfassung bis zu einem prüfbaren
redaktionellen Ergebnis. Unterschiedliche Formate sollen über geeignete
Adapter in einen gemeinsamen Ablauf kommen, statt je Format eine eigene
unverbundene Importoberfläche zu erhalten.

Die Pipeline erzeugt aus einer Quelle zunächst extrahierte und normalisierte
Arbeitsdaten. Sie darf daraus nicht automatisch einen bestätigten
Wissensbestand oder eine veröffentlichte Seite machen. Das übergeordnete
[Domänen- und Lebenszykluskonzept](../architecture/KNOWLEDGE-DOMAIN-AND-LIFECYCLE.md)
beschreibt die Systemgrenzen.

## Import-Prototyp [import-prototype]

**Implementierter Stand, noch kein produktiver Gesamtworkflow:** Die
Django-App `knext.content` stellt unter `/content/` eine gemeinsame
Importwerkbank mit Anmeldung bereit. Das Wissensnetz bleibt unverändert.
Dieser Prototyp verwendet bewusst noch kein Wagtail; die CMS-Entscheidung
bleibt davon unabhängig.

### Content-Modell

| Klasse | Verantwortung |
|---|---|
| `SourceAsset` | Originalbytes, Dateiname, Domänenname, SHA-256, Größe und hochladender Nutzer |
| `ImportRun` | Quelle, Pipeline-/Adapterversion, Zustand, Versuche, Warnungen und konkrete Fehler |
| `ContentDocument` | Stabile UUID, Bezug auf Lauf und Quellstelle, aktuelle Revisionsnummer und Freigabe |
| `ContentRevision` | Neue Version von Titel und Markdown-Text, Quellmetadaten, Bearbeiter und Zeitpunkt |

Die Domänenauswahl stammt aus den konfigurierten Wissenswiki-Domänen.
Originale werden nicht in einem öffentlich erreichbaren Uploadordner abgelegt,
sondern in der Datenbank gespeichert. Gleiche Originalbytes innerhalb einer
Domäne und Pipeline-Version führen zum vorhandenen Lauf; bereits bearbeitete
Entwürfe werden nicht überschrieben. Ein fehlgeschlagener Lauf kann bewusst
erneut gestartet werden. Ein erfolgreicher Import ist keine Freigabe.

Jeder Speichervorgang erzeugt eine neue Inhaltsrevision. Die erwartete
Revisionsnummer verhindert stilles Überschreiben paralleler Änderungen.
Die Freigabe referenziert genau eine Revision und hält Nutzer und Zeitpunkt
fest. Spätere Änderungen verändern diese freigegebene Fassung nicht.
Das Bearbeiten der extrahierten Metadaten, vollständige Revisionsvergleiche
und Rollback sind noch nicht Bestandteil der Oberfläche.

### Formatklassen und Grenzen

Die `DocumentImporterRegistry` wählt formatbezogene Adapter. Die Registry-
Struktur orientiert sich am alten `ki_knowledge/infosite/importer.py`.
Der eigenständige EPUB-Parser und seine synthetischen Tests wurden aus
`ki_knowledge/integrations/epub_ingest.py` beziehungsweise
`tests/test_epub_ingest.py` übernommen, ohne das Altprojekt als Abhängigkeit.
Fehler werden nicht, wie beim alten einfachen PDF-Importer, als erfolgreicher
Inhalt zurückgegeben.

| Adapter | Heute unterstützt | Sichtbare Einschränkung |
|---|---|---|
| `TextImporter` | `.md`, `.markdown`, `.txt`; UTF-8 mit optionalem BOM | Markdown-Frontmatter als Dokumentmetadaten, Textdateien wörtlich |
| `HtmlImporter` | Lokale `.html` und `.htm` | Lesbarer Text; keine aktiven Inhalte, Medien oder Layoutübernahme |
| `StructuredImporter` | CSV/TSV, JSON, YAML | Werteorientierte Vorschau, noch keine fachliche Feldzuordnung; CSV bis 10.000 Zeilen und 100 Spalten |
| `PdfImporter` | `.pdf` mit Textebene und Seitenmarkern | Maximal 200 Seiten; keine OCR, verschlüsselte oder reine Bild-PDFs schlagen mit Hinweis fehl |
| `DocxImporter` | `.docx` mit Absätzen, Überschriften und Tabellen | Keine Bilder, Kommentare oder Layouttreue; Tabellen nach Absatztext |
| `SpreadsheetImporter` | `.xlsx`, ein Dokument je Blatt | Gespeicherte Zellwerte, keine Formelberechnung; insgesamt 10.000 Zeilen, 100 Spalten je Blatt |
| `EpubImporter` | Textuelle EPUB-2/3-Kapitel in Lesereihenfolge | Ein Dokument je Kapitel, Herkunft erhalten; Medien fehlen, Kapitelverknüpfungen noch nicht für die Ausgabe umgeschrieben |

Uploads sind auf 10 MiB begrenzt, Ergebnisse auf insgesamt zwei Millionen
Zeichen und 300 Dokumente je Lauf. ZIP-basierte Formate werden vor Verarbeitung
auf Eintragszahl, entpackte Größe und Kompressionsverhältnis geprüft.
Nichtendliche Zahlen wie `.nan` und `.inf` in Markdown-Frontmatter werden
als Importfehler gemeldet, statt ungültige JSON-Metadaten zu speichern.
Das ist kein Ersatz für isolierte Worker oder harte Laufzeit-/Speicherlimits.
Scans, Bild-OCR, ODS, alte binäre Office-Formate, Ontologien, Jira-Anbindung
und Webabruf sind noch nicht implementiert.

### Ansichten und Ausgabe

`WorkbenchView`, `ImportView` und `RunView` zeigen Quellen, Uploads und
Verarbeitungsläufe. Die Dokumentansicht kombiniert einen Markdown-Editor,
eine bereinigte Vorschau der gespeicherten Revision sowie Freigabe und
Revisionsübersicht. Vorschauen bleiben ausdrücklich unveröffentlicht.

HTML wird vor Anzeige von unerlaubten Tags, Attributen und URL-Protokollen
bereinigt. Nur Nutzer mit `content.publish_content` können freigeben.
Alle angemeldeten Nutzer teilen im Prototyp dieselben Inhalte: Es gibt noch
keine Domänen-ACLs, Mandantentrennung oder getrennten Review-Rollen.

Die Ausgabe bietet einzelne HTML-Dateien oder ein ZIP pro Domäne mit
`index.html`, stabil über Dokument-UUID benannten Seiten und einem
`manifest.json` mit Revisionsnummern, Quellprüfsummen, Pipeline und
Freigabezeitpunkt. Entwürfe ohne Freigabe sind ausgeschlossen; nach einer
erneuten Bearbeitung wird weiterhin die zuvor freigegebene Revision exportiert.
Es gibt noch keine Seitenhierarchie, Suchfunktion, automatische Bereitstellung
oder Übernahme in die Markdown-Wissensdomäne. Exportierte EPUB-Kapitel brauchen
für vollständige Navigation noch eine Linkumschreibung.

Die Verarbeitung läuft synchron im HTTP-Request. Produktionsbetrieb benötigt
zusätzlich isolierte Hintergrundverarbeitung, Wiederaufnahme unterbrochener
Läufe und passende Nutzer-/Domänenrechte. Ein nach Prozessabbruch auf
„Wird verarbeitet“ verbliebener Lauf wird noch nicht automatisch repariert.

## Formatadapter [format-adapters]

Der erste Umfang soll sich aus häufigen, konkreten Quellen ergeben. Zu
prüfende Kandidaten sind:

| Quellart | Beispiele für Verarbeitung | Besondere Prüfpunkte |
|---|---|---|
| Markdown und Text | Struktur und Metadaten übernehmen | Links, Überschriften, Kodierung und Herkunft |
| PDF und Office-Dokumente | Text und Tabellen extrahieren; OCR bei Bedarf | Seiten-/Abschnittsbezug, Tabellenverlust, Scanqualität |
| HTML und Webquellen | Lesbaren Inhalt und Metadaten erfassen | URL, Abrufzeit, Lizenz und entfernte Navigation |
| EPUB und Bücher | Kapitelstruktur und Text übernehmen | Kapitel-/Positionsbezug und Umfang |
| strukturierte Daten | CSV, JSON oder YAML abbilden | Schema, Datentypen und Feldzuordnung |
| externe Systeme | später etwa Wissensbasen oder Ticketsysteme anbinden | Authentifizierung, Änderungsabgleich und Löschungen |

Diese Liste bleibt das breitere Zielbild; den tatsächlich implementierten
Teilumfang beschreibt der Import-Prototyp oben. Sie ist keine Zusage, alle Formate gleichzeitig
zu unterstützen. Jeder Adapter muss unterstützte Varianten, Grenzen und
Ergebnisqualität sichtbar machen.

## Pipeline-Lebenszyklus [pipeline-lifecycle]

Eine Verarbeitung wird als nachvollziehbarer Lauf dargestellt:

1. Quelle registrieren und Typ/Größe prüfen.
2. Adapter und Pipeline-Version bestimmen.
3. Extraktion und Normalisierung ausführen.
4. Ergebnis mit Herkunft, Warnungen und Prüfvorschau speichern.
5. Fehler oder unvollständige Ergebnisse zur Korrektur markieren.
6. Nach menschlicher Prüfung daraus einen Entwurf oder Wissensinhalt erzeugen.

Ein erneuter Lauf muss Ursprung und Laufversion nachvollziehbar halten und
Duplikate vermeiden. Ob einzelne Schritte synchron ausgeführt oder über eine
Jobqueue verteilt werden, ist noch offen; lang laufende oder parallelisierbare
Schritte sollten später ohne Änderung des fachlichen Ablaufs ausgelagert
werden können.

## Entwürfe und Review [drafts-and-review]

Ein Entwurf ist eine bearbeitbare Revision und keine Kopie mit unklarem
Ursprung. Mindestens erkennbar sein sollen:

- zugehörige Domäne und gegebenenfalls Zielposition in der Seitenhierarchie;
- verwendete Quellen und konkrete Quellstellen, soweit verfügbar;
- angewendete Verarbeitungsschritte und KI-Vorschläge;
- Autor bzw. Bearbeiter, Erstellungszeit und Revisionsstand;
- Review- und Veröffentlichungsstatus.

Menschen können Entwürfe bearbeiten und gemeinsam prüfen. KI-Ausgaben
erscheinen als Vorschläge mit Bezug auf Ausgangstext und Quellen. Annahme,
Ablehnung und Veröffentlichung sind ausdrücklich bestätigte Aktionen.
Gleichzeitige Änderungen müssen entweder zusammengeführt oder als Konflikt
angezeigt werden; ein stilles Überschreiben ist nicht akzeptabel.

## Fehler und Wiederaufnahme [failure-handling]

Fehler sind pro Quelle und Verarbeitungsschritt sichtbar. Ein fehlgeschlagener
Lauf darf keine erfolgreiche Endfassung vortäuschen. Nutzer sollen erkennen,
ob das Problem in der Datei, im Adapter, in einer optionalen OCR-/KI-Stufe
oder in der Ausgabe liegt und welche Schritte wiederholt werden können.

Wiederholungen sollen idempotent sein: Bereits gespeicherte Ergebnisse werden
nicht unbemerkt dupliziert oder freigegebene Inhalte überschrieben. Vor einer
erneuten Verarbeitung geänderter Quellen muss erkennbar sein, ob ein neuer
Entwurf, ein Vergleich oder eine ausdrückliche Aktualisierung erwartet wird.

## Statische Ausgabe [static-output]

Aus freigegebenen Revisionen soll eine hierarchische HTML-Site erzeugt werden
können. Das Ergebnis enthält Navigation, stabile URLs, interne Verknüpfungen
und wahlweise sichtbare Quellenangaben. Ein Build referenziert die
eingeschlossenen Revisionen und kann getrennt von der CMS-Anwendung
bereitgestellt werden.

Nur freigegebener Inhalt gehört in die öffentliche Ausgabe; Vorschauen dürfen
Entwürfe anzeigen, aber müssen deutlich als nicht veröffentlicht markiert
sein. Welche Build-Werkzeuge, Themes, Suchfunktionen und Hostingziele wir
verwenden, entscheiden wir nach einem ersten Beispielinhalt. Die
[CMS-Einordnung](../architecture/CMS-AND-PUBLISHING.md) hält fest, warum ein
statischer Export nicht selbst die Redaktionsoberfläche ersetzt.
