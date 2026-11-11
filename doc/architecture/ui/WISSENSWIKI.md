---
title: "Wissenswiki als Arbeitsumgebung"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Beschreibt die fachlichen UI-Grundlagen für das Entwickeln, Vergleichen und Zusammenstellen von Wissensblöcken."
created: "2026-11-11T15:18:00+01:00"
updated: "2026-11-11 20"
update_reason: "Editorzentrierten Einstieg vom Relationsvergleich und weiterführendem Gespräch getrennt"
status: active
semantic_blocks: [shared-work, blocks-and-relations, local-workspace, ordered-composition, conversation-and-proposals, agent-freedom]
sources:
  - repository: "ki-knowledge"
    revision: "9501cc5"
    path: "doc/architecture/WISSENSWIKI-ZUSAMMENARBEIT.md"
    blocks: [shared-work, blocks-and-relations, local-workspace, ordered-composition, conversation-and-proposals, agent-freedom]
  - repository: "ki-knowledge"
    revision: "9501cc5"
    path: "doc/architecture/WISSENSWIKI-TECHNIK.md"
    blocks: [boundary, storage-and-identity, editing, proposals, agent-runtime]
relations:
  - target: "../../features/TEMPLATE-UND-THEME.md"
    type: reference
    reason: "Implementierte Hosteinbindung und Oberflächen"
  - target: "README.md"
    type: parent
    reason: "UI-Konzepte"
  - target: "ZUSAMMENSTELLUNGEN.md"
    type: reference
    reason: "Konkretes Interaktionsmodell für Zusammenstellungen"
---

# Wissenswiki als Arbeitsumgebung

Die folgenden Grundlagen beschreiben das Interaktionsmodell. Gespräch,
KI-Vorschläge und Agenten sind Erweiterungsüberlegungen, keine verfügbaren
Funktionen. Die dateibasierte Wiki-Oberfläche und die DB-basierte
Textwerkstatt bleiben unterschiedliche Speicherzugänge.

## Gemeinsam Gedanken entwickeln [shared-work]

```yaml block-meta
updated: "2026-11-11 15"
status: active
relations: []
```

Die Arbeitsumgebung unterstützt das Formulieren von Gedanken, das Stellen von
Fragen und das Untersuchen von Unterschieden und Zusammenhängen. Sie legt
nicht fest, was wahr oder wichtig ist. Nähe und Verknüpfung von Inhalten
erleichtern die Auseinandersetzung, ersetzen aber keine fachliche Prüfung.

Lesen, Vergleichen und Verbinden sind zusammenhängende Tätigkeiten.
Inhaltsansichten und Netz sollten dieselbe Auswahl verwenden können, statt
bei jedem Wechsel erneut Suchbegriffe oder technische IDs zu verlangen.
Ein Gespräch kann später diesen sichtbaren Arbeitskontext verwenden, ohne
jede Nachricht automatisch in einen gespeicherten Block zu verwandeln.

## Blöcke und Beziehungen [blocks-and-relations]

```yaml block-meta
updated: "2026-11-11 15"
status: active
relations: []
```

Ein Block kann eine Idee, Frage oder Aussage ausdrücken. Die Oberfläche
unterscheidet eigenständig verfasste Blöcke, Dokumente und aus Quellen
erfasste Abschnitte. Eine Überschriftengrenze macht einen Textabschnitt
nicht automatisch zu fachlich bestätigtem Wissen.

Beim Verbinden bleiben Ausgang, Ziel, Typ und Richtung sichtbar. Eine
Relation ist eine Einordnung, kein Beweis. Herkunft, konkrete Quellstelle
und Textstand bleiben getrennt von dieser Einordnung nachvollziehbar.
Dokumentmetadaten erscheinen am Abschnitt als Kontext, nicht als dort
eigens gepflegte Eigenschaften.

## Arbeitsraum und Auswahl [local-workspace]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations:
  - target: EDITOR-UND-KI.md#arbeitsraum
    type: reference
    reason: Editor als Kern mit zuschaltbarem Netz und Vergleich
  - target: "../../features/ui/INDEX.md#wiki-ui"
    type: reference
    reason: "Umgesetzter Teil des Arbeitsraumkonzepts im Next-Host"
  - target: "../../../../wissenswiki-core/doc/UI-ARBEITSRAUM.md#arbeitsraum"
    type: reference
    reason: "Vorhandene Blockbearbeitung und Zweierauswahl im Core"
  - target: "../../../../wissenswiki-core/doc/UI-WISSENSNETZ.md#wissensnetz"
    type: reference
    reason: "Vorhandene Netz-, Inhalts- und Attributansichten im Core"
  - target: "../../features/TEMPLATE-UND-THEME.md#oberflaechen-und-django"
    type: reference
    reason: "Vorhandene gemeinsame Wiki-Shell und Hostadapter"
  - target: "ZUSAMMENSTELLUNGEN.md#ansichten"
    type: reference
    reason: "Auswahl und Inhaltsansichten im Zusammenstellungskontext"
