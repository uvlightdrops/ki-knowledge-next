---
title: "Quellen und Textwerkstatt"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: features
purpose: "Beschreibt die vorhandenen Arbeitswege von Quellenaufnahme bis Textbearbeitung, Wiederherstellung und Freigabe."
created: "2026-11-11T04:56:00+01:00"
updated: "2026-11-12 07"
update_reason: "Lesbare Zeilenumbrüche und höhere Zieltext-Kontrollansicht beschrieben"
status: active
relations:
  - target: "../architecture/CONTENT-MODELL.md"
    type: depends-on
    reason: "Identitäten, Relationen und kontextbezogene Gliederungen"
  - target: "README.md"
    type: parent
    reason: "Index der implementierten Features"
  - target: "../architecture/QUELLEN-UND-TEXTWERKSTATT.md"
    type: depends-on
    reason: "Quellidentität, unveränderliche Extraktion und Revisionsvertrag"
  - target: "IMPORT-PIPELINES-AND-DRAFTS.md"
    type: reference
    reason: "Unterstützte Formate, Verarbeitungsläufe und statische Ausgabe"
---

# Quellen und Textwerkstatt

## Einstieg [einstieg]

```yaml block-meta
updated: "2026-11-12 05"
status: active
relations:
  - target: ../architecture/ui/EDITOR-UND-KI.md#arbeitsraum
    type: reference
    reason: Nutzerbegriff Textwerkstatt und geplanter editorzentrierter Arbeitsraum
  - target: NAVIGATION.md#gruppierte-navigation
    type: reference
    reason: Gemeinsame Navigation zwischen den Anwendungsbereichen
```

