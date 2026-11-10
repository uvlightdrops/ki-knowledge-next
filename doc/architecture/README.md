---
title: "Architekturkonzepte"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Index der konzeptionellen Architekturentscheidungen und Systemgrenzen von ki-knowledge-next."
created: "2026-11-09T18:13:00+01:00"
updated: "2026-11-10T07:47:00+01:00"
update_reason: "Konzept zu Dokumentknoten und Attributebenen aufgenommen"
status: active
semantic_blocks:
  - architecture-overview
  - decision-documents
relations:
  - target: "DOKUMENTE-UND-BLOCKATTRIBUTE.md"
    type: child
    reason: "Semantik von Dokumenten, Abschnitten und Attributherkunft im Netz"
  - target: "../README.md"
    type: parent
    reason: "Zentraler Einstieg in die Projektdokumentation"
  - target: "KNOWLEDGE-DOMAIN-AND-LIFECYCLE.md"
    type: child
    reason: "Fachliches Modell der Domäne und ihres Lebenszyklus"
  - target: "CMS-AND-PUBLISHING.md"
    type: child
    reason: "Einordnung von CMS und Ausgabeformaten"
---

# Architektur

## Überblick [architecture-overview]

Die Architekturkonzepte halten Produktgrenzen und offene Entscheidungen fest.
Sie bauen auf dem frischen Django-Projekt und der eingebundenen
Wissenswiki-App auf, ohne historische Implementierungen des Vorgängerprojekts
ungeprüft als Zielarchitektur zu übernehmen.

## Konzepte und Entscheidungen [decision-documents]

| Dokument | Status | Zweck | Semantische Blöcke |
|---|---|---|---|
| [Wissensdomäne und Lebenszyklus](KNOWLEDGE-DOMAIN-AND-LIFECYCLE.md) | draft | Domänen, Aufnahme, Entwürfe und Veröffentlichung | domain-boundary, lifecycle, collaboration, publishing, current-and-target, open-questions |
| [CMS und Veröffentlichung](CMS-AND-PUBLISHING.md) | draft | Abgrenzung von Redaktion, Wagtail und statischem Export | publishing-model, editorial-interface, wagtail-assessment, recommendation, decision-gates |
| [Dokumente und Blockattribute](DOKUMENTE-UND-BLOCKATTRIBUTE.md) | draft | Dokumentknoten, Einleitung, Attributherkunft und Anzeige-Presets | ausgangspunkt, bestehendes-verhalten, dokument-und-abschnitt, attributebenen, … |
