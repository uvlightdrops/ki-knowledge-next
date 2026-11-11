---
title: "UI-Konzepte"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Ordnet die Konzepte für Arbeitsoberflächen und ihre Verknüpfung mit dem Content-Modell."
created: "2026-11-11T15:18:00+01:00"
updated: "2026-11-11 20"
update_reason: "Editorzentrierten KI-Entwurf und temporäre Seitenvarianten aufgenommen"
status: active
relations:
  - target: EDITOR-UND-KI.md
    type: child
    reason: Markdown-Editor, Sicherungsstände und begrenzte KI-Aufträge
  - target: "RELATIONEN.md"
    type: child
    reason: "Relationenpresets und gemeinsamer Katalogvertrag"
  - target: "../README.md"
    type: parent
    reason: "Architekturübersicht"
  - target: "WISSENSWIKI.md"
    type: child
    reason: "Grundlagen der blockbezogenen Arbeitsumgebung"
  - target: "ZUSAMMENSTELLUNGEN.md"
    type: child
    reason: "Bearbeitung von Zusammenstellungen über Wiki-Ansichten"
---

# UI-Konzepte

## Übersicht [ui-konzepte]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations: []
```

`architecture/ui/` enthält Interaktionsmodelle und ihre Begründungen.
Implementierte Bedienung steht in `features/`; offene Anforderungen stehen
im [TODO-Index](../../requirements/TODO-INDEX.md). Dokumentstatus beschreibt
die Vollständigkeit des Konzepts, nicht dessen Umsetzung.

| Dokument | Status | Zweck | Semantische Blöcke |
|---|---|---|---|
| [Markdown-Editor und KI](EDITOR-UND-KI.md) | draft | Zuschaltbare Ansichten, Sicherungsstände, KI-Vorschläge und Seitenvarianten | arbeitsraum, sicherungsstaende, ki-vorschlaege, seitenentwuerfe |
| [Relationsvokabular](RELATIONEN.md) | active | Betreiberpresets, stabile Bedeutungen und erhaltender Katalogwechsel | betreiberkatalog |
| [Wissenswiki](WISSENSWIKI.md) | active | Gemeinsames Denken, Blockvergleich und Komposition als UI-Grundlagen | shared-work, blocks-and-relations, local-workspace, ordered-composition, … |
| [Zusammenstellungen bearbeiten](ZUSAMMENSTELLUNGEN.md) | draft | Auswahl, Platzierungen, Gliederung und Speicheranschluss | arbeitskontext, ansichten, bearbeitungsaktionen, relationen, speichern-und-konflikte, anschluss, abnahme |
