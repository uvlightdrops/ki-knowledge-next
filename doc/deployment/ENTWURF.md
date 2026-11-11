---
title: "Deployment: offene Integration"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: deployment
purpose: "Trennt den vorhandenen Betriebsanschluss von offenen Produktions-, Automatisierungs- und Abnahmeentscheidungen."
created: "2026-11-10T20:55:00+01:00"
updated: "2026-11-11 21"
update_reason: "Lokalen Web-/Workerstart und vorhandenen Stopvertrag eingeordnet"
status: draft
relations:
  - target: README.md
    type: parent
    reason: Deploymentindex
  - target: ../architecture/ALTREPO-UEBERNAHME.md
    type: reference
    reason: Noch offene Übernahmebereiche
  - target: ../requirements/TODO-INDEX.md#deployment
    type: reference
    reason: Konkrete offene Betriebsaufträge
---

# Deployment: offene Integration

## Stand heute und Betriebsentscheidung [betriebsentscheidung]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
  - target: README.md#deployment-index
    type: reference
    reason: Betriebsgrundlagen und getrennte Hostanleitungen
  - target: ../features/KONFIGURATION-UND-START.md#lokaler-start
    type: reference
    reason: Implementierter lokaler Start und Stackvertrag
```

Next verwendet den gemeinsamen `stackctl`-Einstieg mit eigener
YAML-Konfiguration. Der lokale Starter beaufsichtigt Django und den
separaten Importworker gemeinsam. Der aktuelle Speicher
ist SQLite mit privaten Datei- und Beziehungswurzeln.

[Betriebsgrundlagen](BETRIEB.md) beschreiben Installation, Sicherung,
Update, Wiederherstellung und Abnahme. [U7](UBERSPACE7.md) und
[U8](UBERSPACE8.md) enthalten manuelle Dienst- und Routingvorlagen.
Die Zielhostintegration ist noch nicht implementiert oder praktisch abgenommen.

Für den Ausbau bleibt `stackctl` das gemeinsame Werkzeug. Wiederverwendet
werden passende Betriebsmechanismen, nicht die alte PostgreSQL-/Ollama-
Topologie oder deren anwendungsspezifische Prüfungen. Statische Ausgabe und
Appdeployment sind getrennte Aufträge.

## Produktionsstart und Zielhostprofile [produktionsintegration]

```yaml block-meta
updated: "2026-11-11 20"
status: draft
relations:
  - target: BETRIEB.md#produktionsvoraussetzungen
    type: reference
    reason: Gegenwärtige Voraussetzungen und fehlende Produktionssettings
  - target: UBERSPACE7.md#hostvoraussetzungen-u7
    type: reference
    reason: Supervisord-Ziel
  - target: UBERSPACE8.md#hostvoraussetzungen-u8
    type: reference
    reason: Systemd-User-Ziel
```

Offen sind die deklarierte Gunicorn-Abhängigkeit, geprüfte HTTPS-/Proxy-
und Cookie-Einstellungen sowie Next-spezifische U7-/U8-Stages. Die
Dienstvorlagen sind die Grundlage; Aktivierung und Webrouting bleiben
ausdrücklich bestätigte Betreiberaktionen.

Zielprofile müssen Web und Worker, private Pfade, Staticfiles und
Hostvoraussetzungen gemeinsam prüfen. Der bisherige
[`UberspaceDeployment`](../../../ki-knowledge/ki_knowledge/deployment/uberspace.py)
ist eine Portierungsquelle für Preflight und Dienststeuerung, kein
anwendungsneutraler Adapter: alte Appnamen, Startmodule und Pflichtdienste
müssen durch Next-Verträge ersetzt werden.

Konkrete Zielhostwerte und der vertrauenswürdige Proxyvertrag werden erst
mit dem gewählten Host festgelegt. Ein PostgreSQL-Wechsel oder Clusterbetrieb
ist dafür keine beschlossene Voraussetzung.

## Update- und Sicherungsautomatisierung [wartungsautomatisierung]

```yaml block-meta
updated: "2026-11-11 21"
status: draft
relations:
  - target: BETRIEB.md#updates-und-sicherung
    type: reference
    reason: Maßgebliche Wartungsreihenfolge
  - target: BETRIEB.md#wiederherstellung
    type: reference
    reason: Gemeinsamer Code-, Daten- und Konfigurationsstand beim Restore
```

Zu portieren sind ein installationsweiter Deploylock, Next-spezifische
Preflightprüfungen und ein überprüfter Wiederherstellungspunkt vor Update
und Migration. Der vorhandene Workerlock erfasst weder Deploys noch
Web-Schreibzugriffe. Der Worker lässt laufende Jobs bei SIGTERM auslaufen;
offen bleibt die gemeinsame Wartungssperre für neue Web-Schreibaufträge und
die Einbindung dieses Stopvertrags in die Zielhoststeuerung.

Die Sicherung muss DB, Originale, Extraktionen, Wiki, Beziehungen und
Konfiguration einschließlich externer Datenwurzeln erfassen. Das private
Manifest bindet diese an kompatible Code- und Paketrevisionen.
Mehrere Fast-forward-Pulls sind kein atomarer Releasewechsel; ein
automatischer Rollback ist noch nicht festgelegt.

Portierungstests aus
[`test_uberspace_deployment.py`](../../../ki-knowledge/tests/test_uberspace_deployment.py)
decken insbesondere konkurrierende Locks, Secretbehandlung, Backupfehler
und die Reihenfolge vor Migration ab. Next-spezifische Worker-, SQLite-
und Restorefälle müssen ergänzt werden.

## Praktische Betriebsabnahme [betriebsabnahme]

```yaml block-meta
updated: "2026-11-11 20"
status: draft
relations:
  - target: BETRIEB.md#abnahme
    type: reference
    reason: Fachliche und technische Hostabnahme
```

Ausstehend sind ein kontrollierter Zielhostlauf und eine Wiederherstellung
auf einem isolierten Ziel. Nachzuweisen sind HTTPS/CSRF, private Zugänge,
Staticfiles, Importworker, Neustart und Hostboot sowie konsistente Daten
nach Restore. Fehler vor und nach Backup, Migration und Neustart müssen
sichtbar bleiben; Quota und SQLite-Schreiblast sind praktisch zu prüfen.
