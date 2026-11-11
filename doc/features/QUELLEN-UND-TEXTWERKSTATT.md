---
title: "Quellen und Textwerkstatt"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: features
purpose: "Beschreibt die vorhandenen Arbeitswege von Quellenaufnahme bis Textbearbeitung, Wiederherstellung und Freigabe."
created: "2026-11-11T04:56:00+01:00"
updated: "2026-11-11 21"
update_reason: "Editor mit zuschaltbarer Bubble-Navigation, Eingabevorschau und Sicherungsworkflow beschrieben"
status: active
relations:
  - target: "../architecture/CONTENT-MODELL.md"
    type: depends-on
    reason: "Identitäten, Relationen und kontextbezogene Gliederungen"
  - target: "README.md"
    type: parent
    reason: "Index der implementierten Features"
  - target: "../architecture/QUELLEN-UND-TEXTWERKSTATT.md"
    type: depends-on
    reason: "Quellidentität, unveränderliche Extraktion und Revisionsvertrag"
  - target: "IMPORT-PIPELINES-AND-DRAFTS.md"
    type: reference
    reason: "Unterstützte Formate, Verarbeitungsläufe und statische Ausgabe"
---

# Quellen und Textwerkstatt

## Einstieg [einstieg]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
  - target: ../architecture/ui/EDITOR-UND-KI.md#arbeitsraum
    type: reference
    reason: Nutzerbegriff Textwerkstatt und geplanter editorzentrierter Arbeitsraum
  - target: NAVIGATION.md#gruppierte-navigation
    type: reference
    reason: Gemeinsame Navigation zwischen den Anwendungsbereichen
