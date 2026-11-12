---
title: "Navigation"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: features
purpose: "Beschreibt die gemeinsame Haupt- und Unternavigation der Anwendung."
created: "2026-11-11 15"
updated: "2026-11-12 05"
update_reason: "Breite Editorvariante als eigenen vorläufigen Einstieg ergänzt"
status: active
relations:
  - target: README.md
    type: parent
    reason: Index der implementierten Features
---

# Navigation

## Gruppierte Navigation [gruppierte-navigation]

```yaml block-meta
updated: "2026-11-12 05"
status: active
relations:
  - target: DOMAENEN.md#aktive-domaene
    type: reference
    reason: Persönliche Domänenauswahl im gemeinsamen Navigationsbereich
  - target: QUELLEN-UND-TEXTWERKSTATT.md#einstieg
    type: reference
    reason: Einstieg in Quellbestand und Textwerkstatt
```

Die gemeinsame Navigation erscheint auf Inhaltsseiten, im eingebetteten
Wissenswiki und in der Django-Administration. Sie bietet eine Hauptnavigation
und die Unternavigation des aktuellen Bereichs:

- **INPUT:** Inhalte und Importläufe, Quellen, Dateien und Jobs.
- **INTERN:** Werkstatt, Zusammenstellungen, Ressourcen, Beziehungstypen,
  Wissensnetz, Arbeitsraum und die Textwerkstatt-Demo. „Editor · Entwurf“
  öffnet vorläufig die Dokumentauswahl für die neue Editoransicht.
  „Editor breit · Entwurf“ öffnet die eigene Auswahl für die
  bildschirmbreite Variante; beide bearbeiten dieselben Inhalte.
  Zusammenstellungen,
  Ressourcen und Beziehungstypen behalten zusätzlich den Werkstattkontext.
- **OUTPUT:** „Statische Ausgabe“ öffnet `/content/output/` mit den
  HTML-Site-ZIP-Downloads der freigegebenen Domänen. Die persönliche
  Domänenwahl filtert die Übersicht. Bereich und Unternavigation sind
  auch ohne JavaScript aktiv; INPUT enthält keinen Exportblock mehr.
- **Administration:** Django-Administration, nur für Staff-Benutzer sichtbar.
- **Einstellungen:** Domänenverwaltung und Netz-Einstellungen.

Detail- und Aktionsrouten markieren ihren jeweiligen Bereich. Die
[Domänenauswahl](DOMAENEN.md#aktive-domaene) bleibt in der gemeinsamen
Navigation verfügbar; Wissensnetz und Netz-Einstellungen übernehmen den
aktiven Domänenkontext. Die primäre und sekundäre Leiste sind bei schmalen
Ansichten horizontal scrollbar; ein Tastatur-bedienbares Menü bietet
zusätzlich alle Bereiche und ihre Links. Statische HTML-Exporte enthalten
keine Hostnavigation.
