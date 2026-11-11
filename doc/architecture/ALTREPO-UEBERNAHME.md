---
title: "Übernahme aus dem Altprojekt"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Bündelt die noch offenen Übernahmeentscheidungen und verweist auf bestehende Modellverträge und umgesetzte Grundlagen."
created: "2026-11-10T20:55:00+01:00"
updated: "2026-11-11 20"
update_reason: "Erledigte Grundlagen durch Verweise ersetzt und offene Übernahmebereiche verdichtet"
status: active
relations:
  - target: README.md
    type: parent
    reason: Architekturindex
  - target: ../README.md
    type: reference
    reason: Projektdokumentation
  - target: KONFIGURATION-UND-KI.md
    type: child
    reason: Offene KI- und Runtime-Konfigurationsanbindung
  - target: ../deployment/ENTWURF.md
    type: reference
    reason: Verbleibende Produktionsintegration
  - target: AUSGABE-UND-PUBLIKATION.md
    type: child
    reason: Ressourcenbasierte Ausgabe und Publikation
  - target: DOKUMENTE-UND-BLOCKATTRIBUTE.md
    type: reference
    reason: Fachliche Dokument- und Blocksemantik
  - target: QUELLEN-UND-TEXTWERKSTATT.md
    type: reference
    reason: Herkunfts- und Revisionsvertrag
---

# Übernahme aus dem Altprojekt

## Übernahmegrundsatz [auftrag-und-befund]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations: []
```

Übernommen werden fachliche Fähigkeiten über gemeinsame Pakete und
abgegrenzte Adapter. Führend bleiben die Next-Ressourcen und Revisionen.
KI-Funktionsumfang, geeignete Betriebsmechanismen und ressourcenbasierte
Ausgabe werden weitergeführt; eine Kopie der gesamten Altanwendung ist
dafür nicht erforderlich.

Bereits vorhandene Grundlagen stehen in
[Konfiguration und Start](../features/KONFIGURATION-UND-START.md),
[Quellen und Textwerkstatt](../features/QUELLEN-UND-TEXTWERKSTATT.md),
[Import und Jobs](../features/IMPORT-UND-JOBS.md) und
[Wiki-UI](../features/ui/INDEX.md). Sie sind keine offenen Portierungsaufträge.

## Offene Übernahmebereiche [uebernahmekarte]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations: []
```

| Bereich | Verbleibender Anschluss | Konzept |
|---|---|---|
| KI-Redaktion | `ki-core`-Provider, Modellauswahl, Kontext und revisionsgebundene Vorschläge | [Konfiguration und KI](KONFIGURATION-UND-KI.md#ki-funktionskarte) |
| Runtime-Konfiguration | Schemafähiger Editor mit Rechten, Herkunft und Neustartgrenzen | [Wizard](KONFIGURATION-UND-KI.md#wizard-und-zustaendigkeit) |
| Suche und Erschließung | Embeddings, Retrieval, Quellenchat, Begriffe und Graphableitungen | [KI-Funktionskarte](KONFIGURATION-UND-KI.md#ki-funktionskarte) |
| Zusätzliche Quellenadapter | Nur benötigte Formate und Connectoren an vorhandene Jobs anschließen | [Quellenintegration](QUELLEN-UND-TEXTWERKSTATT.md#integration-des-altbestands) |
| Komposition und Ausgabe | Wiki-Zusammenstellungseditor, Siteauswahl, Sammeldokument/PDF und Publikationsziele | [UI](ui/ZUSAMMENSTELLUNGEN.md), [Ausgabe](AUSGABE-UND-PUBLIKATION.md) |
| Lernmaterial | Quiz, Karten, Glossar und Lernleitfaden an freigegebene Ressourcen binden | [Ausgabebestand](AUSGABE-UND-PUBLIKATION.md#ausgabebestand) |
| Produktionsbetrieb | Zielhostprofile, Wartungsautomatisierung und praktische Restore-Abnahme | [Deploymententwurf](../deployment/ENTWURF.md) |

Nextcloud/WebDAV und Jira bleiben optionale Connectoren. Wagtail ist eine
offene CMS-Adapterentscheidung; Federation/Sync bleibt ein späteres
eigenständiges Thema. Diese Bereiche sind keine Voraussetzungen für den
ersten KI-Redaktionsanschluss.

## Führende Modellverträge [modellgrenzen]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations: []
```

[Content-Modell](CONTENT-MODELL.md) definiert Ressourcen, Relationen,
revisionierte Gliederungen und eigenständige Zusammenstellungen.
[Quellen und Textwerkstatt](QUELLEN-UND-TEXTWERKSTATT.md) definiert
Originale, Extraktion, Revisionslinie und Freigabe.

Alt-Records werden an diese Identitäten und Stände angebunden.
Wiki-Dateibeziehungen und Next-DB-Kanten teilen inzwischen ihr Vokabular,
nicht automatisch ihre Speicherung oder Identität.
Suche und Embeddings bleiben erneuerbare Ableitungen; KI-Ergebnisse
werden als Vorschläge an einen ausdrücklichen Ausgangsstand gebunden.

## Anforderungen an Adapter [bereinigung]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations: []
```

Adapter erhalten explizite Konfiguration, Ressourcenbezüge und Rechte
statt alter Django-Imports oder freier Dateipfade. Fachlogik und geeignete
Fixtures werden gezielt übernommen; neue Schreibwege verwenden die
vorhandenen Revisionen, Freigaben und Jobverträge.

Für KI gelten zusätzlich die
[Übernahmebedingungen](KONFIGURATION-UND-KI.md#ki-bereinigung),
für Ausgabe die
[Abnahmekriterien](AUSGABE-UND-PUBLIKATION.md#bereinigung-und-abnahme).

## Nächste fachliche Anschlüsse [reihenfolge]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations: []
```

Die Konfigurations- und Revisionsgrundlagen erlauben als nächsten Schritt
den KI-Redaktionsanschluss: Texterstellung, Korrekturvorschläge, Schlagworte
und vorgeschlagene Blockaufteilung. Auswahl und konkrete Arbeitsaufträge
stehen im [TODO-Index](../requirements/TODO-INDEX.md).

Retrieval baut auf KI-Basis, erlaubtem Kontext und versionierten Indizes
auf. Ressourcenbasierte Ausgabe benötigt einen freigegebenen Inhalts-
und Strukturstand. Produktionsintegration kann getrennt vorbereitet
werden; ihre Freigabe setzt die praktische Betriebsabnahme voraus.

## Portierungsquellen [nachweise-und-grenzen]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations: []
```

Die Detailkonzepte verlinken die fachlich relevanten Altmodule und Tests.
Für den KI-Einstieg sind insbesondere
[`ki_core.chat`](../../../ki-core/src/ki_core/chat.py) und
[`workbench_proposals.py`](../../../ki-knowledge/ki_knowledge/django_site/workbench_proposals.py)
maßgeblich; für Betrieb der [Deploymententwurf](../deployment/ENTWURF.md).
Der jeweils installierte Paketstand muss vor einer Portierung geprüft
werden; die ursprüngliche Sichtung ersetzt keine aktuelle Integrationsabnahme.
