---
title: "Textwerkstatt-Vertrag"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Bündelt die verbleibenden technischen Anschlussfragen des einfachen Editors und seiner KI-Vorschläge an Next."
created: "2026-11-11 05"
updated: "2026-11-12 00"
update_reason: "KI-Textannahme als umgesetzt eingeordnet und verbleibende strukturierte Anschlüsse abgegrenzt"
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
updated: "2026-11-12 00"
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
