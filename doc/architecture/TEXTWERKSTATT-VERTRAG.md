---
title: "Textwerkstatt-Vertrag"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Bündelt die verbleibenden technischen Anschlussfragen des einfachen Editors und seiner KI-Vorschläge an Next."
created: "2026-11-11 05"
updated: "2026-11-12 07"
update_reason: "Anzeigeumbruch und erhöhte Zieltext-Höhe im Variantenvertrag aktualisiert"
status: draft
relations:
  - target: README.md
    type: parent
    reason: Architekturindex
---

# Textwerkstatt-Vertrag

## Demo und Ziel [demo-und-ziel]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations:
  - target: ../features/TEMPLATE-UND-THEME.md#textwerkstatt-demo
    type: reference
    reason: Vorhandene Read-only-Demo der alten Oberfläche
  - target: QUELLEN-UND-TEXTWERKSTATT.md#modellentscheidung
    type: depends-on
    reason: Führende Herkunfts- und Revisionslinie
  - target: ui/EDITOR-UND-KI.md#arbeitsraum
    type: reference
    reason: Vereinbarter editorzentrierter Einstieg
```

Die alte `/workbench/`-Demo bleibt eine gestalterische Referenz.
Der neue Anschluss folgt dem [UI-Entwurf](ui/EDITOR-UND-KI.md), nicht
einem vollständigen Kompatibilitätsadapter für sämtliche Alt-APIs.
Bearbeitung und Vorschlagsannahme verwenden die vorhandenen Next-Dienste.

## Identität und Rechte [identitaet-und-rechte]

```yaml block-meta
updated: "2026-11-11 20"
status: draft
relations: []
```

Offen bleiben freie Notizen ohne Importlauf, persönliche beziehungsweise
gemeinsame Arbeitsbereiche und die Rechte für Text, Attribute und Freigabe.
Dokument- und Blockauswahl müssen auf eindeutige Next-Ressourcen zeigen;
ihre editierbaren Inhalte und Metadaten benötigen explizite Zuständigkeiten.

## Sicherungsanschluss und Konflikte [revisionen-yaml-konflikte]

```yaml block-meta
updated: "2026-11-12 00"
status: draft
relations:
  - target: ui/EDITOR-UND-KI.md#sicherungsstaende
    type: reference
    reason: Einfache Bedienung der intern revisionierten Sicherungen
```

Der [Editoranschluss](../features/QUELLEN-UND-TEXTWERKSTATT.md#text-bearbeiten)
verwendet die vorhandenen Speicher- und Wiederherstellungsdienste mit
Konfliktschutz. KI-Textannahmen bewahren einen noch ungespeicherten
Ausgangspuffer als eigenen Stand vor dem Ersatz. Offen bleiben automatische
Sicherungszeitpunkte außerhalb ausdrücklicher Speicheraktionen.

Der Editor bearbeitet den headerfreien Markdown-Body. Textänderungen
vererben vorhandene Metadaten; Attributänderungen sind eigene Aktionen.
Freigaben bleiben an konkrete gespeicherte Fassungen gebunden.

## Auswahl und KI-Annahme [markierungen-und-ki]

```yaml block-meta
updated: "2026-11-12 05"
status: draft
relations:
  - target: ../features/QUELLEN-UND-TEXTWERKSTATT.md#ki-textvorschlaege
    type: reference
    reason: Implementierte genaue Textauswahl und transaktionale Vorschlagsannahme
  - target: ui/EDITOR-UND-KI.md#ki-vorschlaege
    type: reference
    reason: Begrenzter Kontext und geprüfte Vorschläge statt vollständigem Chatmodell
