---
title: "Dokumentation von ki-knowledge-next"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: documentation-index
purpose: "Einstieg in das gemeinsam entwickelte Produktkonzept und die Feature-Beschreibungen. Dieses Verzeichnis ist zugleich die Markdown-Quelle der Dokumentationsdomäne in der Site."
created: "2026-11-09T18:13:00+01:00"
updated: "2026-11-11 20"
update_reason: "Offene Übernahmekarte, Deploymententwurf und Mini-TODO-Ausnahme erschlossen"
status: active
relations:
  - target: "deployment/README.md"
    type: child
    reason: "Betriebsgrundlagen und Uberspace-Hostanleitungen"
  - target: "requirements/TODO-INDEX.md"
    type: child
    reason: "Geplante Änderungen und offene Anforderungen"
  - target: "architecture/QUELLEN-UND-TEXTWERKSTATT.md"
    type: reference
    reason: "Bereitstellung, Quellenaufnahme und versionierte Redaktion"
  - target: "../README.md"
    type: reference
    reason: "Projektaufbau und Startanleitung"
  - target: "architecture/README.md"
    type: child
    reason: "Architekturkonzepte und noch offene Technologieentscheidungen"
  - target: "features/README.md"
    type: child
    reason: "Fachliche Anforderungen und Nutzerabläufe"
  - target: "architecture/ALTREPO-UEBERNAHME.md"
    type: reference
    reason: "Einstieg in die Bewertung wiederverwendbarer Altprojekt-Bausteine"
---

# ki-knowledge-next Dokumentation

## Einstieg [starting-point]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations: []
```

Diese Dokumente beschreiben das Zielbild und die Features von
ki-knowledge-next. Sie unterscheiden ausdrücklich zwischen dem heutigen
Projektstand, einem gemeinsam zu prüfenden Vorschlag und einer bereits
getroffenen Entscheidung. Änderungen am Konzept sind nach dem Speichern Teil
der lokalen „Dokumentation“-Domäne und werden von der Site als Markdown
eingelesen.

## Anforderungen [requirements-index]

```yaml block-meta
updated: "2026-11-11 15"
status: active
relations: []
```

[TODO-Index](requirements/TODO-INDEX.md), gegliedert nach UI, Import,
Wissen intern, Ausgabe und Dokumentation.
Einfache passende Punkte sollen eigenständig auch begleitend zu anderen
Aufgaben umgesetzt werden. Komplexere
Themen erhalten zunächst ein verlinktes Konzept; die Hinweise im Index
bestimmen den jeweiligen Arbeitsrahmen.

## Architektur [architecture-index]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations: []
```

| Dokument | Status | Zweck | Semantische Blöcke |
|---|---|---|---|
| [UI-Konzepte](architecture/ui/README.md) | active | Wissenswiki als Arbeitsumgebung und Komposition über verknüpfte Ansichten | ui-konzepte |
| [Wissensdomäne und Lebenszyklus](architecture/KNOWLEDGE-DOMAIN-AND-LIFECYCLE.md) | draft | Domänenmodell, Quellenaufnahme, Entwürfe und Veröffentlichung | domain-boundary, lifecycle, collaboration, publishing, current-and-target, open-questions |
| [CMS und Veröffentlichung](architecture/CMS-AND-PUBLISHING.md) | draft | Wagtail-Einordnung und statische Ausgabe | publishing-model, editorial-interface, wagtail-assessment, recommendation, decision-gates |
| [Dokumente und Blockattribute](architecture/DOKUMENTE-UND-BLOCKATTRIBUTE.md) | draft | Semantik von Dokumenten, Abschnitten und Attributebenen im Netz | ausgangspunkt, bestehendes-verhalten, dokument-und-abschnitt, attributebenen, … |
| [Übernahme aus dem Altprojekt](architecture/ALTREPO-UEBERNAHME.md) | active | Offene Übernahmebereiche und Verweise auf vorhandene Grundlagen | auftrag-und-befund, uebernahmekarte, modellgrenzen, bereinigung, reihenfolge, nachweise-und-grenzen |
| [Quellen und Textwerkstatt](architecture/QUELLEN-UND-TEXTWERKSTATT.md) | active | Implementiertes Herkunfts- und Revisionsmodell mit getrenntem YAML-Header | modellentscheidung, bereitstellung-und-quelle, zerlegung-und-ausgangsstand, yaml-und-editor, … |

