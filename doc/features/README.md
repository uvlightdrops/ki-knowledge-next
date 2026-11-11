---
title: "Implementierte Features"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: features
purpose: "Index der implementierten Funktionen und Bedienabläufe mit Verweisen auf ihre Architekturkonzepte."
created: "2026-11-09T18:13:00+01:00"
updated: "2026-11-11 19"
update_reason: "Konfigurierbaren Relationskatalog in der Featureübersicht erschlossen"
status: active
relations:
  - target: "ui/INDEX.md"
    type: child
    reason: "Umgesetzte Wiki-Ansichten mit Verweisen auf ihre Konzepte"
  - target: "IMPORT-UND-JOBS.md"
    type: child
    reason: "Dateisystem-Abbilder, Mengenübersichten und DB-Worker"
  - target: "TEMPLATE-UND-THEME.md"
    type: child
    reason: "Oberflächen, Arbeitsraum-Dark-Theme und originale UI-Demo"
  - target: "DOMAENEN.md"
    type: child
    reason: "Domänenverwaltung und persönliche Auswahl"
  - target: "NAVIGATION.md"
    type: child
    reason: "Gemeinsame Haupt- und Unternavigation"
  - target: "../architecture/README.md"
    type: reference
    reason: "Modellentscheidungen und Ausbaukonzepte zu den Features"
  - target: "../README.md"
    type: parent
    reason: "Zentraler Einstieg in die Projektdokumentation"
  - target: "IMPORT-PIPELINES-AND-DRAFTS.md"
    type: child
    reason: "Implementierte Formatadapter, Importläufe und Ausgabe"
  - target: "QUELLEN-UND-TEXTWERKSTATT.md"
    type: child
    reason: "Registrierung, Editor und Revisionshistorie"
  - target: "KONFIGURATION-UND-START.md"
    type: child
    reason: "YAML-Konfiguration und lokaler Betrieb"
---

# Features

## Überblick [feature-overview]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations: []
```

`features/` beschreibt den implementierten Iststand: was Nutzer und
Administratoren heute tun können, wie sie es bedienen und welche Grenzen
gelten. `architecture/` enthält Modellentscheidungen, Begründungen und
Ausbaukonzepte. Beide Seiten sind über gegenseitige YAML-Relationen und
Links verbunden; geplante Fähigkeiten werden nicht als verfügbar beschrieben.
`active` bezeichnet eine gepflegte Beschreibung, nicht Produktionsreife.

## Featureübersicht [feature-documents]

```yaml block-meta
updated: "2026-11-11 19"
status: active
relations: []
```

| Dokument | Status | Zweck | Semantische Blöcke |
|---|---|---|---|
| [Wiki-UI](ui/INDEX.md) | active | Vorhandene Wiki-Ansichten und Grenzen des Konzeptanschlusses | wiki-ui |
| [Importpipelines und Entwürfe](IMPORT-PIPELINES-AND-DRAFTS.md) | active | Vorhandene Formatadapter, Laufstatus und HTML-/ZIP-Ausgabe | scope, import-prototype, format-adapters, pipeline-lifecycle, … |
| [Quellen und Textwerkstatt](QUELLEN-UND-TEXTWERKSTATT.md) | active | Bereitstellung, Registrierung, headerfreier Editor und Historie | einstieg, quellen-registrieren, markdown-zerlegen, text-bearbeiten, … |
| [Konfiguration und lokaler Start](KONFIGURATION-UND-START.md) | active | YAML-Layer, Relationspresets, Startwege und Readiness | konfiguration, prioritaet-und-pfade, relationenkatalog, lokaler-start, readiness, grenzen |
| [Templates und Theme](TEMPLATE-UND-THEME.md) | active | Django-Shells, dunkler Arbeitsraum und originale UI-Demo | oberflaechen-und-django, arbeitsraum-theme, textwerkstatt-demo |
| [Domänenverwaltung und persönliche Auswahl](DOMAENEN.md) | active | Domänen anlegen, auswählen und ins Wissenswiki einbinden | domaenen-verwalten, aktive-domaene, hostintegration |
| [Navigation](NAVIGATION.md) | active | Hauptbereiche mit Unternavigation und kontextbezogenen Links | gruppierte-navigation |
| [Import und Jobs](IMPORT-UND-JOBS.md) | active | Batchauswahl, Dateimengen, immutable Ablage und DB-Worker | ablauf-und-batch, ablage-und-browsing, listen-und-zaehlwerte, worker-und-fehler |