```

Auswahlvorschläge benötigen Ausgangstext und eindeutig wiederauffindbare
Textstellen. Unicode-Codepoints und JavaScript-UTF-16-Indizes sind dabei
ausdrücklich zu unterscheiden. Dauerhafte Annotationen sind ein eigener
späterer Ausbau, keine Voraussetzung des einfachen Editors.

Für Textvorschläge sind Codepoint-Anker, exakter Ausgangspuffer, Titel und
DB-Ausgangsstand festgehalten. Annahme und gegebenenfalls Puffersicherung
geschehen transaktional über die vorhandenen Revisionsdienste; eine zweite
Annahme wird abgelehnt. Provider, Modell, Promptversion und Auftrag bleiben
am Vorschlag nachvollziehbar. Generierungen haben ein Eingabelimit,
Zeitlimit und eine Begrenzung pro Nutzer.

Offen sind strukturierte Ergebnisse für Attribute und Blockaufteilung,
feingranulare Teilannahme und Aufbewahrungsgrenzen für Aufträge.

Die Generierung läuft synchron im Webprozess über `ki-core`; es gibt
keinen separaten KI-Worker oder Streamingkanal. `TextProposal` bewahrt
Ausgangspuffer, Auswahl, Auftrag, expliziten Kontext, Provider/Modell,
Promptversion, Ergebnis und Annahmerevision. Statuswerte sind
`generating`, `ready`, `failed`, `accepted` und `discarded`. Bei Annahme
wird auch der vom Nutzer bearbeitete Ersatztext gespeichert.

Generieren, Annehmen und Verwerfen verwenden angemeldete, CSRF-geschützte
POST-Aufrufe. Nur der Ersteller darf seinen Vorschlag annehmen oder
verwerfen. Antworten liefern JSON; Ausgangskonflikte ergeben HTTP 409,
ungültige Eingaben HTTP 400, zurückgewiesene Generierungen HTTP 422
und ungültige Providerkonfiguration HTTP 503. Providerfehlertexte werden
redigiert; das Log nennt Vorschlags-ID und Fehlerklasse.

Der Editor lädt den jüngsten eigenen offenen Vorschlag erneut. Nach einem
Browserabbruch kann der synchrone Provideraufruf weiterlaufen; vor einer
Wiederholung zuerst diesen Stand prüfen. Es gibt noch keine automatische
Bereinigung verwaister `generating`-Aufträge oder Aufbewahrungsfrist.
Das Minutenlimit ist eine DB-Zählprüfung, keine strikte Sperre gegen
gleichzeitige Generierungen. Größen- und Zeitgrenzen stehen in der
[KI-Konfiguration](../features/KONFIGURATION-UND-START.md#ki-konfiguration).

## Gemeinsame Editorvarianten [editorvarianten]

```yaml block-meta
updated: "2026-11-12 07"
status: active
relations:
  - target: ../features/QUELLEN-UND-TEXTWERKSTATT.md#editor-kurzanleitung
    type: reference
    reason: Kurze Bedienung der beiden Ansichten
  - target: ui/EDITOR-UND-KI.md#seitenentwuerfe
    type: reference
    reason: Erprobung eigener Oberflächen ohne zweite Inhaltsspeicherung
  - target: ui/EDITOR-UND-KI.md#layout-presets
    type: reference
    reason: Bewerteter Erweiterungsvertrag für Presets und Widgetkit-Adapter
```

`/content/editor/` und `/content/editor-wide/` haben eigene Textlisten,
Dokument- und Wiederherstellungsrouten. Die breite Vorlage
`editor_wide.html` erbt die gemeinsame Editorvorlage. Views, Formulare,
JavaScript, Auswahlanker, Vorschläge und Revisionsdienste bleiben geteilt.
Die breite CSS-Klasse hebt die Maximalbreite des Seiteninhalts auf.
Benannte Grid-Areas halten die Vorschau ohne KI ab 751 Pixeln rechts
neben dem Editor. Mit KI liegt sie unter ihm in derselben Spalte;
die KI steht rechts über beide Zeilen, das Netz ab 1500 Pixeln links.
Die offenen Hauptspalten verwenden die Gewichte Editor `1.3`, KI `1.65`
und optional Netz `0.7`. Unter 751 Pixeln stehen alle Bereiche in einer
Spalte. Die breite Kontrolltextarea zeigt zwölf statt acht Zeilen und
hat eine entsprechend erhöhte Maximalhöhe von `37.5vh` statt `25vh`.
`wrap="soft"` und CSS-Anzeigeumbrüche erhalten ihren Wert und die
Codepoint-Auswahl; horizontales Scrollen ist deaktiviert.

Speichern, Validierungs-/Konfliktantworten und Wiederherstellen behalten
die aufgerufene Variante bei. KI-Annahme verwendet das versteckte Feld
`editor_variant=wide` ausschließlich zur Wahl einer der beiden festen
Rückkehrrouten; eine freie Redirect-URL ist nicht zulässig.
Ein Variantenwechsel lädt die gemeinsame gespeicherte Fassung und den
letzten eigenen offenen Vorschlag. Ungespeicherte Browserpuffer werden
nicht zwischen Seiten übertragen; die bestehende Verlassenswarnung gilt.
Es gibt weder eine neue DB-Migration noch eine separate Freigabe.

## Anschluss und Abnahme [anschluss-und-abnahme]

```yaml block-meta
updated: "2026-11-12 00"
status: draft
relations: []
```

Der Editor und KI-Textvorschläge verwenden denselben Ressourcen- und
Speichervertrag. Strukturierte Attribute folgen separat. Weitere Seitenvarianten
werden über die Navigation erprobt.

Zu prüfen sind Konflikte ohne Pufferverlust, Wiederherstellung, unveränderte
Originale und Header, Auswahlanker, Rechte, sichere Vorschlagsannahme und
getrennte Freigaben. Eine Abnahme des alten vollständigen Werkstattbackends
ist dafür nicht erforderlich.
