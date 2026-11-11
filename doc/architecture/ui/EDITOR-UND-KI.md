---
title: "Markdown-Editor und KI"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Beschreibt den editorzentrierten Arbeitsraum, einfache Sicherungsstände und kontextbezogene KI-Vorschläge als noch auszugestaltenden UI-Entwurf."
created: "2026-11-11 20"
updated: "2026-11-11 21"
update_reason: "Implementierten Editoreinstieg verlinkt und offene Sicherungsfragen eingegrenzt"
status: draft
relations:
  - target: ../../features/QUELLEN-UND-TEXTWERKSTATT.md#text-bearbeiten
    type: reference
    reason: Implementierter Editor mit zuschaltbarer Gliederungsnavigation
  - target: README.md
    type: parent
    reason: UI-Konzepte
---

# Markdown-Editor und KI

## Editor und zuschaltbare Ansichten [arbeitsraum]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
  - target: ../../features/QUELLEN-UND-TEXTWERKSTATT.md#einstieg
    type: reference
    reason: Bereits vorhandene Bearbeitungsabläufe der Textwerkstatt
  - target: WISSENSWIKI.md#local-workspace
    type: reference
    reason: Auswahl und Relationsvergleich als ergänzende Arbeitsmodi
  - target: ../TEXTWERKSTATT-VERTRAG.md#demo-und-ziel
    type: reference
    reason: Verbleibender technischer Anschluss an Next
```

**Textwerkstatt** bezeichnet aus Nutzersicht die zusammenhängenden
Bearbeitungsabläufe: Texte schreiben und korrigieren, Attribute pflegen,
Beziehungen bestimmen, Inhalte gliedern und KI-Vorschläge prüfen.
Der Begriff benennt weder ein bestimmtes Widget noch eine technische
Komponente, Speicherung oder ausschließlich die alte Werkstatt-Demo.
Einzelne Ansichten werden nach ihrer Aufgabe benannt, etwa Editor,
Vergleich oder Beziehungen.

Der Markdown-Editor bildet den Kern. Bubble-Netz als Navigation, Attribute,
zweiter Text und KI-Bereich werden je nach Aufgabe geöffnet oder geschlossen.
Die Textauswahl bleibt beim Umschalten erhalten. Zwei nebeneinanderliegende
Blöcke dienen dem Vergleich und Relationseditor, nicht als Pflichtlayout
jeder Textbearbeitung.

Der [einfache Einstieg](../../features/QUELLEN-UND-TEXTWERKSTATT.md#text-bearbeiten)
ist implementiert. Ein Attributbereich ergänzt später Dropdowns und Freitext;
Attributherkunft, zulässige Werte und die Trennung von Dokument- und
Blockattributen benötigen noch eine genauere Interaktionsgestaltung.

## Arbeitsstand und Sicherungen [sicherungsstaende]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
  - target: ../../features/QUELLEN-UND-TEXTWERKSTATT.md#historie-und-wiederherstellung
    type: reference
    reason: Vorhandene Speicherung und Wiederherstellung früherer Fassungen
  - target: ../TEXTWERKSTATT-VERTRAG.md#revisionen-yaml-konflikte
    type: reference
    reason: Interne Revisionen, Konfliktschutz und getrennte Freigabe
```

Die Bedienung zeigt einen aktuellen Arbeitsstand, Rückgängig im Editor
und wiederherstellbare Sicherungsstände. Vor größeren Ersetzungen und
KI-Übernahmen wird der vorherige gespeicherte Stand gesichert.
„Vorherigen Stand wiederherstellen“ ersetzt eine ständig sichtbare
Revisionsverwaltung; bei Bedarf sind weitere Sicherungen erreichbar.

Die vorhandenen Next-Revisionen tragen diese Sicherungen intern.
Veröffentlichte Fassungen bleiben vom Arbeitsstand getrennt.
Die Auswahl älterer gespeicherter Stände ist im Editor angeschlossen.
Speicherintervalle, Sicherung ungespeicherter Puffer und Aufbewahrungsgrenzen
sind noch festzulegen.

## Kontext und Vorschlagsarbeit [ki-vorschlaege]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations:
  - target: ../KONFIGURATION-UND-KI.md#ki-funktionskarte
    type: reference
    reason: Gemeinsame Provideranbindung und spätere KI-Fähigkeiten
  - target: ../TEXTWERKSTATT-VERTRAG.md#markierungen-und-ki
    type: reference
    reason: Ausgangsstand, Auswahlanker und sichere Annahme
  - target: WISSENSWIKI.md#conversation-and-proposals
    type: reference
    reason: Weiterführendes Gespräch als gesonderter Ausbau
```

Ein Auftrag besteht aus Vorgabe, ausgewählter Textstelle oder ganzem Text
und ausdrücklich hinzugefügtem Kontext. Weitere Blöcke und Attribute werden
sichtbar ausgewählt, nicht automatisch als vollständiger Domänenchat
übergeben. Vor dem Senden sind Kontext und Provider erkennbar.
Die Anbindung verwendet `ki-core` und die bestehende YAML-Auflösung;
erster Anschluss ist der bewährte OpenAI-Weg.

Ein Vorschlag steht neben dem Original und kann geändert, ganz oder
teilweise übernommen, verworfen oder mit einer weiteren Vorgabe bearbeitet
werden. Ein persistenter allgemeiner Chat ist keine Voraussetzung.
Providerfehler und ungültige Ergebnisse bleiben sichtbar.

Texterstellung und Korrektur liefern Textvorschläge. Schlagworte liefern
Attributvorschläge; semantische Aufteilung liefert prüfbare Blockgrenzen
und Inhalte. Neue Blöcke entstehen erst nach ausdrücklicher Bestätigung.
Annahme prüft den Ausgangsstand und verändert keine veröffentlichte Fassung.

## Spielerische Seitenentwürfe [seitenentwuerfe]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations: []
```

Oberflächen werden zunächst als eigenständige, veränderbare Seitenvarianten
erprobt. Jede angelegte Variante erhält vorläufig einen klar bezeichneten
Eintrag in der gemeinsamen Navigation, damit sie im normalen Arbeitsfluss
aufgerufen und verglichen werden kann.

Die Varianten beginnen beim Editor mit optionalem Netz und können Attribute,
Vergleich oder KI unterschiedlich anordnen. Demo-Daten und echte
Schreibaktionen sind unterscheidbar. Aus einer Variante folgt weder ein
dauerhafter Menüpunkt noch eine zweite Speicherung derselben Inhalte.
Die endgültige Gestaltung wird aus der gemeinsamen Erprobung abgeleitet.

Die erste echte Editorvariante ist als „Editor · Entwurf“ in INTERN
erreichbar. Weitere Seitenvarianten bleiben offen.