```

Eine durchsuchbare Bestandsansicht erschließt Inhalte; zwei Inhaltsbereiche
ermöglichen das Gegenüberstellen von Texten. Der Mensch wählt die
Relationsendpunkte und benennt ihren Zusammenhang. Bei wenig Platz bleiben
die Aufgaben erreichbar, auch wenn Bereiche untereinander oder wechselweise
gezeigt werden.

Die Zweierauswahl passt zum Vergleich und zur gerichteten Beziehung. Eine
Zusammenstellung benötigt zusätzlich eine aktive Zusammenstellung und eine
Auswahl ihrer konkreten Platzierungen; diese darf nicht mit Ausgang/Ziel
gleichgesetzt werden. Netz, Bestand, Inhalt und Attribute sind
zusammenwirkende Ansichten, kein vorausgesetztes allgemeines Widgetframework.

Der [Editorentwurf](EDITOR-UND-KI.md#arbeitsraum) macht die Textbearbeitung
zum Ausgangspunkt; Netz, Vergleich und Attribute werden nach Bedarf ergänzt.

## Ein längerer Text aus Teilen [ordered-composition]

```yaml block-meta
updated: "2026-11-11 17"
status: active
relations:
  - target: "../../features/ui/INDEX.md#wiki-ui"
    type: reference
    reason: "Abgrenzung der vorhandenen parts-Liste vom Next-Zusammenstellungseditor"
  - target: "../../../../wissenswiki-core/doc/UI-ARBEITSRAUM.md#arbeitsraum"
    type: reference
    reason: "Vorhandene geordnete Textteile im dateibasierten Core"
  - target: "ZUSAMMENSTELLUNGEN.md#arbeitskontext"
    type: reference
    reason: "Eigenständige Platzierungen statt globaler Blockordnung"
```

Ein Essay oder Buch kann als Ganzes mit Bestandteilen in einer bestimmten
Reihenfolge betrachtet werden. Dieselben Blöcke können anderswo anders
angeordnet sein oder mehrfach vorkommen. Eine Nachbarschaft behauptet
weder Begründung noch Zustimmung; Gliederung und fachliche Beziehungen
bleiben getrennt.

Die alte `parts`-Liste an einem Wiki-Block veranschaulicht geordnete Teile,
ist aber nicht das Speichermodell für Next-Zusammenstellungen. Dort ist
die Zusammenstellung eine eigene Ressource; Elternzuordnung, Reihenfolge
und Querverweise gehören zu ihren Platzierungen. Inhalt und Revision
bleiben beim referenzierten Dokument beziehungsweise Block.

## Gespräch und Vorschläge [conversation-and-proposals]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations:
  - target: EDITOR-UND-KI.md#ki-vorschlaege
    type: reference
    reason: Begrenzte Vorschlagsaufträge als erster KI-Einstieg
```

Der erste KI-Einstieg folgt den
[begrenzten Vorschlagsaufträgen](EDITOR-UND-KI.md#ki-vorschlaege).
Ein allgemeines Gespräch mit dauerhaftem Verlauf bleibt ein gesonderter
Ausbau. Dafür sind Kontextauswahl, Speicherung und Lebensdauer noch
festzulegen; es ist keine Voraussetzung der Textbearbeitung.

## Handlungsspielraum der Agenten [agent-freedom]

```yaml block-meta
updated: "2026-11-11 15"
status: active
relations: []
```

Ein künftiger Agent kann auf ausdrückliche Anfrage antworten oder innerhalb
eines begrenzten Auftrags selbstständig Vorschläge erkunden. Arbeitsbereich,
erlaubte Aktionen, Kosten beziehungsweise Aufrufbudget, Abbruch und
Fehlerzustände müssen sichtbar und begrenzbar sein.

Mehr Handlungsspielraum bedeutet nicht automatisch Schreibzugriff auf
bestätigtes Wissen. Als Ausgangsmodell erzeugen Agenten prüfbare Entwürfe;
weitergehende Autonomie benötigt eine eigene Entscheidung. Verfügbare
Entwicklungsagenten sind keine bereits integrierte Laufzeit der Anwendung.