Die **Textwerkstatt** umfasst die Arbeitswege zum Bearbeiten von Texten und
ihren Zusammenhängen. Hier sind die bereits verfügbaren Schritte beschrieben;
der [UI-Entwurf](../architecture/ui/EDITOR-UND-KI.md#arbeitsraum) entwickelt
ihre gemeinsame Oberfläche weiter.

Über die [Navigation](NAVIGATION.md#gruppierte-navigation) führen
`/content/sources/` zum Quellbestand und `/content/documents/` zur
Dokumentübersicht. Dort lassen sich Texte, Herkunft, frühere Fassungen und
Freigabestand direkt öffnen. Die [Domänenauswahl](DOMAENEN.md) begrenzt
die angezeigten Inhalte.

Werkstatt und Editor-Textliste zeigen Titel, Domäne, Ordner, Dateiname,
Arbeitsstand und Freigabe in eigenen Spalten. Die Filter stehen waagrecht
über der jeweiligen Spalte; Spaltenüberschriften wechseln zwischen
auf- und absteigender Sortierung. Filter und Sortierung gelten für den
gesamten angezeigten Domänenbestand und bleiben beim Seitenwechsel erhalten.
„Zurücksetzen“ entfernt die Tabellenfilter, nicht die aktive Domäne.
Ordner und Dateiname beziehen sich auf die Quelle: Der Ordner zeigt ihren
zuletzt registrierten Pfad innerhalb der Domäne. Ohne Pfadregistrierung
steht dort ein Strich; die DB-Arbeitsfassung hat keinen eigenen Dateipfad.

Der Arbeitsweg lautet: **Quelle erfassen → in Markdown umwandeln →
Text bearbeiten → Fassung freigeben → Ausgabe erzeugen**.
Die [alte Werkstatt-Demo](TEMPLATE-UND-THEME.md#textwerkstatt-demo)
zeigt separat Beispielinhalte.

## Quellen registrieren [quellen-registrieren]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
- target: ../architecture/QUELLEN-UND-TEXTWERKSTATT.md#bereitstellung-und-quelle
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

Die Quellenansicht zeigt bereitgestellte Dateien, etwa
`Books/epub/buch.epub`, sowie bereits erfasste Quellen. Name und Format
lassen sich filtern; mehrere Quellen können gemeinsam ausgewählt werden.

„Als Quelle registrieren“ bewahrt eine Kopie der Datei und öffnet ihre
Detailansicht mit Herkunft, Größe, Format und Prüfsumme. Die Umwandlung
in Markdown folgt als eigener Schritt.

„Aktuelle Datei prüfen / registrieren“ erkennt bereits erfasste Inhalte.
Eine veränderte Datei erhält einen neuen Quellstand; der registrierte
Stand bleibt erhalten, auch wenn die bereitgestellte Datei später entfernt
wird. Dateien bleiben an ihrem bisherigen Ablageort.

Unterstützte Dateien liegen unter `DOMAIN/FILEFORMAT/DATEI`; weitere
Unterordner sind erlaubt. Versteckte Einträge und nicht unterstützte
Formatordner werden ausgelassen. Symlinks, unlesbare Dateien und
überschrittene Größenlimits werden ausdrücklich zurückgewiesen.
Die Sicherung von Originalkopien und Markdown-Ergebnissen beschreibt
[Import und Jobs](IMPORT-UND-JOBS.md).

## Markdown zerlegen [markdown-zerlegen]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
- target: ../architecture/QUELLEN-UND-TEXTWERKSTATT.md#zerlegung-und-ausgangsstand
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

„In Markdown zerlegen“ wandelt die gespeicherte Quelle in bearbeitbare
Dokumente um, beispielsweise die Kapitel eines EPUB. Die Laufansicht zeigt
Fortschritt, verwendete Verarbeitungsversion, Warnungen und Fehler.

Danach lässt sich jedes Dokument bearbeiten oder sein unveränderter
Markdown-Ausgangsstand ansehen und herunterladen.

Ein vorhandenes Ergebnis derselben Verarbeitungsversion wird wieder geöffnet.
Fehlgeschlagene Läufe können ausdrücklich wiederholt werden. Eine neuere
Verarbeitungsversion kann neue Ergebnisse erzeugen; ältere bearbeitete
Dokumente bleiben erhalten.

Die Batch-Auswahl unter `/content/sources/` reiht mehrere Quellen ein;
`/content/` zeigt ihre Läufe. Unterstützte Formate beschreibt
[Importpipelines und Entwürfe](IMPORT-PIPELINES-AND-DRAFTS.md).

## Text bearbeiten [text-bearbeiten]

```yaml block-meta
updated: "2026-11-12 06"
status: active
relations:
- target: ../architecture/ui/EDITOR-UND-KI.md#arbeitsraum
  type: depends-on
  reason: Editorzentrierter Arbeitsraum mit zuschaltbaren Ansichten
- target: ../architecture/QUELLEN-UND-TEXTWERKSTATT.md#yaml-und-editor
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

Die Dokumentseite bietet Titel, Markdown-Textfeld und eine bereinigte
Vorschau der gespeicherten Fassung. Ungespeicherte Eingaben sind noch
nicht in dieser Vorschau zu sehen.

Metadaten aus dem ursprünglichen YAML-Header stehen getrennt und
schreibgeschützt neben dem Text. Sie bleiben beim Speichern erhalten.
Der bearbeitbare Redaktionstitel ist unabhängig vom ursprünglichen
Metadatenfeld `title`. Ein YAML-Header im Textfeld wird zurückgewiesen.

Der heutige Button „Als neue Revision speichern“ bewahrt eine neue Fassung.
Falls zwischenzeitlich jemand anderes gespeichert hat, wird ein Konflikt
angezeigt statt dessen Arbeit zu überschreiben.

Unter `/content/editor/` lässt sich ein Dokument für die neue Editoransicht
wählen. „Editor · Entwurf“ ist vorläufig in der INTERN-Navigation verankert.
Dokumentseiten und Werkstattübersicht verlinken ebenfalls auf den Editor.
„Editor breit · Entwurf“ öffnet unter `/content/editor-wide/` eine eigene
Textliste für die bildschirmbreite Variante. Beide Varianten bearbeiten
dieselben Dokumente und Sicherungsstände. Im geöffneten Editor wechseln
„Breite Ansicht“ und „Standardansicht“ zwischen ihnen; ungespeicherte
Eingaben vor dem Wechsel speichern.

Die breite Variante nutzt die gesamte verfügbare Bildschirmbreite.
Ohne KI liegt die Vorschau ab 751 Pixeln rechts neben dem Markdown-Editor.
Beim Öffnen der KI-Werkstatt nimmt diese den rechten Bereich ein;
die Vorschau liegt dann direkt unter dem Editor in derselben Breite.
Ab 1500 Pixeln erhält das Bubble-Netz eine eigene linke Spalte.
Auf kleineren Fenstern stehen die Bereiche untereinander.

Die Ansicht bietet Markdown-Textfeld und zuschaltbare Vorschau und
Bubble-Navigation. „Vorschau aktualisieren“ rendert die aktuellen Eingaben
bereinigt und erneuert ihre Gliederung, ohne zu speichern. Die Bubbles
markieren den direkten Abschnittstext einschließlich seiner Überschrift;
Verbindungslinien zeigen die Überschriftenhierarchie, keine fachlichen
Relationen. Suche und Abschnittsauswahl erschließen auch größere Texte.
Die Bubble-Darstellung ist auf 120 Treffer begrenzt; die Auswahl enthält alle.

Nach Textänderungen muss die Gliederung vor einer Abschnittsauswahl
aktualisiert werden. Ansichtsschalter erhalten Text und Auswahl.
Beim Verlassen mit ungespeicherten Änderungen erscheint eine Warnung.
Speichern nutzt dieselben Fassungen wie die bisherige Dokumentseite.
Bei einem Konflikt bleiben die Eingaben und ihr ursprünglicher Ausgangsstand
erhalten; „Gespeicherten Stand laden“ verwirft sie ausdrücklich.

Ohne JavaScript bleiben Speichern, gespeicherte Vorschau und Wiederherstellen
verfügbar; Bubble-Navigation und Eingabevorschau benötigen JavaScript.
Die KI-Werkstatt ergänzt [prüfbare Textvorschläge](#ki-textvorschlaege).
Der Attributeditor ist noch nicht angeschlossen.

## Editor kurz bedienen [editor-kurzanleitung]

```yaml block-meta
updated: "2026-11-12 05"
status: active
relations:
  - target: ../architecture/TEXTWERKSTATT-VERTRAG.md#editorvarianten
    type: reference
    reason: Gemeinsamer technischer Vertrag beider Editoransichten
```

1. Unter **INTERN → Editor breit · Entwurf** einen Text öffnen. Die
   Spaltenfilter helfen beim Finden nach Titel, Domäne, Ordner oder Dateiname.
2. Markdown bearbeiten und **Speichern** wählen. **Vorschau aktualisieren**
   zeigt die Eingaben und erneuert die Bubble-Gliederung, ohne zu speichern.
3. **Bubble-Netz**, **Vorschau** und **KI-Werkstatt** nach Bedarf zuschalten.
   Eine Bubble markiert ihren Abschnitt im Text.
4. Für KI zuerst Text markieren oder den ganzen Text wählen, einen Auftrag
   eingeben und optional eine Kontextvorlage einfügen. **Vorschlag erstellen**,
   Ergebnis prüfen und bearbeiten, dann **Übernehmen und speichern** oder
   **Verwerfen**. Bei verändertem Ausgangstext ist die Übernahme gesperrt.
5. Unter **Sicherungen** einen früheren Stand wiederherstellen. Speichern,
   Wiederherstellen und KI-Übernahme lassen die Freigabe unverändert.

## KI-Textvorschläge [ki-textvorschlaege]

```yaml block-meta
updated: "2026-11-12 07"
status: active
relations:
  - target: ../architecture/ui/EDITOR-UND-KI.md#ki-vorschlaege
    type: depends-on
    reason: Sichtbarer Kontext und bewusste Vorschlagsübernahme
  - target: KONFIGURATION-UND-START.md#ki-konfiguration
    type: reference
    reason: Betreiberaktivierung, Providerzugang und neutraler Verbindungstest
  - target: ../architecture/TEXTWERKSTATT-VERTRAG.md#markierungen-und-ki
    type: depends-on
    reason: Eindeutige Auswahlanker und geprüfter Ausgangsstand
  - target: ../architecture/KONFIGURATION-UND-KI.md#ki-funktionskarte
    type: reference
    reason: Trennung des implementierten Textworkflows von späteren KI-Fähigkeiten
  - target: ../architecture/KONFIGURATION-UND-KI.md#ki-bereinigung
    type: reference
    reason: Verbleibende Validierungs- und Datenverträge für den strukturierten Ausbau
```

Im Editor öffnet **KI-Werkstatt** den optionalen Bereich neben dem Text.
„Textauswahl verwenden“ übernimmt die markierte Stelle, „Ganzen Text
verwenden“ den vollständigen Body. Der tatsächlich gesendete Zieltext wird
schreibgeschützt angezeigt. Provider und Modell sind sichtbar.
Im breiten Editor erhält die KI-Spalte mehr Raum: Bei geöffneter Vorschau
ist die Kontrollansicht auf großen Bildschirmen mindestens 50 Prozent
breiter als in der früheren Anordnung mit separater Vorschauspalte.
„Zieltext · Original“ ist dort zwölf statt acht Zeilen hoch.
Lange Zeilen werden zur Anzeige umgebrochen, ohne seitliches Scrollen.
Dies ändert nicht den gesendeten Text.

Eine Vorlage hilft beim Korrigieren, klareren Formulieren, Zusammenfassen
oder Weiterentwickeln; der Auftrag bleibt frei bearbeitbar. Zusätzliches
Material und Attribute werden ausdrücklich als Zusatztext eingetragen.
Unter „Zusatzkontext ausdrücklich ergänzen“ lässt sich eine Kontextvorlage
wählen und mit „In Zusatzkontext einfügen“ an vorhandenen Text anhängen.
„Semantische Gliederung“ richtet die Bearbeitung auf zusammengehörige
Gedanken, sinnvolle Abschnittsgrenzen und prägnante Markdown-Überschriften
für die weitere Wissensverarbeitung aus. Der eingefügte Kontext bleibt
frei bearbeitbar; die Auswahl allein sendet keinen Auftrag.
Nur Zieltext, Auftrag und dieser Zusatzkontext gehen an den Provider,
nicht automatisch das übrige Dokument, sein Titel oder die Domäne.

„Vorschlag erstellen“ verändert den Arbeitsstand nicht. Der Ersatztext
erscheint neben dem Original und lässt sich vor der Übernahme bearbeiten.
„Übernehmen und speichern“ ersetzt genau den gewählten Bereich. War der
Ausgangstext noch ungespeichert, wird dieser vorher als eigener
Sicherungsstand bewahrt. Bereits gespeicherte Stände bleiben ebenfalls
erhalten; die Freigabe ändert sich nicht.

Bei verändertem Text, Titel oder DB-Arbeitsstand wird die Übernahme
abgelehnt. „Verwerfen“ verändert den Text nicht. Der letzte offene eigene
Vorschlag wird beim erneuten Öffnen des Editors wieder angezeigt; bei
abweichendem Ausgangstext bleibt er nur zum Vergleichen oder Verwerfen.
Nicht übernommene manuelle Änderungen am Vorschlag bestehen nur im Browser;
beim Verlassen erscheint eine Warnung.

Aufträge, Kontext, Ausgangspuffer, Textanker, Provider, Modell und Ergebnisse
bleiben in der DB nachvollziehbar. Nur der Auftraggeber darf seinen
Vorschlag übernehmen oder verwerfen. Es gibt noch keine automatische
Aufbewahrungsbereinigung. Der erste Anschluss erzeugt Textvorschläge;
strukturierte Attributänderungen und neue Blockidentitäten folgen separat.

## Historie und Wiederherstellung [historie-und-wiederherstellung]

```yaml block-meta
updated: "2026-11-12 00"
status: active
relations:
- target: ../architecture/ui/EDITOR-UND-KI.md#sicherungsstaende
  type: reference
  reason: Einfache Bedienung der gespeicherten Fassungen als Sicherungen
- target: ../architecture/QUELLEN-UND-TEXTWERKSTATT.md#revisionslinie-und-freigabe
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

Frühere Fassungen sind mit Zeitpunkt, Bearbeiter und Änderungsanlass
erreichbar. Jede lässt sich lesen, als Markdown herunterladen und mit
ihrem Vorgänger vergleichen. Der Vergleich umfasst Text und YAML-Header,
nicht den separat geführten Redaktionstitel.

„Diesen Stand als neue Revision übernehmen“ macht eine frühere Fassung
wieder zum aktuellen Arbeitsstand. Die bisherigen Fassungen bleiben
erhalten; zwischenzeitliche Änderungen werden auch hier geprüft.

Im neuen Editor sind frühere Arbeitsstände unter „Sicherungen“ erreichbar.
Der vorherige Stand ist vorausgewählt; andere Sicherungen lassen sich nach
Zeitpunkt, Titel und Bearbeiter auswählen. Vorheriges Lesen und Vergleichen
bleibt möglich. Wiederherstellen bewahrt den aktuellen gespeicherten Stand;
ungespeicherte Eingaben werden nach Bestätigung verworfen.
Die Speicherung erfolgt beim ausdrücklichen Speichern, Wiederherstellen
oder Übernehmen eines KI-Vorschlags. Automatische Sicherungen von Eingabepuffern sind noch
nicht implementiert.

## Gliederungen und Zusammenstellungen [gliederungen-und-zusammenstellungen]

```yaml block-meta
updated: "2026-11-12 05"
status: active
relations:
  - target: "../architecture/CONTENT-MODELL.md#app-und-grenzen"
    type: depends-on
    reason: "Vertrag und Abgrenzung der DB-basierten Zusammenstellungen"
```

Dokumente und frühere Fassungen verlinken ihre schreibgeschützte Gliederung,
auch mit tieferen Überschriften. Von dort sind Blocktexte und Herkunft
erreichbar.

Unter `/content/collections/` entstehen eigene Sequenzen, Hierarchien,
Sammlungen oder Netze. Titel, Herkunft und Domäne helfen bei der Auswahl.
Die Struktur wird derzeit als JSON bearbeitet; Beispiele stehen am Editor.
Ein Download ermöglicht ihre Wiederverwendung. Inhalte dürfen mehrfach
vorkommen. Unbekannte Ressourcen, kreisförmige Elternzuordnungen und
veraltete Bearbeitungen werden zurückgewiesen.

Der Ressourcenkatalog erschließt Dokumente, Blöcke, Ordner und
Zusammenstellungen mit ihren Beziehungen und gespeicherten Textständen.
Ordner dienen der Gruppierung. Die kompakte Beziehungstypentabelle zeigt
Bezeichnung, Schlüssel, Definition und Verwendung (aktiv oder nur lesbar).
Beziehungstypen lassen sich mit Definition ergänzen; die gemeinsame Werteliste beschreibt der
[Relationskatalog](KONFIGURATION-UND-START.md#relationenkatalog).
Beziehungen können Domänengrenzen überschreiten.

Diese Ansichten sind bisher tabellarisch. Ihre geplante Bearbeitung über
Wiki-Ansichten steht im
[Zusammenstellungskonzept](../architecture/ui/ZUSAMMENSTELLUNGEN.md).
Speichern einer Struktur gibt ihre Inhalte nicht automatisch frei.

## Freigabe und Grenzen [freigabe-und-grenzen]

```yaml block-meta
updated: "2026-11-12 05"
status: active
relations:
- target: ../architecture/QUELLEN-UND-TEXTWERKSTATT.md#grenzen-und-ausbau
  type: depends-on
  reason: Modellvertrag zum implementierten Ablauf
```

Nutzer mit Freigaberecht (`content.publish_content`) können die aktuelle
Fassung für die Ausgabe bestimmen. Weitere Bearbeitung oder
Wiederherstellung lässt diese Freigabe unverändert. HTML-Ausgabe verwendet
weiterhin die freigegebene Fassung:
[Import und Ausgabe](IMPORT-PIPELINES-AND-DRAFTS.md).

Angemeldete Nutzer teilen derzeit den Bestand. Private Arbeitsbereiche,
Domänenrechte, Annotationen und ein Attributeditor sind
noch nicht angeschlossen. Die Anwendung bewahrt Originale und ältere
Fassungen; sie ist kein manipulationssicheres Archiv.

Technische Modellentscheidungen und Anschlussgrenzen stehen im
[Architekturkonzept](../architecture/QUELLEN-UND-TEXTWERKSTATT.md).
