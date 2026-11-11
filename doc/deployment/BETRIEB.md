---
title: "Betriebsgrundlagen"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: deployment
purpose: "Beschreibt die gemeinsame Vorbereitung und den sicheren Betriebsablauf für Next auf Uberspace."
created: "2026-11-11 18"
updated: "2026-11-11 22"
update_reason: "SIGTERM-Auslaufen des Importworkers im Wartungsablauf berücksichtigt"
status: active
sources:
  - repository: ki-knowledge
    path: ki_knowledge/deployment/uberspace.py
    purpose: "Vorbild für Preflight, Deploylock, Sicherung und Updatefolge; keine Codeübernahme"
relations:
  - target: README.md
    type: parent
    reason: Deploymentindex
---

# Betriebsgrundlagen

## Produktionsvoraussetzungen [produktionsvoraussetzungen]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations:
  - target: ENTWURF.md#produktionsintegration
    type: reference
    reason: Noch offener Produktionsanschluss
  - target: UBERSPACE7.md#hostvoraussetzungen-u7
    type: reference
    reason: Voraussetzungen des U7-Hosts
  - target: UBERSPACE8.md#hostvoraussetzungen-u8
    type: reference
    reason: Voraussetzungen des U8-Hosts
```

Next bietet `knext.wsgi:application`, SQLite unter `paths.var/db.sqlite3`,
einen separaten `content_worker` und `/health/ready/`. Für diese Topologie
sind weder FastAPI noch PostgreSQL, pgvector oder Ollama Pflichtdienste.
Ein kleiner Start mit einem Webworker und einem Importworker vermeidet
unnötige Parallelität; SQLite-Schreibkonflikte und Hostlimits müssen dennoch
unter realer Last geprüft werden.
Der `content_worker` sperrt parallele Worker bereits über einen Dateilock;
dieser ersetzt keinen Deploylock und sperrt keine Web-Schreibzugriffe.

**Noch fehlende Produktionsintegration:** Gunicorn ist nicht als
Projektabhängigkeit deklariert. Das Konfigurationsschema erlaubt nur
`stack.target: local`; es gibt keine Next-Stages für Supervisord oder
Systemd-User. Die Vorlagen unten werden deshalb nicht über den vorhandenen
lokalen `stackctl`-Stack gestartet. Alte `deploy/uberspace*/deploy.py`-
Entrypoints dürfen nicht gegen Next ausgeführt werden.

`debug: false`, `allowed_hosts` und `secret_key` sind konfigurierbar.
HTTPS-Proxyvertrauen, sichere Session-/CSRF-Cookies, HTTPS-Redirect und HSTS
sind in Next noch nicht als Produktionskonfiguration verdrahtet.
Vor öffentlichem Betrieb müssen diese Settings ergänzt, mit dem
tatsächlichen Proxyvertrag geprüft und durch `manage.py check --deploy`
bewertet werden. Keine beliebigen Forwarded-Header als vertrauenswürdig
behandeln. Zusätzliche CSRF-Origins nur für tatsächlich benötigte Origins
setzen; sie ersetzen keine korrekte HTTPS-Erkennung.

Gunicorn und eine reproduzierbar festgehaltene Abhängigkeitsauswahl gehören
in die freigegebene Releaseinstallation, nicht in einen improvisierten
Dienststart. Die folgenden Dienstvorlagen setzen diese Ergänzungen voraus.

## Installation und private Pfade [installation]

```yaml block-meta
updated: "2026-11-11 18"
status: active
relations:
  - target: ../features/KONFIGURATION-UND-START.md#prioritaet-und-pfade
    type: depends-on
    reason: Tatsächlicher YAML-Layer- und Credentialsvertrag