```

Die **Textwerkstatt** umfasst die Arbeitswege zum Bearbeiten von Texten und
ihren Zusammenhängen. Hier sind die bereits verfügbaren Schritte beschrieben;
der [UI-Entwurf](../architecture/ui/EDITOR-UND-KI.md#arbeitsraum) entwickelt
ihre gemeinsame Oberfläche weiter.

Über die [Navigation](NAVIGATION.md#gruppierte-navigation) führen
`/content/sources/` zum Quellbestand und `/content/documents/` zur
Dokumentübersicht. Dort lassen sich Texte, Herkunft, frühere Fassungen und
Freigabestand direkt öffnen. Die [Domänenauswahl](DOMAENEN.md) begrenzt
die angezeigten Inhalte.

Der Arbeitsweg lautet: **Quelle erfassen → in Markdown umwandeln →
Text bearbeiten → Fassung freigeben → Ausgabe erzeugen**.
Die [alte Werkstatt-Demo](TEMPLATE-UND-THEME.md#textwerkstatt-demo)
zeigt separat Beispielinhalte.

## Quellen registrieren [quellen-registrieren]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
- target: ../architecture/QUELLEN-UND-TEXTWERKSTATT.md#bereitstellung-und-quelle
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

Die Quellenansicht zeigt bereitgestellte Dateien, etwa
`Books/epub/buch.epub`, sowie bereits erfasste Quellen. Name und Format
lassen sich filtern; mehrere Quellen können gemeinsam ausgewählt werden.

„Als Quelle registrieren“ bewahrt eine Kopie der Datei und öffnet ihre
Detailansicht mit Herkunft, Größe, Format und Prüfsumme. Die Umwandlung
in Markdown folgt als eigener Schritt.

„Aktuelle Datei prüfen / registrieren“ erkennt bereits erfasste Inhalte.
Eine veränderte Datei erhält einen neuen Quellstand; der registrierte
Stand bleibt erhalten, auch wenn die bereitgestellte Datei später entfernt
wird. Dateien bleiben an ihrem bisherigen Ablageort.

Unterstützte Dateien liegen unter `DOMAIN/FILEFORMAT/DATEI`; weitere
Unterordner sind erlaubt. Versteckte Einträge und nicht unterstützte
Formatordner werden ausgelassen. Symlinks, unlesbare Dateien und
überschrittene Größenlimits werden ausdrücklich zurückgewiesen.
Die Sicherung von Originalkopien und Markdown-Ergebnissen beschreibt
[Import und Jobs](IMPORT-UND-JOBS.md).

## Markdown zerlegen [markdown-zerlegen]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
- target: ../architecture/QUELLEN-UND-TEXTWERKSTATT.md#zerlegung-und-ausgangsstand
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

„In Markdown zerlegen“ wandelt die gespeicherte Quelle in bearbeitbare
Dokumente um, beispielsweise die Kapitel eines EPUB. Die Laufansicht zeigt
Fortschritt, verwendete Verarbeitungsversion, Warnungen und Fehler.

Danach lässt sich jedes Dokument bearbeiten oder sein unveränderter
Markdown-Ausgangsstand ansehen und herunterladen.

Ein vorhandenes Ergebnis derselben Verarbeitungsversion wird wieder geöffnet.
Fehlgeschlagene Läufe können ausdrücklich wiederholt werden. Eine neuere
Verarbeitungsversion kann neue Ergebnisse erzeugen; ältere bearbeitete
Dokumente bleiben erhalten.

Die Batch-Auswahl unter `/content/sources/` reiht mehrere Quellen ein;
`/content/` zeigt ihre Läufe. Unterstützte Formate beschreibt
[Importpipelines und Entwürfe](IMPORT-PIPELINES-AND-DRAFTS.md).

## Text bearbeiten [text-bearbeiten]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
- target: ../architecture/ui/EDITOR-UND-KI.md#arbeitsraum
  type: depends-on
  reason: Editorzentrierter Arbeitsraum mit zuschaltbaren Ansichten
- target: ../architecture/QUELLEN-UND-TEXTWERKSTATT.md#yaml-und-editor
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

Die Dokumentseite bietet Titel, Markdown-Textfeld und eine bereinigte
Vorschau der gespeicherten Fassung. Ungespeicherte Eingaben sind noch
nicht in dieser Vorschau zu sehen.

Metadaten aus dem ursprünglichen YAML-Header stehen getrennt und
schreibgeschützt neben dem Text. Sie bleiben beim Speichern erhalten.
Der bearbeitbare Redaktionstitel ist unabhängig vom ursprünglichen
Metadatenfeld `title`. Ein YAML-Header im Textfeld wird zurückgewiesen.

Der heutige Button „Als neue Revision speichern“ bewahrt eine neue Fassung.
Falls zwischenzeitlich jemand anderes gespeichert hat, wird ein Konflikt
angezeigt statt dessen Arbeit zu überschreiben.

Unter `/content/editor/` lässt sich ein Dokument für die neue Editoransicht
wählen. „Editor · Entwurf“ ist vorläufig in der INTERN-Navigation verankert.
Dokumentseiten und Werkstattübersicht verlinken ebenfalls auf den Editor.

Die Ansicht bietet Markdown-Textfeld und zuschaltbare Vorschau und
Bubble-Navigation. „Vorschau aktualisieren“ rendert die aktuellen Eingaben
bereinigt und erneuert ihre Gliederung, ohne zu speichern. Die Bubbles
markieren den direkten Abschnittstext einschließlich seiner Überschrift;
Verbindungslinien zeigen die Überschriftenhierarchie, keine fachlichen
Relationen. Suche und Abschnittsauswahl erschließen auch größere Texte.
Die Bubble-Darstellung ist auf 120 Treffer begrenzt; die Auswahl enthält alle.

Nach Textänderungen muss die Gliederung vor einer Abschnittsauswahl
aktualisiert werden. Ansichtsschalter erhalten Text und Auswahl.
Beim Verlassen mit ungespeicherten Änderungen erscheint eine Warnung.
Speichern nutzt dieselben Fassungen wie die bisherige Dokumentseite.
Bei einem Konflikt bleiben die Eingaben und ihr ursprünglicher Ausgangsstand
erhalten; „Gespeicherten Stand laden“ verwirft sie ausdrücklich.

Ohne JavaScript bleiben Speichern, gespeicherte Vorschau und Wiederherstellen
verfügbar; Bubble-Navigation und Eingabevorschau benötigen JavaScript.
Attribute und KI-Vorschläge sind in dieser Variante noch nicht angeschlossen.

## Historie und Wiederherstellung [historie-und-wiederherstellung]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
- target: ../architecture/ui/EDITOR-UND-KI.md#sicherungsstaende
  type: reference
  reason: Einfache Bedienung der gespeicherten Fassungen als Sicherungen
- target: ../architecture/QUELLEN-UND-TEXTWERKSTATT.md#revisionslinie-und-freigabe
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

Frühere Fassungen sind mit Zeitpunkt, Bearbeiter und Änderungsanlass
erreichbar. Jede lässt sich lesen, als Markdown herunterladen und mit
ihrem Vorgänger vergleichen. Der Vergleich umfasst Text und YAML-Header,
nicht den separat geführten Redaktionstitel.

„Diesen Stand als neue Revision übernehmen“ macht eine frühere Fassung
wieder zum aktuellen Arbeitsstand. Die bisherigen Fassungen bleiben
erhalten; zwischenzeitliche Änderungen werden auch hier geprüft.

Im neuen Editor sind frühere Arbeitsstände unter „Sicherungen“ erreichbar.
Der vorherige Stand ist vorausgewählt; andere Sicherungen lassen sich nach
Zeitpunkt, Titel und Bearbeiter auswählen. Vorheriges Lesen und Vergleichen
bleibt möglich. Wiederherstellen bewahrt den aktuellen gespeicherten Stand;
ungespeicherte Eingaben werden nach Bestätigung verworfen.
Die Speicherung erfolgt nur beim ausdrücklichen Speichern oder
Wiederherstellen; automatische Sicherungen von Eingabepuffern sind noch
nicht implementiert.

## Gliederungen und Zusammenstellungen [gliederungen-und-zusammenstellungen]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
  - target: "../architecture/CONTENT-MODELL.md#app-und-grenzen"
    type: depends-on
    reason: "Vertrag und Abgrenzung der DB-basierten Zusammenstellungen"
```

