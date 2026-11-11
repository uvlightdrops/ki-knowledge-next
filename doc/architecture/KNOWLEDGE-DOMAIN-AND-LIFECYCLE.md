---
title: "Wissensdomäne und Lebenszyklus"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Skizziert, wie Quellen in einer Domäne aufgenommen, geprüft, gemeinsam weiterentwickelt und als freigegebene Inhalte ausgegeben werden können."
created: "2026-11-09T18:13:00+01:00"
updated: "2026-11-11 15"
update_reason: "Domänenverweise auf die getrennte Featurebeschreibung umgestellt"
status: draft
relations:
  - target: "README.md"
    type: parent
    reason: "Architekturindex"
  - target: "../features/IMPORT-PIPELINES-AND-DRAFTS.md"
    type: reference
    reason: "Konkrete Anforderungen an Aufnahme, Verarbeitung und Freigabe"
  - target: "CMS-AND-PUBLISHING.md"
    type: reference
    reason: "Technologieoption für Redaktion und statische Ausgabe"
---

# Wissensdomäne und Lebenszyklus

## Domänengrenze [domain-boundary]

```yaml block-meta
updated: "2026-11-11 15"
status: active
relations:
  - target: ../features/DOMAENEN.md#domaenen-verwalten
    type: reference
    reason: Implementierte Domänenseite und Grenzen der persönlichen Auswahl
```

Eine Domäne ist ein zusammenhängender Arbeits- und Veröffentlichungsbereich
mit eigenen Quellen, Entwürfen, Beziehungen, Zugriffsrechten und Ausgaben.
`doc/` ist zunächst die Dokumentationsdomäne, in der wir das Produktkonzept
direkt in der Site erarbeiten. Die bestehenden Wissenswiki-Domänen bleiben
davon getrennte Eingaben, solange ihre Nutzung oder Migration nicht ausdrücklich
beschlossen ist.

Das Django-Projekt bindet bereits `wissenswiki-django` ein. Die
„Dokumentation“-Domäne zeigt standardmäßig auf dieses Repositorys `doc/`;
`KI_NEXT_DOC` kann den Quellordner für lokale Umgebungen überschreiben. Die
Markdown-Dateien sind dabei die lesbare Quelle, nicht bloß eine Kopie in einem
CMS-Datensatz.

Die [Domänenseite](../features/DOMAENEN.md) kann inzwischen
leere Datenbaum-Domänen anlegen und je Benutzer eine aktive Domäne speichern.
Diese Auswahl ist Navigationskontext, keine globale Aktivierung und keine
Zugriffskontrolle. Eigene Domänenrechte bleiben Zielbild; der gemeinsame
Arbeitsraum ist weiterhin unabhängig von Dokumentdomänen.

## Lebenszyklus [lifecycle]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations:
- target: ../features/IMPORT-PIPELINES-AND-DRAFTS.md#pipeline-lifecycle
  type: reference
  reason: Implementierter Ablauf zu diesem Konzept
```

Der fachliche Ablauf soll getrennte Zustände sichtbar machen:

1. **Quelle erfassen:** Datei hochladen, aus einem verbundenen Speicher
   übernehmen oder über einen expliziten Quellpfad registrieren.
2. **Verarbeiten:** Format erkennen, Inhalt auslesen und normalisieren; bei
   Bedarf OCR, Tabellen- oder Metadatenextraktion als eigene Schritte ausführen.
3. **Prüfen:** Ergebnis, Herkunft und Warnungen sichtbar machen; fehlerhafte
   oder unvollständige Extraktion nicht als fertiges Wissen ausgeben.
4. **Entwurf erstellen:** Inhalt redaktionell oder mit KI-Unterstützung
   strukturieren und gemeinsam bearbeiten.
5. **Freigeben:** Eine zuständige Person bestätigt eine konkrete Revision.
6. **Ausgeben:** Freigegebene Inhalte als Website oder anderes Format bauen.

Erfassung, Verarbeitung, redaktioneller Status und Veröffentlichung sind
getrennte Statusdimensionen. Beispielsweise bedeutet „Import erfolgreich“
nicht „inhaltlich geprüft“ und „gespeichert“ nicht „öffentlich“.

## Zusammenarbeit [collaboration]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations:
- target: ../features/IMPORT-PIPELINES-AND-DRAFTS.md#drafts-and-review
  type: reference
  reason: Implementierter Ablauf zu diesem Konzept
```

