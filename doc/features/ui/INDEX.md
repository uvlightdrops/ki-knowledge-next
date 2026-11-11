---
title: "Umgesetzte Wiki-UI"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: features
purpose: "Verknüpft die vorhandene Wiki-Oberfläche mit ihren UI-Konzepten und beschreibt die Grenze der Umsetzung."
created: "2026-11-11 17"
updated: "2026-11-11 20"
update_reason: "Bereinigte Markdown-Inhaltsansichten und Quelltextzugang beschrieben"
status: active
relations:
  - target: ../README.md
    type: parent
    reason: Index der implementierten Features
---

# Umgesetzte Wiki-UI

## Arbeitsraum und Wissensnetz [wiki-ui]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations:
  - target: ../../architecture/ui/RELATIONEN.md#betreiberkatalog
    type: depends-on
    reason: Alle freigegebenen Typen aus demselben Betreiberkatalog
  - target: ../../architecture/ui/WISSENSWIKI.md#local-workspace
    type: depends-on
    reason: Konzept der zusammenwirkenden Auswahl- und Inhaltsansichten
  - target: ../../architecture/ui/WISSENSWIKI.md#ordered-composition
    type: depends-on
    reason: Geordnete Teile als Vorläufer eigenständiger Zusammenstellungen
  - target: ../../../../wissenswiki-core/doc/UI-ARBEITSRAUM.md#arbeitsraum
    type: reference
    reason: Vorhandene dateibasierte Bearbeitung im Core
  - target: ../../../../wissenswiki-core/doc/UI-WISSENSNETZ.md#wissensnetz
    type: reference
    reason: Vorhandene Exploration und Vergleich im Core
```

Die Wiki-Oberfläche setzt das [Arbeitsraumkonzept](../../architecture/ui/WISSENSWIKI.md#local-workspace)
mit durchsuchbarem Bestand, zwei Bearbeitungsbereichen, Relationsendpunkten
und Inhaltsvergleich um. Das Wissensnetz ergänzt Auswahl, Filter und
Attributvergleich. Next verwendet diese gemeinsame Core-Oberfläche;
[Hosteinbindung und Theme](../TEMPLATE-UND-THEME.md) bleiben separat beschrieben.

Die Inhaltsansichten im Netz und die Bestandteile-Vorschau im Arbeitsraum
rendern Markdown einschließlich Tabellen und Codeblöcken. Der gemeinsame
Core-Renderer entfernt aktive HTML-Elemente und unsichere Linkziele.
Im Netz bleibt der Markdown-Quelltext aufklappbar; die Bearbeitungsfelder
im Arbeitsraum bleiben Quelltextfelder. Gespeicherte Inhalte werden nicht verändert.

Relationsauswahl und Schreibvalidierung verwenden den konfigurierten
Betreiberkatalog. Das Widget bietet alle freigegebenen Typen unabhängig von
ihrem bisherigen Einsatz; gespeicherte nicht freigegebene Typen bleiben lesbar.

Die geordnete `parts`-Liste im dateibasierten Arbeitsraum verwirklicht das
Zusammenfügen von Textteilen, nicht den DB-basierten Zusammenstellungseditor.
Die zusätzlichen Platzierungsansichten aus dem
[Zusammenstellungskonzept](../../architecture/ui/ZUSAMMENSTELLUNGEN.md)
sind noch nicht angeschlossen. Gespräch, KI-Vorschläge und Agentenlaufzeit
aus den UI-Überlegungen sind ebenfalls keine verfügbaren Wiki-Funktionen.