```

Ein möglicher privater Aufbau ist:

```text
~/ki/src/ki-knowledge-next/       Checkout und .venv
~/ki/src/<siblings>/             versionierte Paketcheckouts
~/ki/var/ki-knowledge-next/       SQLite und interne Zustände
~/ki/data/                      bereitgestellte Originale und Extraktionen
~/ki/wiki/                      bearbeitbare Wiki-Blöcke
~/ki/relations/                 getrennte Beziehungswurzeln
~/ki/backups/                   private Wiederherstellungspunkte
```

Code, Daten, `creds.yaml`, DB und Backups liegen außerhalb des DocumentRoot.
Nur gesammelte Staticfiles dürfen öffentlich werden. Vorhandene externe
Domänen und Pfade einbinden, nicht durch leere Beispielverzeichnisse ersetzen.

Im geprüften Checkout Python 3.12 oder neuer explizit wählen und eine eigene
venv erstellen. Projekt und deklarierte Siblings aus kompatiblen, dokumentierten
Revisionen installieren; der bestehende Installationsweg steht im
[Projekt-README](../../README.md). Anschließend `pip check` ausführen.
Keine vorhandene venv oder fremden Konfigurationsdateien überschreiben.

Beispiel für die bereits unterstützten Felder in der privaten `ki.yaml`;
`ACCOUNT` und Domain sind Platzhalter:

```yaml
apps:
  ki_knowledge_next:
    paths:
      var: /home/ACCOUNT/ki/var/ki-knowledge-next
      workspace: /home/ACCOUNT/ki/wiki
      data: /home/ACCOUNT/ki/data
      data_relations: /home/ACCOUNT/ki/relations/data
      document_relations: /home/ACCOUNT/ki/relations/documentation
    django:
      debug: false
      allowed_hosts: [knowledge.example.org]
      static_root: /var/www/virtual/ACCOUNT/knowledge.example.org/static
```

`documentation` bleibt standardmäßig das `doc/` im Next-Checkout.
Den zufälligen Secret Key unter
`apps.ki_knowledge_next.django.secret_key` in der Git-ignorierten
`creds.yaml` hinterlegen. Credentials sind nur für den Account lesbar
(`0600`); keine Secrets in Units, Argumentlisten, Screenshots oder Git.
Service und Verwaltungsbefehle müssen dieselben Konfigurationslayer laden;
keine nur in einer interaktiven Shell gesetzten Produktionswerte voraussetzen.

Vor dem ersten Start, bei bestehenden Daten erst nach geprüftem Backup:

```bash
.venv/bin/python -m knext.config
.venv/bin/python -m pip check
.venv/bin/python manage.py check --deploy
.venv/bin/python manage.py migrate --plan
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
```

Die Deployprüfung ist ein Gate, kein automatisch erfolgreicher Schritt.
Warnungen zu den oben fehlenden HTTPS-Settings nicht pauschal ignorieren.
Gunicorn liefert Staticfiles nicht selbst aus. Der konkrete DocumentRoot
und das Staticbackend werden in der jeweiligen Hostanleitung geprüft.

## Updates und Sicherung [updates-und-sicherung]

```yaml block-meta
updated: "2026-11-11 22"
status: active
relations:
  - target: ENTWURF.md#wartungsautomatisierung
    type: reference
    reason: Noch offene Automatisierung dieses Wartungsablaufs
  - target: UBERSPACE7.md#dienste-u7
    type: reference
    reason: U7-Dienststeuerung für den Wartungsablauf
  - target: UBERSPACE8.md#dienste-u8
    type: reference
    reason: U8-Dienststeuerung für den Wartungsablauf
