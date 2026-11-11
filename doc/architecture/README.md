---
title: "Architekturkonzepte"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Index der konzeptionellen Architekturentscheidungen und Systemgrenzen von ki-knowledge-next."
created: "2026-11-09T18:13:00+01:00"
updated: "2026-11-11 20"
update_reason: "Technischen Textwerkstattvertrag auf einfachen Editoranschluss eingegrenzt"
status: active
relations:
  - target: "ui/README.md"
    type: child
    reason: "Fachliche UI-Grundlagen und Interaktionskonzepte"
  - target: "CONTENT-MODELL.md"
    type: child
    reason: "Graphenmodell und kontextbezogene Zusammenstellungen"
  - target: "IMPORT-UND-JOBS.md"
    type: child
    reason: "Getrennte Batches, Jobs, Versuche und immutable Dateisystem-Abbilder"
  - target: "TEXTWERKSTATT-VERTRAG.md"
    type: child
    reason: "Originale UI-Demo und erforderliche Next-Vertragsänderungen"
  - target: "../features/README.md"
    type: reference
    reason: "Iststand und Bedienabläufe zu den Architekturkonzepten"
  - target: "QUELLEN-UND-TEXTWERKSTATT.md"
    type: child
    reason: "Bereitstellung, registrierte Originale, immutable Extraktion und Revisionslinie"
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
  - target: "ALTREPO-UEBERNAHME.md"
    type: child
    reason: "Übernahmekarte und Bereinigung des Altbestands"
  - target: "KONFIGURATION-UND-KI.md"
    type: child
    reason: "Schemaauswahl und vollständiger KI-Funktionsumfang"
  - target: "../deployment/README.md"
    type: reference
    reason: "Betriebsgrundlagen, Zielhostanleitungen und offene Integration"
  - target: "AUSGABE-UND-PUBLIKATION.md"
    type: child
    reason: "Komposition von Ressourcen zu Sites und Downloads"
---

# Architektur

## Überblick [architecture-overview]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations: []
```

Die Architekturkonzepte halten Produktgrenzen und offene Entscheidungen fest.
Sie bauen auf dem frischen Django-Projekt und der eingebundenen
Wissenswiki-App auf, ohne historische Implementierungen des Vorgängerprojekts
ungeprüft als Zielarchitektur zu übernehmen.
Modellverträge und ihre Begründung bleiben hier; implementierte Bedienabläufe
stehen im [Featureindex](../features/README.md). Die zugehörigen Konzepte und
Features verweisen gegenseitig aufeinander. Kurze Standhinweise im Konzept
ersetzen keine Featurebeschreibung.

## Konzepte und Entscheidungen [decision-documents]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations: []
```

| Dokument | Status | Zweck | Semantische Blöcke |
|---|---|---|---|
| [UI-Konzepte](ui/README.md) | active | Wiki-Arbeitsumgebung und Bearbeitung von Zusammenstellungen | ui-konzepte |
| [Content-Modell](CONTENT-MODELL.md) | active | Ressourcen, typisierte Relationen und gespeicherte Zusammenstellungen | graph-und-perspektiven, ressourcen-und-relationen, zusammenstellungen, markdown-und-revisionen, app-und-grenzen |
| [Wissensdomäne und Lebenszyklus](KNOWLEDGE-DOMAIN-AND-LIFECYCLE.md) | draft | Domänen, Aufnahme, Entwürfe und Veröffentlichung | domain-boundary, lifecycle, collaboration, publishing, current-and-target, open-questions |
| [CMS und Veröffentlichung](CMS-AND-PUBLISHING.md) | draft | Abgrenzung von Redaktion, Wagtail und statischem Export | publishing-model, editorial-interface, wagtail-assessment, recommendation, decision-gates |
| [Dokumente und Blockattribute](DOKUMENTE-UND-BLOCKATTRIBUTE.md) | draft | Dokumentknoten, Einleitung, Attributherkunft und Anzeige-Presets | ausgangspunkt, bestehendes-verhalten, dokument-und-abschnitt, attributebenen, … |
| [Übernahme aus dem Altprojekt](ALTREPO-UEBERNAHME.md) | active | Offene Übernahmebereiche und führende Modellverträge | auftrag-und-befund, uebernahmekarte, modellgrenzen, bereinigung, reihenfolge, nachweise-und-grenzen |
| [Quellen und Textwerkstatt](QUELLEN-UND-TEXTWERKSTATT.md) | active | Herkunft, unveränderliche Extraktion und headerfreie Revisionen | modellentscheidung, bereitstellung-und-quelle, zerlegung-und-ausgangsstand, yaml-und-editor, … |
| [Konfiguration und KI](KONFIGURATION-UND-KI.md) | draft | YAML-Wizard, Schemakern, KI-Fähigkeiten und Übernahmebedingungen | konfigurationsentscheidung, schemaauswahl, wizard-und-zustaendigkeit, ki-funktionskarte, ki-bereinigung, abnahme-und-quellen |
| [Ausgabe und Publikation](AUSGABE-UND-PUBLIKATION.md) | draft | Ressourcenkomposition, eingebettete/autarke Sites und Baumexport bis PDF | ausgabebestand, publikationskomposition, formate-und-umfang, tiefe-baeume, generator-und-cms, pdf-und-druck, bereinigung-und-abnahme |
| [Textwerkstatt-Vertrag](TEXTWERKSTATT-VERTRAG.md) | draft | Offene Rechte-, Speicher- und Auswahlverträge des einfachen Editors | demo-und-ziel, identitaet-und-rechte, revisionen-yaml-konflikte, markierungen-und-ki, anschluss-und-abnahme |
| [Import und Jobs](IMPORT-UND-JOBS.md) | active | Dateisystem-Abbilder, DB-Queue und Worker-Recovery | modell-und-grenzen, dateisystem-vertrag, worker-und-zustaende, ansichten-und-rechte |

Betriebsgrundlagen, Hostanleitungen und offene Produktionsintegration stehen
im [Deploymentordner](../deployment/README.md).
