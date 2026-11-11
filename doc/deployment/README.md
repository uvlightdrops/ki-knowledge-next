---
title: "Deployment"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: deployment
purpose: "Einstieg in die Betriebsgrundlagen und die getrennten Uberspace-7-/8-Anleitungen für Next."
created: "2026-11-11 18"
updated: "2026-11-11 20"
update_reason: "Stand heute und offene Integration getrennt erschlossen"
status: active
relations:
  - target: ../README.md
    type: parent
    reason: Projektdokumentation
  - target: BETRIEB.md
    type: child
    reason: Gemeinsame Voraussetzungen, Installation, Updates und Wiederherstellung
  - target: UBERSPACE7.md
    type: child
    reason: Supervisord und U7-Webrouting
  - target: UBERSPACE8.md
    type: child
    reason: Systemd-User-Dienste und U8-Webrouting
  - target: ENTWURF.md
    type: child
    reason: Produktionsintegration, Automatisierung und praktische Abnahme
  - target: ../architecture/README.md
    type: reference
    reason: Modellkonzepte außerhalb der Betriebsanleitungen
---

# Deployment

## Betriebsdokumente [deployment-index]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations:
  - target: ENTWURF.md#betriebsentscheidung
    type: reference
    reason: Vorhandener Betriebsanschluss und gemeinsame Werkzeugentscheidung
```

Die Betriebsgrundlagen und Hostanleitungen beschreiben den manuellen
Next-Betrieb. Der Entwurf bündelt die noch fehlende Produktionsintegration
und Automatisierung; konkrete Arbeitsaufträge stehen im
[TODO-Index](../requirements/TODO-INDEX.md#deployment).

| Dokument | Status | Zweck | Semantische Blöcke |
|---|---|---|---|
| [Betriebsgrundlagen](BETRIEB.md) | active | Produktionsvoraussetzungen, Vorbereitung, Update und Restore | produktionsvoraussetzungen, installation, updates-und-sicherung, wiederherstellung, abnahme |
| [Uberspace 7](UBERSPACE7.md) | active | Supervisord-Dienste und explizites U7-Webbackend | hostvoraussetzungen-u7, dienste-u7, webrouting-u7 |
| [Uberspace 8](UBERSPACE8.md) | active | Systemd-User-Dienste und explizites U8-Webbackend | hostvoraussetzungen-u8, dienste-u8, webrouting-u8 |
| [Offene Integration](ENTWURF.md) | draft | Stand heute, Produktionsstart, Wartungsautomatisierung und Abnahme | betriebsentscheidung, produktionsintegration, wartungsautomatisierung, betriebsabnahme |

`active` bezeichnet die Vollständigkeit der Beschreibung für diesen Umfang,
nicht eine Produktionsfreigabe. Vor Dienstaktivierung gelten die
[Produktionsvoraussetzungen](BETRIEB.md#produktionsvoraussetzungen).
