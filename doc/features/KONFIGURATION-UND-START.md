---
title: "Konfiguration und lokaler Start"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: features
purpose: "Beschreibt die implementierte YAML-Konfiguration, lokalen Startwege und Readiness-Prüfung, ohne geplantes Produktionsdeployment oder KI als verfügbar auszugeben."
created: "2026-11-11T04:56:00+01:00"
updated: "2026-11-11 21"
update_reason: "Lokalen gemeinsamen Start von Django und Importworker beschrieben"
status: active
relations:
  - target: "README.md"
    type: parent
    reason: "Index der implementierten Features"
  - target: "../architecture/KONFIGURATION-UND-KI.md"
    type: depends-on
    reason: "Schemazuständigkeit und Abgrenzung der späteren KI-/Wizard-Anbindung"
  - target: "../deployment/ENTWURF.md"
    type: depends-on
    reason: "Noch offene Produktionsintegration"
---

# Konfiguration und lokaler Start

## Konfiguration [konfiguration]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations:
- target: ../architecture/KONFIGURATION-UND-KI.md#konfigurationsentscheidung
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

**Implementiert:** Django und `stackctl` verwenden denselben projektlokalen
Loader auf Basis von `yaml-cfg-wizard`. Das Next-Schema validiert
Pfad-/Django-Einstellungen und den lokalen Ein-Dienst-Stack.
Unbekannte Felder, ungültige Typen und ausdrücklich gewählte, fehlende
Stages/Profiles führen zu Fehlern.

Eine optionale, Git-ignorierte `ki.yaml` im Projekt kann beispielsweise
Hostnamen und Stackport festlegen:

```yaml
apps:
  ki_knowledge_next:
    django:
      allowed_hosts: [localhost, "127.0.0.1"]
stack:
  services:
    django:
      port: 8782
```

```bash
.venv/bin/python -m knext.config
```

Der Befehl validiert, ohne aufgelöste Werte oder Zugangsdaten auszugeben.
Es gibt noch keinen Web-Konfigurationseditor.

## Priorität und Pfade [prioritaet-und-pfade]

```yaml block-meta
updated: "2026-11-11 18"
status: active
relations:
- target: ../deployment/BETRIEB.md#installation
  type: reference
  reason: Verwendung derselben YAML-Layer im vorbereiteten Hostbetrieb
- target: ../architecture/KONFIGURATION-UND-KI.md#wizard-und-zustaendigkeit
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

Priorität von niedrig nach hoch:
Schema-Defaults → `config/defaults/` → `ki.yaml` → ausgewähltes Profile →
ausgewählte Stage → Runtime-Layer → bisherige `KI_NEXT_*` →
`KI_CFG_*` → projektlokale `creds.yaml`.

Stage/Profile werden über `KI_STAGE` / `KI_PROFILE` oder die Marker
`config/stages/.active_stage` / `config/profiles/.active_profile` gewählt.
Ohne Auswahl wird kein solcher Layer geladen. `KI_STAGE=dev-local`
aktiviert die mitgelieferte lokale Stage.

Relative Datenpfade beziehen sich auf das Projekt, nicht auf das aktuelle
Arbeitsverzeichnis. Konfigurationen aus Nachbarprojekten oder Home-
Konfigurationsordnern werden nicht eingelesen.
`apps.ki_knowledge_next.paths.data` bestimmt die Bereitstellungswurzel;
`paths.documentation` standardmäßig das lokale `doc/`.

Die bisherigen `KI_NEXT_*` funktionieren mit Übergangswarnung.
Ein skalarer Override kann etwa
`KI_CFG_STACK__SERVICES__DJANGO__PORT=8782` verwenden; Listen wie
`allowed_hosts` werden in YAML gesetzt.

Credentials gehören in die Git-ignorierte `creds.yaml`, nicht in versionierte
Defaults. Bei `debug: false` ist ein ausdrücklich gesetzter Secret Key
erforderlich. Im lokalen Debugbetrieb bleibt der Entwicklungsschlüssel
unter `paths.var/secret_key` erhalten.

## Relationenkatalog [relationenkatalog]

```yaml block-meta
updated: "2026-11-11 19"
status: active
relations:
  - target: ../architecture/ui/RELATIONEN.md#betreiberkatalog
    type: depends-on
    reason: Stabile Typbedeutungen und erhaltender Presetwechsel
```

`apps.ki_knowledge_next.relation_catalog` wählt `basic`, `documentation`
(Standard) oder `knowledge` und ergänzt eigene Typen. Beispiel in `ki.yaml`:

```yaml
apps:
  ki_knowledge_next:
    relation_catalog:
      preset: basic
      types:
        - key: illuminates
          label: Beleuchtet
          description: "Der Ausgang beleuchtet einen Aspekt des Ziels."
          color: "#b58a40"
          enabled: true
