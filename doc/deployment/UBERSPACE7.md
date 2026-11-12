---
title: "Uberspace 7"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: deployment
purpose: "Beschreibt die manuelle Next-Dienstvorlage für Supervisord und das explizite Webrouting auf U7."
created: "2026-11-11 18"
updated: "2026-11-12 18"
update_reason: "Erkennung und bestätigte Weiterverwendung einer vorhandenen Python-Umgebung beschrieben"
status: active
relations:
  - target: README.md
    type: parent
    reason: Deploymentindex
---

# Uberspace 7

## Hostvoraussetzungen [hostvoraussetzungen-u7]

```yaml block-meta
updated: "2026-11-11 20"
status: active
relations:
  - target: BETRIEB.md#produktionsvoraussetzungen
    type: depends-on
    reason: Produktionsgates vor Dienstaktivierung
  - target: ENTWURF.md#produktionsintegration
    type: reference
    reason: Noch ausstehende Umsetzung des Zielprofils
```

U7 verwendet Supervisord im Benutzeraccount. Python mindestens 3.12
explizit über das versionierte Binary wählen, nicht den unversionierten
U7-Standard voraussetzen. Git, `supervisorctl`, Uberspace-CLI, freie Ports,
Quota und die gewählte Domain prüfen.

Die [gemeinsame Installation](BETRIEB.md#installation) muss abgeschlossen
sein. Die folgenden Vorlagen sind erst nach Ergänzung der dort benannten
Produktionssettings und Gunicorn-Abhängigkeit aktivierbar.
Keine alten PostgreSQL-/Ollama-Dienste als Next-Pflichtbestand übernehmen.

Quellen, geprüft am 11. November 2026:
[Python](https://manual.uberspace.de/lang-python/),
[Supervisord](https://manual.uberspace.de/daemons-supervisord/) und
[Webbackends](https://manual.uberspace.de/web-backends/).

## Eingaben der Ersteinrichtung [setup-eingaben-u7]

```yaml block-meta
updated: "2026-11-12 18"
status: active
relations: []
```

`python3.12 scripts/setup_u7.py` merkt jede gültige Eingabe unmittelbar
in `.setup-u7-answers.json` im Projektcheckout: Domain, Port, Wiki- und
Datenverzeichnis. Nach einem Fehler oder Abbruch mit Strg+C werden bereits
erfasste Werte beim nächsten Aufruf in eckigen Klammern angeboten.
Enter übernimmt den Wert; eine neue Eingabe ersetzt ihn. Ungültige Eingaben
werden direkt erneut abgefragt.

Die Datei wird atomar mit privaten Zugriffsrechten (`0600`) geschrieben
und von Git ignoriert. Sie enthält keine Passwörter, Django-Schlüssel
oder Bestätigungen für Hoständerungen. Zum Verwerfen der Vorgaben kann
die Datei gezielt gelöscht werden. Eine beschädigte Eingabedatei führt
zu einem sichtbaren Fehler statt zum stillen Verlust der Werte.

Das ist eine Wiederverwendung von Eingaben, keine automatische Fortsetzung
teilweise installierter Dienste. Sicherheitsprüfungen und Bestätigungen
laufen erneut; vorhandene Konfigurationen, Zugangsdaten und Datenpfade
werden weiterhin nicht überschrieben. Teilstände nach späteren Installationsfehlern müssen vor
einem erneuten Einrichtungsversuch geprüft werden.

Eine vorhandene lokale `.venv` wird erkannt und auf Python mindestens 3.12,
einen passenden eigenen venv-Prefix und verfügbares pip geprüft.
Nach ausdrücklicher Bestätigung wird sie weiterverwendet; die Installation
kann dabei Pakete aktualisieren. Die Umgebung wird nicht neu erzeugt oder
gelöscht. Ungültige Umgebungen und als Symlink eingebundene `.venv`-Verzeichnisse
führen zu einem sichtbaren Abbruch. Fehlt `.venv`, wird sie wie bisher angelegt.

## Webdienst und Importworker [dienste-u7]

```yaml block-meta
updated: "2026-11-11 18"
status: active
relations:
  - target: BETRIEB.md#updates-und-sicherung
    type: reference
    reason: Gemeinsames Stoppen aller Writer vor Update und Sicherung
```

Je Dienst eine Datei unter `~/etc/services.d/` anlegen.
`ACCOUNT`, Pfade und Port ersetzen; keine vorhandenen Dienste überschreiben.
Das Beispiel bindet den Webdienst an `0.0.0.0:8780`, wie vom U7-Frontend
benötigt. Gunicorn bleibt im Vordergrund, ohne `--daemon`.

`ki-next-web.ini`:

```ini
[program:ki-next-web]
directory=/home/ACCOUNT/ki/src/ki-knowledge-next
command=/home/ACCOUNT/ki/src/ki-knowledge-next/.venv/bin/python -m gunicorn knext.wsgi:application --bind 0.0.0.0:8780 --workers 1 --threads 2 --timeout 120 --access-logfile - --error-logfile -
autostart=true
autorestart=true
startsecs=10
stopsignal=TERM
stopwaitsecs=150
stopasgroup=true
killasgroup=true
umask=0077
```

`ki-next-worker.ini`:

```ini
[program:ki-next-worker]
directory=/home/ACCOUNT/ki/src/ki-knowledge-next
command=/home/ACCOUNT/ki/src/ki-knowledge-next/.venv/bin/python manage.py content_worker
autostart=true
autorestart=true
startsecs=10
stopsignal=TERM
stopwaitsecs=300
stopasgroup=true
killasgroup=true
umask=0077
```

Kein `--once`: Der Worker soll als dauerhafter Dienst laufen. Ein Stoptimeout
ist kein zugesicherter transaktionaler Jobabschluss; unterbrochene Jobs prüfen.
Supervisor verwendet eigene Logdateien unter `~/logs/`; deren Rotation und
Quota kontrollieren.

```bash
supervisorctl reread
supervisorctl update ki-next-web ki-next-worker
supervisorctl status ki-next-web ki-next-worker
supervisorctl tail ki-next-web stderr
supervisorctl tail ki-next-worker stderr
```

`update` aktiviert die neuen Dienste. Nur nach bestandenen Gates ausführen.
Wartungssteuerung:

```bash
supervisorctl stop ki-next-worker ki-next-web
# Backup, Update, Migration und Staticfiles nach BETRIEB.md
supervisorctl start ki-next-web ki-next-worker
```

## Domain und Staticfiles [webrouting-u7]

```yaml block-meta
updated: "2026-11-11 18"
status: active
relations: []
```

Domain und TLS separat einrichten. Den bestehenden DocumentRoot gemäß
[U7-Handbuch](https://manual.uberspace.de/web-documentroot/) prüfen:
Domain-Symlinks können denselben Inhalt teilen. `STATIC_ROOT` muss in den
öffentlichen `static/`-Ordner dieser Domain zeigen; nur Staticfiles dort
ablegen, keine Symlinks auf private Daten oder den ganzen Checkout.

Zuerst Bestand anzeigen. Nach ausdrücklicher Freigabe der Domainzuordnung:

```bash
uberspace web backend list
uberspace web backend set knowledge.example.org --http --port 8780
uberspace web backend set knowledge.example.org/static --apache
uberspace web backend list
```

Die Befehle verändern Routing. Die Domain ist ein Platzhalter; nicht das
globale `/`-Backend fremder Anwendungen ersetzen. U7 benötigt `0.0.0.0`
oder `::`, nicht Loopback. Öffentliche Staticfiles (`0644`) und ihre
Verzeichnisse (`0755`) müssen vom Webserver lesbar sein, während Daten
und Credentials privat bleiben. Keine rekursive Rechteänderung am Home
oder an privaten Datenwurzeln durchführen.

Über die echte HTTPS-Domain Login, CSRF, `/static/` und Readiness prüfen.
Proxy-/HTTPS-Header nicht ungeprüft aus dem Altprojekt übernehmen.
Die gemeinsame [Betriebsabnahme](BETRIEB.md#abnahme) bleibt erforderlich.
