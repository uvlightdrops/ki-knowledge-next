---
title: "Zusammenstellungen bearbeiten"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Definiert den geplanten Wiki-Arbeitsweg zum Auswählen, Gliedern und Prüfen von Content-Zusammenstellungen."
created: "2026-11-11T15:18:00+01:00"
updated: "2026-11-11 15"
update_reason: "UI-Anforderungen mit dem umbenannten TODO-Index verbunden"
status: draft
semantic_blocks: [arbeitskontext, ansichten, bearbeitungsaktionen, relationen, speichern-und-konflikte, anschluss, abnahme]
relations:
  - target: "README.md"
    type: parent
    reason: "UI-Konzepte"
  - target: "WISSENSWIKI.md"
    type: depends-on
    reason: "Arbeitsumgebung für Vergleich und Komposition"
  - target: "../CONTENT-MODELL.md"
    type: depends-on
    reason: "Persistente Ressourcen, Platzierungen und Zusammenstellungen"
---

# Zusammenstellungen bearbeiten

Das Konzept beschreibt den geplanten interaktiven Anschluss an das Wiki.
Der derzeitige JSON-Editor ist kein Ersatz dafür. Noch offen sind die genaue
Erweiterungsschnittstelle des Core und die konkrete Gestaltung am Bildschirm;
die beschriebenen Aktionen sind noch nicht angeschlossen.

## Arbeitskontext [arbeitskontext]

```yaml block-meta
updated: "2026-11-11 15"
status: active
relations:
  - target: "WISSENSWIKI.md#ordered-composition"
    type: depends-on
    reason: "Kontextbezogene Komposition wiederverwendeter Inhalte"
```

Eine aktive Zusammenstellung verbindet die Bestands-, Netz-, Gliederungs-
und Inhaltsansichten. Ein kompakter Kontextkopf nennt Titel, Strukturform,
Speicherzustand und bei Quellgliederungen die gebundene Revision sowie
Schreibschutz. Die Domänenauswahl begrenzt die Suche, nicht automatisch
die Mitgliedschaft: bereits enthaltene domänenfremde Ressourcen bleiben
sichtbar und werden als solche gekennzeichnet.

Der Auswahlkontext unterscheidet Ressourcen und Platzierungen:

| Bezug | Bedeutung |
|---|---|
| Ressource | Dokument, Block, Ordner oder Zusammenstellung mit eigenständiger Identität |
| Platzierung | Ein konkretes Vorkommen dieser Ressource mit lokalem Schlüssel, Elternbezug und Position |
| Textstand | Optional gebundene Revision; sonst eine ausdrücklich bezeichnete Vorschau des aktuellen Entwurfs |

Die Auswahl einer Platzierung zeigt genau deren Textstand und Kontext.
Mehrere Vorkommen derselben Ressource bleiben unterscheidbar. Ein Wechsel
des Vergleichspaars leert weder die aktive Zusammenstellung noch deren
ungespeicherte Arbeitsfassung.

## Zusammenwirkende Ansichten [ansichten]

```yaml block-meta
updated: "2026-11-11 15"
status: active
relations:
  - target: "../../requirements/TODO-INDEX.md#ui"
    type: reference
    reason: "UI-Anforderungen zu Wiki-Inhalten und Beziehungswidget"
  - target: "WISSENSWIKI.md#local-workspace"
    type: depends-on
    reason: "Gemeinsame Auswahl für Bestand, Netz, Vergleich und Inhalt"
```

| Ansicht | Aufgabe |
|---|---|
| Bestand und Suche | Ressourcen nach Titel, Typ und Domäne finden; eine oder mehrere für das Hinzufügen auswählen |
| Zusammenstellung | Platzierungen als geordnete Liste, aufklappbare Hierarchie oder Mitgliedschaft zeigen und bearbeiten |
| Netz | Beziehungen erkunden; im Zusammenstellungskontext lokale Platzierungen und Querverweise zeigen |
| Inhalt und Vergleich | Ausgewählte Texte als bereinigtes Markdown lesen, Herkunft und Revision prüfen |
| Attribute | Ressourceneigenschaften, Dokumentkontext und Platzierungsangaben getrennt zeigen |
| Beziehungen | Typ, Richtung, Geltungsbereich und Begründung einer Verbindung bearbeiten |

Die Bestandsauswahl zum Hinzufügen ist von den beiden Vergleichsendpunkten
getrennt. Eine Auswahlaktion kann einen Vergleichsendpunkt ausdrücklich
setzen; sie verbindet oder speichert nichts nebenbei.
Das Beziehungswidget ist aufklappbar und anfangs geschlossen.
Inhaltsbereiche zeigen gerendertes Markdown; Quelltext bleibt eine
ausdrückliche alternative Ansicht. Fremdes HTML und aktive Inhalte werden
nicht ungeprüft ausgeführt.