```

Die Wiki-Konfiguration erhält denselben Katalog als `RELATION_CATALOG`.
Im Solo-Wiki und im Django-Adapter kann dieser Schlüssel direkt konfiguriert
werden. `enabled: false` deaktiviert einen Typ für neue Beziehungen, nicht
seine vorhandenen Kanten. Definitionen bestehender Presetschlüssel dürfen
nicht geändert werden; doppelte Schlüssel und ungültige Farben werden
ausdrücklich abgelehnt. Nach Dateikonfigurationsänderungen Webprozesse neu starten.

## Lokaler Start [lokaler-start]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
- target: ../deployment/ENTWURF.md#betriebsentscheidung
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
- target: IMPORT-UND-JOBS.md#worker-und-fehler
  type: reference
  reason: Workerstatus und Verarbeitung der wartenden Aufträge
```

Nach der Einrichtung aus dem [Projekt-README](../../README.md) sind folgende
Startwege verfügbar:

| Startweg | Verhalten |
|---|---|
| `./start [adresse:port]` | Führt Migrationen aus und startet Django und einen separaten Importworker; Standard `127.0.0.1:8780`, eigener Adressparameter statt Stackport |
| `./start --lan LAN-IP` | Lauscht auf `0.0.0.0:8780`; ergänzt konkrete IPv4-Adresse und localhost für diesen Prozess, keine Wildcardfreigabe |
| IDE / `manage.py runserver` | Direkter Django-Start; Worker separat starten und Migrationen vorher ausführen |
| `stackctl run django` | Startet Django und Importworker gemeinsam im Vordergrund mit `--noreload`; führt keine Migrationen aus |

```bash
.venv/bin/python manage.py migrate
.venv/bin/python -m stackctl spec
.venv/bin/python -m stackctl run django
```

`stackctl spec` zeigt den Dienstplan, ohne Dienste zu starten.
Der lokale Stack verwaltet Web und Worker über `knext.devserver` als einen
gemeinsamen Startweg; beide bleiben eigene Prozesse. Strg+C oder SIGTERM
stoppt beide. Ein unerwartetes Prozessende stoppt auch den Partner und
zeigt den Fehler an. Der Worker beendet seinen laufenden Job vor dem Stop;
nach 30 Sekunden erzwingt der lokale Starter einen Abbruch mit Warnung.
Ein bereits separat laufender Worker muss vor diesem gemeinsamen Start
gestoppt werden; die Sperre verhindert einen zweiten Worker.

Alle Prozesse verwenden dieselben Konfigurationslayer. Die eingestellten
Wiki- und Datenwurzeln müssen erreichbar sein; Fehler bleiben im Terminal
sichtbar. Der lokale Betrieb setzt weder PostgreSQL noch FastAPI oder
Ollama voraus.

Für LAN-Zugriff beispielsweise `./start --lan 192.168.1.20` verwenden und
die tatsächliche Adresse des Rechners einsetzen. Der Start zeigt die URL an.
Bestehende Hosteinträge bleiben erhalten; ein vorhandenes `*` wird abgelehnt.
Die prozessbezogene Ergänzung nutzt den bestehenden `KI_NEXT_ALLOWED_HOSTS`-
Übergangsweg. Höhere Layer wie `creds.yaml` oder `KI_CFG_*` dürfen die konkrete
IP nicht ausschließen; andernfalls bricht der Start vor Migrationen mit
einem Konfigurationshinweis ab.

Die Freigabe ändert keine Firewall und umgeht keine WLAN-Clientisolation.
Nur im vertrauenswürdigen LAN verwenden: HTTP und Debug-Entwicklungsserver
sind keine öffentliche Produktionsbereitstellung. Ohne `--lan` bleibt der
Standardstart auf Loopback beschränkt.

## Readiness [readiness]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations:
- target: ../deployment/BETRIEB.md#abnahme
  type: reference
  reason: Einordnung der Readiness-Prüfung in die Hostabnahme
```

`/health/ready/` ist ohne Anmeldung erreichbar und erlaubt GET/HEAD.
Sind Datenbank und Migrationsstand bereit, liefert GET HTTP 200 mit
`{"status": "ready"}`. Bei Datenbankfehlern oder ausstehenden Migrationen
liefert es HTTP 503 mit `{"status": "not_ready"}`.
Interne Fehlerdetails und Konfigurationswerte werden nicht ausgegeben.

Die Prüfung deckt keine externen Markdown-Wurzeln, KI-Dienste oder Worker
ab. Ein bereiter Endpunkt bestätigt somit nicht alle fachlichen Funktionen.

## Grenzen [grenzen]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations: []
```

Dies ist lokaler Entwicklungsbetrieb, keine Produktionsfreigabe.
Produktionsserver, automatische Updates, Zielhostprofile und ein
automatisierter Backup-/Restoreablauf sind noch nicht implementiert.
Die für die Quellenmigration angelegte lokale SQLite-Sicherung ist kein
allgemeines Deployment-Backupfeature.

KI-Schema, Provider-/Chat-Anbindung und Runtime-Webeditor stehen weiterhin
im [Konfigurationskonzept](../architecture/KONFIGURATION-UND-KI.md).
Der geplante Produktionsablauf steht in
[Betriebsgrundlagen](../deployment/BETRIEB.md); offene Integration steht im
[Deploymententwurf](../deployment/ENTWURF.md).
