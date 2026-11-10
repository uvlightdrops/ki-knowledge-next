---
title: "Dokumentation von ki-knowledge-next"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: documentation-index
purpose: "Einstieg in das gemeinsam entwickelte Produktkonzept und die Feature-Beschreibungen. Dieses Verzeichnis ist zugleich die Markdown-Quelle der Dokumentationsdomäne in der Site."
created: "2026-11-09T18:13:00+01:00"
updated: "2026-11-10T07:47:00+01:00"
update_reason: "Konzept zu Dokumenten und Blockattributen verlinkt"
status: active
semantic_blocks:
  - starting-point
  - architecture-index
  - feature-index
  - working-principles
relations:
  - target: "../README.md"
    type: reference
    reason: "Projektaufbau und Startanleitung"
  - target: "architecture/README.md"
    type: child
    reason: "Architekturkonzepte und noch offene Technologieentscheidungen"
  - target: "features/README.md"
    type: child
    reason: "Fachliche Anforderungen und Nutzerabläufe"
---

# ki-knowledge-next Dokumentation

## Einstieg [starting-point]

Diese Dokumente beschreiben das Zielbild und die Features von
ki-knowledge-next. Sie unterscheiden ausdrücklich zwischen dem heutigen
Projektstand, einem gemeinsam zu prüfenden Vorschlag und einer bereits
getroffenen Entscheidung. Änderungen am Konzept sind nach dem Speichern Teil
der lokalen „Dokumentation“-Domäne und werden von der Site als Markdown
eingelesen.

## Architektur [architecture-index]

| Dokument | Status | Zweck | Semantische Blöcke |
|---|---|---|---|
| [Wissensdomäne und Lebenszyklus](architecture/KNOWLEDGE-DOMAIN-AND-LIFECYCLE.md) | draft | Domänenmodell, Quellenaufnahme, Entwürfe und Veröffentlichung | domain-boundary, lifecycle, collaboration, publishing, current-and-target, open-questions |
| [CMS und Veröffentlichung](architecture/CMS-AND-PUBLISHING.md) | draft | Wagtail-Einordnung und statische Ausgabe | publishing-model, editorial-interface, wagtail-assessment, recommendation, decision-gates |
| [Dokumente und Blockattribute](architecture/DOKUMENTE-UND-BLOCKATTRIBUTE.md) | draft | Semantik von Dokumenten, Abschnitten und Attributebenen im Netz | ausgangspunkt, bestehendes-verhalten, dokument-und-abschnitt, attributebenen, … |

## Features [feature-index]

| Dokument | Status | Zweck | Semantische Blöcke |
|---|---|---|---|
| [Importpipelines und Entwürfe](features/IMPORT-PIPELINES-AND-DRAFTS.md) | draft | Formatübergreifende Aufnahme, nachvollziehbare Pipeline und redaktionelle Freigabe | scope, format-adapters, pipeline-lifecycle, drafts-and-review, failure-handling, static-output |

## Arbeitsprinzipien [working-principles]

- Quelldatei, importierter Inhalt, Entwurf und veröffentlichte Ausgabe sind
  unterschiedliche Zustände und dürfen nicht stillschweigend ineinander
  übergehen.
- Formatadapter und Verarbeitungsschritte sollen austauschbar bleiben; ein
  Importer darf keine redaktionelle Freigabe vortäuschen.
- KI-Ergebnisse bleiben prüfbare Vorschläge, bis ein Mensch sie annimmt.
- Produktanforderungen und Technologieentscheidungen werden gemeinsam
  weiterentwickelt. Als „draft“ markierte Inhalte sind keine stillschweigend
  beschlossene Roadmap.