Die Netzansicht unterscheidet im lokalen Modus Knoten anhand der Platzierung,
nicht nur der Ressourcen-ID. Ein globaler Ressourcenmodus darf mehrere
Vorkommen zusammenfassen, muss diesen Modus aber sichtbar kennzeichnen.
Das Öffnen einer referenzierten Zusammenstellung ist Navigation, keine
automatische rekursive Expansion.

Auf schmalen Bildschirmen wechseln Bestand, Gliederung und Inhalt als
erreichbare Bereiche; Auswahl und Änderungen bleiben beim Wechsel erhalten.
Fokus, Typbezeichnungen und Richtung dürfen nicht nur durch Farbe vermittelt
werden. Ein allgemeines frei anordbares Dashboard ist dafür nicht erforderlich.

## Platzierungen bearbeiten [bearbeitungsaktionen]

```yaml block-meta
updated: "2026-11-11 15"
status: active
relations: []
```

„Zusammenstellung anlegen“ erfasst Titel und Strukturform. „Zur
Zusammenstellung hinzufügen“ übernimmt ausgewählte Ressourcen als neue
Platzierungen. Bei Mehrfachauswahl bleibt die Reihenfolge der angezeigten
Auswahlliste vor dem Bestätigen prüfbar; technische IDs werden intern
aufgelöst und nicht abgeschrieben.

| Aktion | Verhalten |
|---|---|
| Hinzufügen | In Sequenz/Hierarchie an die gewählte Stelle, sonst als Mitglied aufnehmen |
| Erneut platzieren | Dasselbe Ziel mit neuer Platzierungsidentität aufnehmen; kein versehentliches Deduplizieren |
| Nach oben/unten | Unter Geschwistern verschieben; ein Teilbaum bleibt zusammen |
| Einrücken/ausrücken | In Hierarchien den Elternkontext ändern; keine Zyklen erzeugen |
| Revision wählen | Nur tatsächlich vorhandene Textstände anbieten; historische und ungebundene Vorschau unterscheiden |
| Entfernen | Nur Platzierung und betroffene lokale Kanten entfernen, nicht Ressource oder Inhalt |
| Quellgliederung übernehmen | Eine bearbeitbare eigene Zusammenstellung mit erhaltenen Ressourcen-/Revisionsbezügen anlegen |

Entfernen eines Elternknotens zeigt die betroffenen Nachfahren und
Querverweise vorab. Der Dialog bietet entweder den Teilbaum zu entfernen
oder die Kinder am bisherigen Elternort zu erhalten. Ohne Bestätigung
wird nichts entfernt. Tastaturbedienbare Aktionen sind der grundlegende
Bedienweg; Drag-and-drop kann dieselben Operationen ergänzen.

Sammlungen und Netze zeigen keine fachliche Rangfolge aus technischen
Positionswerten. Ein Wechsel der Strukturform, der Elternbezüge verlieren
würde, verlangt eine Vorschau und Bestätigung; die UI flacht nicht still
einen Baum ab. Quellgliederungen selbst bleiben schreibgeschützt.

Ein Inhaltswechsel innerhalb der Gliederung ist kein Textedit. „Inhalt
bearbeiten“ führt für DB-Blöcke zur Dokumentrevision in der Textwerkstatt;
die Strukturaktion schreibt nicht direkt in einen Block-Snapshot. Die
Vorschau berücksichtigt ausschließlich eigenen Abschnittstext und explizit
einbezogene Kinder, damit Kindertexte nicht doppelt erscheinen.

## Beziehungen im richtigen Kontext [relationen]

```yaml block-meta
updated: "2026-11-11 15"
status: active
relations: []
```

Globale Beziehungen verbinden Ressourcen unabhängig von ihrer Platzierung.
Lokale Querverweise verbinden zwei Platzierungen genau einer
Zusammenstellung. Der aktive Modus nennt ausdrücklich „Ressourcenrelation“
oder „Querverweis dieser Zusammenstellung“; Endpunkte tragen zusätzlich
Titel, Typ und gegebenenfalls ihren Gliederungspfad.

Elternverbindungen und Reihenfolge sind gesonderte Strukturinformationen.
Sie werden nicht durch „Beziehung anlegen“ zu einer fachlichen Behauptung.
Lokale Querverweise dürfen zyklisch sein; Elternzuordnungen nicht.
Bestehende Relationstypen stammen aus dem ausgewählten Datenzugang.
Die UI setzt ähnlich benannte Typen wie `reference` und `references`
nicht automatisch gleich.

## Speichern und Konflikte [speichern-und-konflikte]

```yaml block-meta
updated: "2026-11-11 15"
status: active
relations: []
```

Strukturänderungen bearbeiten zunächst eine lokale Arbeitsfassung.
Der Kontextkopf unterscheidet „Gespeichert“, „Ungespeicherte Änderungen“,
„Wird gespeichert“ und „Speichern fehlgeschlagen“. Eine ausdrückliche
Speicheraktion überträgt die vollständige Struktur mit ihrer erwarteten
Versionsnummer atomar an den bestehenden Dienst.

