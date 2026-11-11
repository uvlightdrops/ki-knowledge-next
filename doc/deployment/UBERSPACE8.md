---
title: "Uberspace 8"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: deployment
purpose: "Beschreibt die manuelle Next-Dienstvorlage für Systemd-User und das U8-spezifische Webrouting."
created: "2026-11-11 18"
updated: "2026-11-11 20"
update_reason: "Hostvorlage mit offener Produktionsintegration verbunden"
status: active
relations:
  - target: README.md
    type: parent
    reason: Deploymentindex
---

# Uberspace 8

## Hostvoraussetzungen [hostvoraussetzungen-u8]

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

U8 stellt eine beim Hostboot gestartete Systemd-User-Instanz bereit.
`systemctl --user show-environment` muss ohne Fehler funktionieren.
Kein Systemdienst, Rootzugriff oder selbst eingerichtetes Linger voraussetzen.
Versioniertes Python mindestens 3.12, `journalctl`, Git, Uberspace-CLI,
Quota, freie Ports und Domain prüfen.

Die [gemeinsame Installation](BETRIEB.md#installation) muss abgeschlossen
sein; die Vorlagen setzen deren noch fehlende Produktionsintegration voraus.
U8-Anbieter-PostgreSQL und Extensions sind für den gegenwärtigen SQLite-
Next-Host keine Pflicht und werden hier nicht eingerichtet.

Quellen, geprüft am 11. November 2026:
[Systemd](https://u8manual.uberspace.de/services_systemd/),
[Python](https://u8manual.uberspace.de/lang_python/) und
[Webbackends](https://u8manual.uberspace.de/web_backends/).

## Webdienst und Importworker [dienste-u8]

```yaml block-meta
updated: "2026-11-11 18"
status: active
relations:
  - target: BETRIEB.md#updates-und-sicherung
    type: reference
    reason: Gemeinsames Stoppen aller Writer vor Update und Sicherung
```

Vorlagen unter `~/.config/systemd/user/` ablegen. Die expliziten Units
halten Web- und Workerparameter nachvollziehbar; vorhandene Units nicht
überschreiben. `%h` ist der Systemd-Home-Specifier, keine Shellvariable.
Gunicorn bleibt im Vordergrund und bindet für das U8-Frontend an
`0.0.0.0:8780`.

`ki-next-web.service`:

```ini
[Unit]
Description=Next Webdienst

[Service]
Type=simple
WorkingDirectory=%h/ki/src/ki-knowledge-next
ExecStart=%h/ki/src/ki-knowledge-next/.venv/bin/python -m gunicorn knext.wsgi:application --bind 0.0.0.0:8780 --workers 1 --threads 2 --timeout 120 --access-logfile - --error-logfile -
Restart=on-failure
RestartSec=5
TimeoutStopSec=150
UMask=0077

[Install]
WantedBy=default.target
```

`ki-next-worker.service`:

```ini
[Unit]
Description=Next Importworker

[Service]
Type=simple
WorkingDirectory=%h/ki/src/ki-knowledge-next
ExecStart=%h/ki/src/ki-knowledge-next/.venv/bin/python manage.py content_worker
Restart=on-failure
RestartSec=5
TimeoutStopSec=300
UMask=0077

[Install]
WantedBy=default.target
```

Kein `--once` und keine Secrets in `Environment=`. Beide Prozesse lesen
dieselben privaten YAML-Dateien. `default.target` ist das Bootziel der
User-Instanz, nicht `multi-user.target`. Systemd beendet die Dienstprozessgruppe;
nach erzwungenem Timeout unterbrochene Jobs prüfen.

Nach bestandenen Produktionsgates:

```bash
systemctl --user daemon-reload
systemctl --user enable --now ki-next-web.service ki-next-worker.service
systemctl --user status ki-next-web.service ki-next-worker.service
journalctl --user -u ki-next-web.service -u ki-next-worker.service -n 100 --no-pager
```

Wartungssteuerung:

```bash
systemctl --user stop ki-next-worker.service ki-next-web.service
# Backup, Update, Migration und Staticfiles nach BETRIEB.md
systemctl --user start ki-next-web.service ki-next-worker.service
```

Nach Unitänderungen erneut `daemon-reload`. Logretention und Speicherquota
prüfen. U8 bietet auch `uberspace service add`; dessen sofortigen Start
nicht mit einer harmlosen Konfigurationsvorschau verwechseln.

## Domain und Staticfiles [webrouting-u8]

```yaml block-meta
updated: "2026-11-11 18"
status: active
relations: []
```

Den DocumentRoot gemäß
[U8-Handbuch](https://u8manual.uberspace.de/web_documentroot/) prüfen,
insbesondere Domain-Symlinks und gemeinsam verwendete Verzeichnisse.
Nur gesammelte Staticfiles öffentlich bereitstellen. Gunicorn liefert sie
nicht aus; `STATIC_ROOT` muss zum `static/`-Pfad der gewählten Domain passen.
Private Daten und Backups dürfen nicht über DocumentRoot-Symlinks erreichbar sein.
Öffentliche Staticfiles benötigen Webserver-lesbare Rechte (`0644` für
Dateien, `0755` für ihre Verzeichnisse); die private Dienst-Umask darf
nicht durch pauschale Rechteänderungen an allen Daten aufgehoben werden.

**U8 verwendet `add`, nicht die U7-Syntax `set --http --port`.**
Vor Änderung den Bestand ansehen und die konkrete Domain freigeben:

```bash
uberspace web backend list
uberspace web backend add knowledge.example.org/ port 8780
uberspace web backend add knowledge.example.org/static static
uberspace web backend list
```

`knowledge.example.org` ist ein Platzhalter. Bei bereits vorhandener Zuordnung
bricht `add` ohne `--force` ab; Überschreiben erst nach Prüfung und expliziter
Freigabe, nicht automatisch erzwingen. `static` lässt reine Assets direkt
vom U8-Frontend aus dem DocumentRoot ausliefern. Es ersetzt hier das
U7-`--apache`-Staticbackend.

U8 braucht ebenfalls `0.0.0.0` oder `::`, nicht Loopback. Domainwurzel statt
eines ungeprüften App-Unterpfads verwenden. HTTPS-/Proxyerkennung und
Staticfile-Rechte vor Freigabe testen; anschließend die gemeinsame
[Betriebsabnahme](BETRIEB.md#abnahme) durchführen.