## Features [feature-index]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations: []
```

| Dokument | Status | Zweck | Semantische Blöcke |
|---|---|---|---|
| [Importpipelines und Entwürfe](features/IMPORT-PIPELINES-AND-DRAFTS.md) | active | Implementierte Formatadapter, Laufzustände und HTML-/ZIP-Ausgabe | scope, import-prototype, format-adapters, pipeline-lifecycle, … |
| [Quellen und Textwerkstatt](features/QUELLEN-UND-TEXTWERKSTATT.md) | active | Registrierung, Zerlegung, headerfreier Editor und Historie | einstieg, quellen-registrieren, markdown-zerlegen, text-bearbeiten, … |
| [Konfiguration und lokaler Start](features/KONFIGURATION-UND-START.md) | active | YAML-Layer, Startwege und Readiness | konfiguration, prioritaet-und-pfade, lokaler-start, readiness, grenzen |

## Deployment [deployment]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations: []
```

[Deployment](deployment/README.md) enthält gemeinsame Betriebsgrundlagen
und getrennte Uberspace-7-/8-Anleitungen. Produktionsvoraussetzungen und
manuelle Betriebsabläufe stehen in den Grundlagen; noch fehlende Integration
steht im [Deploymententwurf](deployment/ENTWURF.md).

## Arbeitsprinzipien [working-principles]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations: []
```

- `requirements/` sammelt geplante Änderungen und noch offene Anforderungen.
  Einfache passende Punkte dürfen gemäß Index eigenständig umgesetzt werden;
  komplexe Themen erhalten klickbare Konzeptverweise.
- `features/` dokumentiert implementierte Funktionen, Bedienung und bekannte
  Grenzen; `architecture/` dokumentiert Modellentscheidungen, Begründungen
  und Ausbaukonzepte. Feature und Konzept bilden gegenseitige YAML-Relationen
  und Links, statt dieselben Abläufe doppelt zu erklären.
- `active` bedeutet gepflegter Dokumentationsstand, nicht Produktionsreife.
  Nicht implementierte Fähigkeiten werden ausdrücklich als solche benannt.
- Jeder H2-Block trägt direkt unter seiner Überschrift einen sichtbaren
  `yaml block-meta`-Abschnitt mit eigenem `updated`, `status` und `relations`.
  Diese Werte werden nicht zusätzlich im Dateiheader gepflegt. Die
  Überschrift trägt die stabile ID; normale YAML-Beispiele sind keine
  Blockmetadaten. Die strukturierte Auswertung dieses lokalen Formats im
  Wissensnetz ist noch ein eigener Implementierungsschritt.
  Der kurze [TODO-Zettel](requirements/TODO-INDEX.md) ist davon ausgenommen;
  dort genügen Überschriften, Listenpunkte und klickbare Konzeptverweise.
- Quelldatei, importierter Inhalt, Entwurf und veröffentlichte Ausgabe sind
  unterschiedliche Zustände und dürfen nicht stillschweigend ineinander
  übergehen.
- Formatadapter und Verarbeitungsschritte sollen austauschbar bleiben; ein
  Importer darf keine redaktionelle Freigabe vortäuschen.
- KI-Ergebnisse bleiben prüfbare Vorschläge, bis ein Mensch sie annimmt.
- Produktanforderungen und Technologieentscheidungen werden gemeinsam
  weiterentwickelt. Als „draft“ markierte Inhalte sind keine stillschweigend
  beschlossene Roadmap.