Eine gemeinsame Arbeitsoberfläche soll Inhalte hierarchisch ordnen, Entwürfe
und Revisionen nachvollziehbar machen und redaktionelle Arbeit mit anderen
Personen ermöglichen. Rollen, parallele Bearbeitung, Konfliktauflösung und
Freigaberechte müssen vor dem produktiven Mehrbenutzerbetrieb konkretisiert
werden.

KI kann beim Zusammenfassen, Strukturieren und Überarbeiten helfen. Sie
verändert keine freigegebene Revision stillschweigend: Änderungen werden als
prüfbarer Entwurf mit Bezug auf Ausgangsrevision und Quellen vorgelegt.

## Veröffentlichung [publishing]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations: []
```

Die fachliche Struktur einer Wissensdomäne soll nicht an eine einzelne
Weboberfläche gebunden sein. Aus freigegebenen Revisionen kann eine
hierarchische, statische HTML-Site gebaut werden. Navigation, URL-Pfade,
Quellennachweise und interne Links werden aus dem veröffentlichten
Strukturstand erzeugt. Ein Build erhält eine eindeutige Version, damit eine
ältere Ausgabe bei Bedarf wiederhergestellt werden kann.

Das CMS-Editorlebnis und der statische Webauftritt sind verschiedene Dinge:
Das CMS dient dem Erstellen, Prüfen und Freigeben; der Export ist ein
Publikationsartefakt und benötigt für die reine Lektüre keine laufende
Django- oder CMS-Instanz.

## Heute und Zielbild [current-and-target]

```yaml block-meta
updated: "2026-11-11 06"
status: draft
relations: []
```

**Heute:** Das Projekt ist ein Django-Hostprojekt mit SQLite,
Anmeldung/Admin und der eingebundenen Wissenswiki-App. Diese App kann
konfigurierte Markdown-Domänen lesen und Beziehungen separat speichern. Das
lokale `doc/` ist nun die Standardquelle der Dokumentationsdomäne. Im
Projekt-Setup ist Wagtail noch nicht enthalten. Die eigenständige
`knext.content`-App ergänzt inzwischen einen synchronen Importprototyp mit
Originalquellen, versionierten Entwürfen, expliziter Freigabe und statischem
HTML-/ZIP-Export. Details und Grenzen stehen im
[Import-Prototyp](../features/IMPORT-PIPELINES-AND-DRAFTS.md#import-prototyp-import-prototype).
Ein vollständiger Mehrbenutzer-Reviewworkflow und hierarchischer Site-Build
sind damit noch nicht umgesetzt.

**Zielbild / Vorschlag:** Die Anwendung ergänzt den Markdown-Wissenskern um
explizite Importadapter, Verarbeitungsläufe, Entwürfe, Revisionen,
Freigaberegeln und reproduzierbare Ausgabe. Das Datenmodell des Prototyps ist ein erster prüfbarer Implementierungsschritt,
nicht die abschließende Festlegung des Gesamtmodells. Eine
Die erste Hintergrundjob-Technologie ist nun ein separater Django-Worker
mit DB-Queue; siehe [Import und Jobs](IMPORT-UND-JOBS.md).

## Offene Fragen [open-questions]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations: []
```

- Welche Formate und Speicherquellen gehören in den ersten nutzbaren Import?
- Soll ein Import synchron starten, oder braucht der erste Umfang bereits
  eine warteschlangenbasierte Verarbeitung?
- Was ist die kleinste sinnvolle redaktionelle Einheit: Dokument, Abschnitt
  oder Wissensblock?
- Welche Personen dürfen Entwürfe bearbeiten, prüfen, freigeben und
  veröffentlichen?
- Welche Seiten und Metadaten erscheinen im statischen HTML, und wo wird es
  bereitgestellt?
- Ist Wagtail für Hierarchie und Workflow der beste erste Editor, oder genügt
  zunächst eine schlankere Django-Oberfläche?

Die aktuelle Einordnung von Wagtail und statischem Export steht in
[CMS und Veröffentlichung](CMS-AND-PUBLISHING.md); die Aufnahme- und
Entwurfsanforderungen sind unter
[Importpipelines und Entwürfe](../features/IMPORT-PIPELINES-AND-DRAFTS.md)
ausgeführt.
