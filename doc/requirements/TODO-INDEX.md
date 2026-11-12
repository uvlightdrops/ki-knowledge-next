---
title: "TODO-Index"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: requirements
purpose: "Thematischer Arbeitsvorrat mit eigenständig umzusetzenden einfachen Aufgaben und Konzeptverweisen für komplexere Themen."
created: "2026-11-11T14:46:00+01:00"
updated: "2026-11-12 05"
update_reason: "Spaltenfilter, Sortierung und kompakte Beziehungstypen im internen Bereich nach DONE aufgenommen"
status: active
relations:
  - target: "../README.md"
    type: parent
    reason: "Dokumentationsübersicht"
---

# TODO-Index

#### Verwendung dieses Dokuments

Einfache, klar abgegrenzte Punkte sollen eigenständig umgesetzt werden,
auch begleitend zu anderen Aufgaben, wenn sie fachlich passen und unabhängig
bearbeitet werden können. Sie sind Arbeitsaufträge, nicht nur vorgemerkte
Ideen; eine erneute Beauftragung ist nicht erforderlich. Dabei dürfen die
Hauptaufgabe und parallele Änderungen nicht beeinträchtigt werden.
Sie sind hier als einfache Listenpunkte gekennzeichnet.

Komplexere oder unklare Themen haben eine eigene Überschrift.
Sie erhalten zunächst einen klickbaren Konzeptverweis.

Erledigte Punkte werden in die jeweilige Unterrubrik DONE verschoben.

Dieser kurze Arbeitszettel benötigt keine YAML-Metadaten pro Abschnitt.
Stabile Abschnitts-IDs dürfen für Verweise erhalten bleiben.
Die Ausnahme gilt nur hier; Konzepte und Featuredocs behalten ihre Blockmetadaten.



## UI TODO [ui]

#### Navigation und UI pages aufbau

in der alten ki kn version hatten wir einigermaßen landing page aufgebaut.
Überlegen wir hierzu auch was.

#### Wissenswiki: Zusammenstellungen bearbeiten

[Konzept](../architecture/ui/ZUSAMMENSTELLUNGEN.md), noch nicht angeschlossen.

#### Editor generell

Offen sind Attributbereich, zusätzlicher Vergleich und strukturierte KI-Vorschläge.
[Editor- und KI-Entwurf](../architecture/ui/EDITOR-UND-KI.md)

#### Spielerische Seitenvarianten

Editorzentrierte Varianten erproben; jede angelegte Entwurfsseite zunächst
temporär in der gemeinsamen Navigation verankern.
[Entwurf](../architecture/ui/EDITOR-UND-KI.md#seitenentwuerfe)



### UI DONE

- Werkstatt und Editor-Textliste mit getrennten Herkunftsspalten,
  waagrechten Spaltenfiltern und auf-/absteigender Sortierung;
  Beziehungstypen als kompakte Tabelle.
  [Bedienung](../features/QUELLEN-UND-TEXTWERKSTATT.md#einstieg)
- Die gemeinsame Inhaltsseiten-Hülle zeigt keinen „Prototyp“-Hinweis mehr.
- Wiki-Inhaltsansichten und Bestandteile-Vorschau zeigen bereinigtes Markdown
  mit Überschriften, Listen, Tabellen und Codeblöcken; Quelltext bleibt zugänglich.
  [Umgesetzte Wiki-UI](../features/ui/INDEX.md#wiki-ui)
- Erster echter Markdown-Editor mit zuschaltbarer Bubble-Gliederung,
  Vorschau der Eingaben und Auswahl früherer Sicherungsstände.
  Vorläufiger Navigationseintrag „Editor · Entwurf“; bestehende Editorwege
  bleiben erhalten. [Bedienung](../features/QUELLEN-UND-TEXTWERKSTATT.md#text-bearbeiten)


## Input TODO

#### View content/sources

Tabellenansicht der files mit filter line darüber, nach allem was sinnvoll erscheint: Domäne, filename, filetyp, linux timestamps

### Input DONE

- Quellentabelle kompakter dargestellt.
- Gemeinsamer lokaler Web-/Workerstart und automatisch aktualisierte
  Job-/Batchseiten mit Workerstatus, Fortschritt und Fehlern.
  [Bedienung](../features/IMPORT-UND-JOBS.md#worker-und-fehler)
- Wartende Jobs seitenweise markieren und gemeinsam abbrechen; laufende
  Jobs und gespeicherte Nachweise bleiben erhalten.


## Wissen intern TODO

#### KI-Funktionen

Der erste Anschluss verwendet ki-core und die gemeinsame YAML-Auflösung.
Offen sind strukturierte Attributvorschläge, neue Blockgrenzen und die
Auswahl zusätzlicher Ressourcen als Kontext.

[Konzept und Übernahmebedingungen](../architecture/KONFIGURATION-UND-KI.md#ki-funktionskarte)

Begrenzte Aufträge statt vollständigem Domänenchat.
[Vorschlagsarbeit](../architecture/ui/EDITOR-UND-KI.md#ki-vorschlaege)

###### Texte semantisch aufteilen in kleinere Blöcke

###### Schlagworte erstellen



### intern DONE

- KI-Textworkflow im Editor mit Auswahl/Body, freiem Auftrag, Vorlagen und
  explizitem Zusatztext. Vorschläge prüfen, bearbeiten, verwerfen oder mit
  gesichertem Ausgangspuffer übernehmen; Freigabe und Originale bleiben
  getrennt. OpenAI-Zugang über ki-core mit neutralem Test geprüft.
  [Bedienung](../features/QUELLEN-UND-TEXTWERKSTATT.md#ki-textvorschlaege)




## Ausgabe TODO

Landing bzw index page
Tabellenansicht der ausgabe md bzw html mit filter line darüber, nach allem was sinnvoll erscheint: Domäne,

### DONE

**Umgesetzt:** `/content/output/` mit vorhandenen HTML-Site-ZIP-Downloads,
Domänenfilter und Leerstandsanzeige. Keine neue Publikationsfunktion.



## Deployment TODO [deployment]

#### Produktionsstart und HTTPS-Konfiguration

Gunicorn deklarieren und Produktionssettings mit dem tatsächlichen
Proxyvertrag prüfen. [Entwurf](../deployment/ENTWURF.md#produktionsintegration)

#### U7-/U8-Zielhostprofile

Manuelle Dienstvorlagen an den gemeinsamen Stackvertrag anschließen.
[Entwurf](../deployment/ENTWURF.md#produktionsintegration)

#### Wartung, Sicherung und Wiederherstellung

Deploylock, Writer-/Jobvertrag und konsistente Sicherung mit
Revisionsmanifest umsetzen.
[Entwurf](../deployment/ENTWURF.md#wartungsautomatisierung)

#### Praktische Host- und Restore-Abnahme

Gewählten Host und isolierte Wiederherstellung prüfen.
[Abnahme](../deployment/ENTWURF.md#betriebsabnahme)

## Dokumentation

### DONE

Übernahmekarte auf offene Anschlüsse verdichtet; Deploymentanalyse durch
[Stand heute und offene Integration](../deployment/ENTWURF.md) ersetzt.
Die [Betriebsgrundlagen](../deployment/BETRIEB.md) bleiben die Anleitung.
