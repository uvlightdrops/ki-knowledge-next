---
title: "Textwerkstatt-Vertrag"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Bündelt die verbleibenden technischen Anschlussfragen des einfachen Editors und seiner KI-Vorschläge an Next."
created: "2026-11-11 05"
updated: "2026-11-11 21"
update_reason: "Implementierten Editor- und Wiederherstellungsanschluss aus offenen Vertragsfragen herausgenommen"
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
updated: "2026-11-11 21"
status: draft
relations:
  - target: ui/EDITOR-UND-KI.md#sicherungsstaende
    type: reference
    reason: Einfache Bedienung der intern revisionierten Sicherungen
```

Der [Editoranschluss](../features/QUELLEN-UND-TEXTWERKSTATT.md#text-bearbeiten)
verwendet die vorhandenen Speicher- und Wiederherstellungsdienste mit
Konfliktschutz. Offen bleiben automatische Sicherungszeitpunkte für
ungespeicherte Puffer und der spätere KI-Annahmevertrag.

Der Editor bearbeitet den headerfreien Markdown-Body. Textänderungen
vererben vorhandene Metadaten; Attributänderungen sind eigene Aktionen.
Freigaben bleiben an konkrete gespeicherte Fassungen gebunden.

## Auswahl und KI-Annahme [markierungen-und-ki]

```yaml block-meta
updated: "2026-11-11 20"
status: draft
relations:
  - target: ui/EDITOR-UND-KI.md#ki-vorschlaege
    type: reference
    reason: Begrenzter Kontext und geprüfte Vorschläge statt vollständigem Chatmodell
```

Auswahlvorschläge benötigen Ausgangstext und eindeutig wiederauffindbare
Textstellen. Unicode-Codepoints und JavaScript-UTF-16-Indizes sind dabei
ausdrücklich zu unterscheiden. Dauerhafte Annotationen sind ein eigener
späterer Ausbau, keine Voraussetzung des einfachen Editors.

Offen sind Ergebnisformate für Text, Attribute und Blockaufteilung,
teilweise Annahme, Kontextlimits und die Lebensdauer der Aufträge.
Provider, Modell und Ausgangsstand müssen nachvollziehbar bleiben.
Doppelte Annahme oder Wiederholung darf nicht unbemerkt zusätzliche
Schreibvorgänge oder kostenpflichtige Anfragen erzeugen.

## Anschluss und Abnahme [anschluss-und-abnahme]

```yaml block-meta
updated: "2026-11-11 21"
status: draft
relations: []
```

Der erste Editoranschluss ist vorhanden. Attribute und KI-Vorschläge folgen
auf demselben Ressourcen- und Speichervertrag. Weitere Seitenvarianten
werden über die Navigation erprobt.

Zu prüfen sind Konflikte ohne Pufferverlust, Wiederherstellung, unveränderte
Originale und Header, Auswahlanker, Rechte, sichere Vorschlagsannahme und
getrennte Freigaben. Eine Abnahme des alten vollständigen Werkstattbackends
ist dafür nicht erforderlich.