Dokumente und frühere Fassungen verlinken ihre schreibgeschützte Gliederung,
auch mit tieferen Überschriften. Von dort sind Blocktexte und Herkunft
erreichbar.

Unter `/content/collections/` entstehen eigene Sequenzen, Hierarchien,
Sammlungen oder Netze. Titel, Herkunft und Domäne helfen bei der Auswahl.
Die Struktur wird derzeit als JSON bearbeitet; Beispiele stehen am Editor.
Ein Download ermöglicht ihre Wiederverwendung. Inhalte dürfen mehrfach
vorkommen. Unbekannte Ressourcen, kreisförmige Elternzuordnungen und
veraltete Bearbeitungen werden zurückgewiesen.

Der Ressourcenkatalog erschließt Dokumente, Blöcke, Ordner und
Zusammenstellungen mit ihren Beziehungen und gespeicherten Textständen.
Ordner dienen der Gruppierung. Beziehungstypen lassen sich mit Definition
ergänzen; die gemeinsame Werteliste beschreibt der
[Relationskatalog](KONFIGURATION-UND-START.md#relationenkatalog).
Beziehungen können Domänengrenzen überschreiten.

Diese Ansichten sind bisher tabellarisch. Ihre geplante Bearbeitung über
Wiki-Ansichten steht im
[Zusammenstellungskonzept](../architecture/ui/ZUSAMMENSTELLUNGEN.md).
Speichern einer Struktur gibt ihre Inhalte nicht automatisch frei.

## Freigabe und Grenzen [freigabe-und-grenzen]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
- target: ../architecture/QUELLEN-UND-TEXTWERKSTATT.md#grenzen-und-ausbau
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

Nutzer mit Freigaberecht (`content.publish_content`) können die aktuelle
Fassung für die Ausgabe bestimmen. Weitere Bearbeitung oder
Wiederherstellung lässt diese Freigabe unverändert. HTML-Ausgabe verwendet
weiterhin die freigegebene Fassung:
[Import und Ausgabe](IMPORT-PIPELINES-AND-DRAFTS.md).

Angemeldete Nutzer teilen derzeit den Bestand. Private Arbeitsbereiche,
Domänenrechte, Annotationen, KI-Vorschläge und ein Attributeditor sind
noch nicht angeschlossen. Die Anwendung bewahrt Originale und ältere
Fassungen; sie ist kein manipulationssicheres Archiv.

Technische Modellentscheidungen und Anschlussgrenzen stehen im
[Architekturkonzept](../architecture/QUELLEN-UND-TEXTWERKSTATT.md).