```

Ein gemeinsamer Deploylock muss alle Entrypoints derselben Installation
einschließen. Die Lockautomatisierung des Altprojekts ist noch nicht portiert;
bis dahin nur einen kontrollierten Wartungsvorgang gleichzeitig zulassen.

1. Wartung ankündigen, neue Schreibaufträge unterbinden und Web- sowie
   Importworker kontrolliert stoppen. Auf laufende Jobs und weitere Writer
   achten; erzwungener Abbruch kann einen prüfpflichtigen Jobstand hinterlassen.
2. Konsistenten Snapshot erstellen: SQLite mit ihrer Backup-API oder einem
   verifizierten Offlinebackup sichern, nicht eine live beschriebene DB-Datei
   allein kopieren. Wiki, Beziehungen, Originale, Extraktionen, private
   Konfiguration und jede externe Datenwurzel zum selben Stand sichern.
3. Integrität des DB-Backups und Lesbarkeit der Dateien prüfen. UTC-Zeit,
   Python-/Paketversionen und Git-Revisionen aller beteiligten Repositories
   in einem privaten Manifest festhalten. Backups auch außerhalb des Hosts
   verschlüsselt aufbewahren und regelmäßig testen.
4. Nur saubere Checkouts mit bekannten Upstreams aktualisieren:
   `git pull --ff-only`, keine automatischen Resets oder Stashes.
   Mehrere nacheinander aktualisierte Repositories sind kein atomarer Release.
5. Abhängigkeiten aus dem neuen Release installieren und prüfen; Migrationen
   und Staticfiles aus dem neuen Code ausführen. Danach Dienste starten und
   die Abnahme durchführen.

Ein Fehler nach Stop oder Migration bleibt sichtbar; Dienste nicht
blind wieder starten. Dieser Ablauf ist eine Betriebsanweisung, noch kein
automatisiertes Backup-/Updatesystem in Next.

SIGTERM lässt den gegenwärtigen Importworker seinen laufenden Job beenden,
ohne den nächsten zu übernehmen. Den Host-Stoptimeout passend zur maximalen
Jobdauer wählen und das tatsächliche Prozessende abwarten.
Vor Wartung aktive Jobs prüfen; nach erzwungener Unterbrechung markiert der nächste
Workerstart verwaiste laufende Jobs zur Prüfung statt sie still zu wiederholen.

## Wiederherstellung [wiederherstellung]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations:
  - target: ENTWURF.md#wartungsautomatisierung
    type: reference
    reason: Automatisierungsvertrag für überprüfbare Wiederherstellungspunkte
```

Vor dem Restore Web, Worker und weitere schreibende Zugänge stoppen.
Den fehlgeschlagenen Stand separat bewahren. Einen geprüften Backupzeitpunkt
mit kompatiblen Code-, Paket- und Schemafassungen auswählen und DB,
Dateidaten sowie Konfiguration gemeinsam wiederherstellen. Neue DB mit
altem Code zu kombinieren ist kein Rollback.

DB-Snapshot zunächst separat öffnen und auf Integrität prüfen. Veraltete
SQLite-Journal-/WAL-Dateien dürfen nicht mit dem wiederhergestellten Snapshot
vermengt werden; den Austausch im vollständig gestoppten Zustand planen.
Absolute externe Datenpfade und Dateirechte prüfen. Keine neueren Daten
unbemerkt durch ein älteres Backup überschreiben.

Erst Readiness, Anmeldung und einen fachlichen Leseweg prüfen, dann
Schreibzugriffe und Worker wieder freigeben. Jobstände auf unterbrochene
Ausführung und mögliche bereits angelegte Artefakte prüfen; nicht pauschal
alle Jobs wiederholen. Ein Restore muss auf einem isolierten Ziel praktisch
erprobt werden, bevor das Backup als belastbar gilt.

## Betriebsabnahme [abnahme]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations:
  - target: ENTWURF.md#betriebsabnahme
    type: reference
    reason: Ausstehender praktischer Nachweis
  - target: ../features/KONFIGURATION-UND-START.md#readiness
    type: depends-on
    reason: Umfang und Grenzen des vorhandenen Healthchecks
```

Über die echte HTTPS-Domain `/health/ready/` auf HTTP 200 und
`{"status":"ready"}` prüfen. Das bestätigt DB und Migrationen, nicht Worker,
Dateiwurzeln oder alle Fachfunktionen. Ergänzend Anmeldung, CSRF-geschützte
Aktion, Wiki-Domäne, Staticfiles und einen kleinen kontrollierten Importjob
prüfen. Unangemeldete Nutzer dürfen keine privaten Inhalte erhalten.

Dienstneustart und Hostboot müssen Web und Worker wieder starten.
RAM-/Speicherquota, Logrotation, SQLite-Schreiblast und Restore praktisch
prüfen. Statischer HTML-/ZIP-Export bleibt ein Artefaktdownload und löst
keine Änderung des Appdeployments oder Webroutings aus.
