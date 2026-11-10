---
title: "Featurekonzepte"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: features
purpose: "Index der fachlichen Features, Abläufe und Anforderungen für ki-knowledge-next."
created: "2026-11-09T18:13:00+01:00"
updated: "2026-11-09T18:13:00+01:00"
update_reason: "Featureindex für die ersten Produktanforderungen angelegt"
status: active
semantic_blocks:
  - feature-overview
  - feature-documents
relations:
  - target: "../README.md"
    type: parent
    reason: "Zentraler Einstieg in die Projektdokumentation"
  - target: "IMPORT-PIPELINES-AND-DRAFTS.md"
    type: child
    reason: "Erste Featureanforderungen zu Import, Entwurf und Ausgabe"
---

# Features

## Überblick [feature-overview]

Featuredokumente beschreiben, was Nutzer mit der Anwendung tun können und
welche fachlichen Regeln dabei gelten. Implementierungsdetails und offene
Technologieentscheidungen gehören in die verlinkten Architekturkonzepte.

## Featureübersicht [feature-documents]

| Dokument | Status | Zweck | Semantische Blöcke |
|---|---|---|---|
| [Importpipelines und Entwürfe](IMPORT-PIPELINES-AND-DRAFTS.md) | draft | Quellenformate aufnehmen, in nachvollziehbaren Schritten verarbeiten und Ergebnisse kontrolliert freigeben | scope, format-adapters, pipeline-lifecycle, drafts-and-review, failure-handling, static-output |
