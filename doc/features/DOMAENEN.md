---
title: "Domänenverwaltung und persönliche Auswahl"
project: ki-knowledge-next
scope: features
purpose: "Beschreibt das Anlegen von Domänen, die persönliche Auswahl und ihre Einbindung in das Wissenswiki."
created: "2026-11-11 05"
updated: "2026-11-11 17"
update_reason: "Domänenkontext ohne entferntes Uploadformular beschrieben"
status: active
agent_project: ki-knowledge-next
relations:
  - target: README.md
    type: parent
    reason: Index der implementierten Features
---

# Domänenverwaltung und persönliche Auswahl

## Domänen verwalten [domaenen-verwalten]

```yaml block-meta
updated: "2026-11-11 17"
status: active
relations:
  - target: ../architecture/KNOWLEDGE-DOMAIN-AND-LIFECYCLE.md#domain-boundary
    type: depends-on
    reason: Domänengrenze und Abgrenzung der persönlichen Auswahl
```

`/domains/` zeigt allen angemeldeten Benutzern verfügbare Dokumentdomänen
und bietet deren persönliche Auswahl. Unter „Einstellungen“ enthält die
Unternavigation einen direkten Link „Domänen“. Nur Staff-Benutzer können eine
neue Domäne anlegen.

Ein einfacher Verzeichnisname, etwa `Books`, erzeugt
`DATA_DIR/Books/md`, das getrennte Beziehungsverzeichnis und einen
`ManagedDomain`-Eintrag in Next. Der Anzeigename erhält den konfigurierten
`MARKDOWN_DATA.prefix`, standardmäßig `ki:Books`. Auch eine noch leere Domäne
ist danach im Switcher, Quellenbestand und Wissensnetz verfügbar.
Bestehende konfigurierte und entdeckte Alt-Domänen bleiben erhalten.

Vorhandene Verzeichnisse, doppelte Namen, Pfadbestandteile und Symlinks am
Ziel werden nicht überschrieben oder übernommen. Fehler erscheinen im
Formular. DB-Transaktion und gezielte Entfernung gerade angelegter leerer
Ordner behandeln unmittelbare Fehlschläge; DB und Dateisystem bilden dennoch
keine gemeinsame crashsichere Transaktion. Nach einem Prozessabbruch muss
ein Administrator mögliche verwaiste Verzeichnisse prüfen. Ein Job-/Recovery-
System und Domänenlöschen oder -umbenennen sind noch nicht implementiert.

## Persönliche aktive Domäne [aktive-domaene]

```yaml block-meta
updated: "2026-11-11 17"
status: active
relations:
  - target: NAVIGATION.md#gruppierte-navigation
    type: reference
    reason: Gemeinsame Navigation mit Domänenswitcher
```

Die [gemeinsame Navigation](NAVIGATION.md#gruppierte-navigation) bietet
„Domäne“ und „Wechseln“. Die Auswahl wird mit
`ActiveDomain` pro angemeldetem Benutzer in der Datenbank gespeichert und
bleibt über neue Sitzungen hinweg erhalten. Andere Benutzer und die globale
Verfügbarkeit der Domänen werden nicht verändert.

Die Auswahl filtert Importläufe, Ausgabeübersicht, Dokumentlisten und Quellen.
Wissensnetz und Netz-Einstellungen bekommen
sie als URL-Kontext. „Alle / Arbeitsraum“ hebt den Listenfilter auf.
Der Arbeitsraum ist weiterhin der gemeinsame, domänenunabhängige Blockeditor;
er wird nicht durch eine Domänenwahl in einen anderen Speicher umgeschaltet.
Die Textwerkstatt-Demo bleibt unabhängig mit synthetischen Daten.

Explizite gültige Domänen in Listen-/Wiki-URLs überschreiben nur den Kontext
der betreffenden Seite, nicht die dauerhaft gespeicherte Auswahl.
Kurze Datenbaum-Domänennamen in Wiki-Links werden auf den vollständigen
Registry-Namen umgeleitet, damit Seite und API dieselbe Domäne verwenden.
Detail- und Revisionslinks bleiben direkt lesbar; der Switcher ist keine
Zugriffsschranke. Domänenspezifische Rollen und Leserechte sind nicht umgesetzt.
Falls eine gespeicherte Domäne aus der Konfiguration verschwindet, erscheint
eine Warnung statt einer stillen Ersatzwahl.

Historische Registry-Namen wie `ki:Books` und gespeicherte Quellnamen wie
`Books` werden beim Filtern gemeinsam berücksichtigt. Die Registrierung unter
`DOMAIN/FILEFORMAT/DATEI` verwendet den Verzeichnisnamen als Quellidentität.
Die Dokumentationsdomäne behält
ihren eigenen Namen.

## Hostintegration [hostintegration]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations: []
```

`knext/domains.py` erweitert die konfigurierte Registry pro Zugriff mit
verwalteten Domänen, ohne deren gemeinsamen Cache zu verändern.
`knext/wiki.py` verbindet diese Registry mit dem bestehenden
`wissenswiki_core`-Renderer und dessen API; Routen und JSON-Vertrag unter
`/wiki/` bleiben erhalten.

Migration `content.0005` ergänzt nur die Verwaltungs- und Auswahlmodelle.
Originalquellen, Extraktionen und Revisionen bleiben unverändert.
Anlegen und Wechseln sind CSRF-geschützte POST-Aktionen; Rücksprünge werden
auf erlaubte Hosts geprüft. Django Admin bietet lesende Inspektion der
verwalteten Domänen, nicht unkontrollierte Pfadbearbeitung.