Validierungsfehler markieren die betroffene Platzierung oder Verbindung.
Bei HTTP 409 bleiben lokale Änderungen erhalten; die UI bietet das Laden
des neueren Serverstands zum Vergleich. Erneutes Speichern auf neuer Basis
erfordert eine bewusste Übernahme, keine automatische Überschreibung.
Beim Verlassen einer geänderten Arbeitsfassung wird vor dem Verwerfen gewarnt.
Während einer laufenden Anfrage sind konkurrierende Speicheraktionen gesperrt;
bei unklarem Netzergebnis wird zunächst der Serverstand geprüft.

„Änderung zurücknehmen“ vor dem Speichern betrifft die Arbeitsfassung.
Eine dauerhafte Revisionshistorie redaktioneller Zusammenstellungen existiert
im Modell noch nicht und wird von der UI nicht behauptet. Ebenso wenig
bedeutet Speichern eine Freigabe oder Veröffentlichung der enthaltenen Texte.

## Datenzugänge und Repo-Grenzen [anschluss]

```yaml block-meta
updated: "2026-11-11 15"
status: draft
relations:
  - target: "../CONTENT-MODELL.md#app-und-grenzen"
    type: depends-on
    reason: "Vorhandener DB-Anschluss und Grenze zur dateibasierten Wiki-API"
```

Die gemeinsame Wiki-Oberfläche liegt in `wissenswiki-core`. Ihre derzeitigen
Skripte sind an konkrete DOM-Elemente und eine dateibasierte API gebunden;
eine universelle Datenadapter- oder Widgetschnittstelle ist noch nicht
vorhanden. Der Anschluss ergänzt gezielt die benötigten Auswahl-, Inhalts-
und Aktionsschnittstellen, nicht einen zweiten Renderer in Next.

| Verantwortlich | Vertrag |
|---|---|
| Core | Wiederverwendbare Ansichten, Auswahlweitergabe und verständliche Aktionen; Solo-Wiki ohne DB nutzbar |
| Django-Adapter | Framework-Anbindung, Login und CSRF; keine eigene Content-Wahrheit |
| Next | DB-Ressourcen, Revisionsauflösung, Zusammenstellungen, Berechtigungsprüfung und Speicheroperationen |

Der nächste Implementierungsschritt benötigt einen expliziten Datenzugang
für DB-Ressourcen einschließlich Titel, Typ, Textstand und erlaubter Aktionen.
Er nutzt `save_collection` und die vorhandene Versionsprüfung; der aktuelle
HTML-Formularendpunkt ist noch kein vollständiger JSON-Schreibvertrag.
Rückmeldungen müssen strukturierte Validierungsfehler und Konflikte liefern.
Die genaue API- und Core-Schnittstelle ist vor dem Anschluss festzulegen.

Dateibasierte Wiki-IDs und DB-UUIDs sind getrennte Namensräume. Gleichheit
wird weder aus Titel noch aus Dateipfad geraten. Ein noch nicht erfasster
Dateiabschnitt lässt sich erst nach ausdrücklicher Aufnahme und nachweisbarer
Zuordnung in einer DB-Zusammenstellung platzieren. Die Aktion benennt diese
Voraussetzung, statt implizit Dateien zu importieren.

Anfangs ist der vollständige Arbeitsweg auf bereits indexierten
DB-Ressourcen umzusetzen. Eine spätere Verknüpfung beider Bestände braucht
einen eigenen Identitätsvertrag. UI-Fähigkeiten wie Bearbeiten, Verknüpfen
und Revision auswählen werden vom Datenzugang geliefert und serverseitig
erneut geprüft. Die persönliche Domänenauswahl ersetzt keine Zugriffskontrolle.

## Durchgängiger Arbeitsweg und Abnahme [abnahme]

```yaml block-meta
updated: "2026-11-11 15"
status: active
relations: []
```

Eine Person findet zwei indexierte Blöcke im Bestand oder Netz, öffnet sie
im Vergleich und fügt sie einer neuen Zusammenstellung hinzu. Sie platziert
einen Block nochmals, ordnet die Vorkommen um und macht eines zum Kind des
anderen. Ein lokaler Querverweis verbindet die gewünschten Vorkommen.
Die Inhaltsansicht zeigt die dazu gewählten Textstände. Nach dem Speichern
und erneuten Öffnen bleiben Struktur, Identitäten und Bindungen erhalten.

Der erste Anschluss ist abnahmefähig, wenn dieser Weg ohne JSON-Eingabe und
ohne manuelles Übertragen von IDs funktioniert. Zusätzlich müssen
Mehrfachplatzierung, Entfernen ohne Inhaltsverlust, Tastaturbedienung,
schmale Ansicht, Markdown-Darstellung, Quellgliederungs-Schreibschutz,
zyklische Querverweise und ein paralleler Speicherkonflikt prüfbar sein.
Ein unbekannter Dateiknoten darf nicht fälschlich als DB-Ressource erscheinen.
Die unveränderte Solo-Wiki-Funktion bleibt eine eigene Regressionsbedingung.
