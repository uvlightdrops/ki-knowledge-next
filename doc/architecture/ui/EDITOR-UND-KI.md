---
title: "Markdown-Editor und KI"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Beschreibt den editorzentrierten Arbeitsraum, einfache Sicherungsstände und kontextbezogene KI-Vorschläge als noch auszugestaltenden UI-Entwurf."
created: "2026-11-11 20"
updated: "2026-11-12 07"
update_reason: "Generische Frameworkrecherche und Widgetkit-Erweiterung vom Editoranschluss abgegrenzt"
status: draft
relations:
  - target: ../../features/QUELLEN-UND-TEXTWERKSTATT.md#text-bearbeiten
    type: reference
    reason: Implementierter Editor mit zuschaltbarer Gliederungsnavigation
  - target: README.md
    type: parent
    reason: UI-Konzepte
---

# Markdown-Editor und KI

## Editor und zuschaltbare Ansichten [arbeitsraum]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
  - target: ../../features/QUELLEN-UND-TEXTWERKSTATT.md#einstieg
    type: reference
    reason: Bereits vorhandene Bearbeitungsabläufe der Textwerkstatt
  - target: WISSENSWIKI.md#local-workspace
    type: reference
    reason: Auswahl und Relationsvergleich als ergänzende Arbeitsmodi
  - target: ../TEXTWERKSTATT-VERTRAG.md#demo-und-ziel
    type: reference
    reason: Verbleibender technischer Anschluss an Next
```

**Textwerkstatt** bezeichnet aus Nutzersicht die zusammenhängenden
Bearbeitungsabläufe: Texte schreiben und korrigieren, Attribute pflegen,
Beziehungen bestimmen, Inhalte gliedern und KI-Vorschläge prüfen.
Der Begriff benennt weder ein bestimmtes Widget noch eine technische
Komponente, Speicherung oder ausschließlich die alte Werkstatt-Demo.
Einzelne Ansichten werden nach ihrer Aufgabe benannt, etwa Editor,
Vergleich oder Beziehungen.

Der Markdown-Editor bildet den Kern. Bubble-Netz als Navigation, Attribute,
zweiter Text und KI-Bereich werden je nach Aufgabe geöffnet oder geschlossen.
Die Textauswahl bleibt beim Umschalten erhalten. Zwei nebeneinanderliegende
Blöcke dienen dem Vergleich und Relationseditor, nicht als Pflichtlayout
jeder Textbearbeitung.

Der [einfache Einstieg](../../features/QUELLEN-UND-TEXTWERKSTATT.md#text-bearbeiten)
ist implementiert. Ein Attributbereich ergänzt später Dropdowns und Freitext;
Attributherkunft, zulässige Werte und die Trennung von Dokument- und
Blockattributen benötigen noch eine genauere Interaktionsgestaltung.

## Arbeitsstand und Sicherungen [sicherungsstaende]

```yaml block-meta
updated: "2026-11-11 21"
status: active
relations:
  - target: ../../features/QUELLEN-UND-TEXTWERKSTATT.md#historie-und-wiederherstellung
    type: reference
    reason: Vorhandene Speicherung und Wiederherstellung früherer Fassungen
  - target: ../TEXTWERKSTATT-VERTRAG.md#revisionen-yaml-konflikte
    type: reference
    reason: Interne Revisionen, Konfliktschutz und getrennte Freigabe
```

Die Bedienung zeigt einen aktuellen Arbeitsstand, Rückgängig im Editor
und wiederherstellbare Sicherungsstände. Vor größeren Ersetzungen und
KI-Übernahmen wird der vorherige gespeicherte Stand gesichert.
„Vorherigen Stand wiederherstellen“ ersetzt eine ständig sichtbare
Revisionsverwaltung; bei Bedarf sind weitere Sicherungen erreichbar.

Die vorhandenen Next-Revisionen tragen diese Sicherungen intern.
Veröffentlichte Fassungen bleiben vom Arbeitsstand getrennt.
Die Auswahl älterer gespeicherter Stände ist im Editor angeschlossen.
Speicherintervalle, Sicherung ungespeicherter Puffer und Aufbewahrungsgrenzen
sind noch festzulegen.

## Kontext und Vorschlagsarbeit [ki-vorschlaege]

```yaml block-meta
updated: "2026-11-12 00"
status: active
relations:
  - target: ../../features/QUELLEN-UND-TEXTWERKSTATT.md#ki-textvorschlaege
    type: reference
    reason: Implementierter Textworkflow mit expliziter Annahme
  - target: ../KONFIGURATION-UND-KI.md#ki-funktionskarte
    type: reference
    reason: Gemeinsame Provideranbindung und spätere KI-Fähigkeiten
  - target: ../TEXTWERKSTATT-VERTRAG.md#markierungen-und-ki
    type: reference
    reason: Ausgangsstand, Auswahlanker und sichere Annahme
  - target: WISSENSWIKI.md#conversation-and-proposals
    type: reference
    reason: Weiterführendes Gespräch als gesonderter Ausbau
```

Ein Auftrag besteht aus Vorgabe, ausgewählter Textstelle oder ganzem Text
und ausdrücklich hinzugefügtem Kontext. Weitere Blöcke und Attribute werden
sichtbar ausgewählt, nicht automatisch als vollständiger Domänenchat
übergeben. Vor dem Senden sind Kontext und Provider erkennbar.
Die Anbindung verwendet `ki-core` und die bestehende YAML-Auflösung;
erster Anschluss ist der bewährte OpenAI-Weg.

Der [erste Textworkflow](../../features/QUELLEN-UND-TEXTWERKSTATT.md#ki-textvorschlaege)
ist angeschlossen: freie Auswahl oder ganzer Body, Auftrag mit Vorlagen,
ausdrücklicher Zusatztext und ein bearbeitbarer Ersatzvorschlag. Die
Übernahme speichert nach Ausgangsprüfung und bewahrt auch einen bisher
ungespeicherten Ausgangspuffer. Die konkrete Bedienung und Grenzen stehen
in der Featurebeschreibung.

Ein Vorschlag steht neben dem Original und kann geändert, ganz oder
teilweise übernommen, verworfen oder mit einer weiteren Vorgabe bearbeitet
werden. Ein persistenter allgemeiner Chat ist keine Voraussetzung.
Providerfehler und ungültige Ergebnisse bleiben sichtbar.

Texterstellung und Korrektur liefern Textvorschläge. Als nächste Erweiterung liefern Schlagworte
Attributvorschläge; semantische Aufteilung liefert prüfbare Blockgrenzen
und Inhalte. Neue Blöcke entstehen erst nach ausdrücklicher Bestätigung.
Annahme prüft den Ausgangsstand und verändert keine veröffentlichte Fassung.

## Spielerische Seitenentwürfe [seitenentwuerfe]

```yaml block-meta
updated: "2026-11-12 06"
status: active
relations:
  - target: ../TEXTWERKSTATT-VERTRAG.md#editorvarianten
    type: reference
    reason: Gemeinsamer Speicher- und Aktionsvertrag der Editorvarianten
  - target: "#layout-presets"
    type: reference
    reason: Bewertung benannter Arbeitslayouts statt weiterer Seitenkopien
```

Oberflächen werden zunächst als eigenständige, veränderbare Seitenvarianten
erprobt. Jede angelegte Variante erhält vorläufig einen klar bezeichneten
Eintrag in der gemeinsamen Navigation, damit sie im normalen Arbeitsfluss
aufgerufen und verglichen werden kann.

Die Varianten beginnen beim Editor mit optionalem Netz und können Attribute,
Vergleich oder KI unterschiedlich anordnen. Demo-Daten und echte
Schreibaktionen sind unterscheidbar. Aus einer Variante folgt weder ein
dauerhafter Menüpunkt noch eine zweite Speicherung derselben Inhalte.
Die endgültige Gestaltung wird aus der gemeinsamen Erprobung abgeleitet.

Die erste echte Editorvariante ist als „Editor · Entwurf“ in INTERN
erreichbar. „Editor breit · Entwurf“ ergänzt eine bildschirmbreite
Variante mit Editor, optionalem Netz links und einem rechten Bereich
für die Vorschau oder KI. Bei geöffneter KI liegt die Vorschau unter
dem Editor.
Beide greifen auf denselben Inhalt zu; die breite Vorlage erbt die
gemeinsame Oberfläche, statt ihre Funktionen unabhängig zu kopieren.

## Layout-Presets und Widgetkit [layout-presets]

```yaml block-meta
updated: "2026-11-12 07"
status: draft
relations:
  - target: "#seitenentwuerfe"
    type: reference
    reason: Aktuelle Varianten als Grundlage der Erprobung
  - target: ../TEXTWERKSTATT-VERTRAG.md#editorvarianten
    type: reference
    reason: Unveränderter Speichervertrag unter verschiedenen Anordnungen
  - target: ../../../../../dev_doc/doc/architecture/LAYOUT-PRESETS-UND-WORKSPACES.md#widgetkit-erweiterung
    type: reference
    reason: Generischer Frameworkvergleich und optionaler Paketvertrag jenseits des Editors
```

Die [projektübergreifende Recherche zu Layout-Presets und Workspaces](../../../../../dev_doc/doc/architecture/LAYOUT-PRESETS-UND-WORKSPACES.md)
vergleicht Bootstrap/MUI, Qt, Eclipse, VS Code, JupyterLab und Golden Layout.
Sie trennt responsive Anordnung, Perspektiven, Speicherung und
Workflowregeln und beschreibt eine mögliche Widgetkit-Erweiterung.
Der folgende Abschnitt behandelt dagegen nur deren Anwendung im Next-Editor.

**Empfehlung:** wenige benannte Arbeitslayouts zuerst, frei verschiebbare
Widgets erst bei bewiesenem Bedarf. Presets beschreiben eine Aufgabe
und ihre Anfangsanordnung, nicht eine neue Seite oder Inhaltsspeicherung.
Die Auswahl eines Presets darf weder speichern noch einen KI-Aufruf auslösen.
Der aktuelle breite Editor ist weiterhin eine feste Variante;
eine Presetauswahl und persönliche Layoutspeicherung sind noch nicht umgesetzt.

| Ansatz | Eignung für den Editor |
|---|---|
| Benannte CSS-Grid-Presets | Kleiner Einstieg: „Schreiben“ mit Vorschau rechts, „KI-Bearbeitung“ mit rechter KI-Spalte und Vorschau unter dem Text, „Navigation“ mit zusätzlichem Netz. Gleiche DOM-Elemente, Formulare und Ereignisse bleiben erhalten. |
| Veränderbare Spaltenbreiten | Später sinnvoll innerhalb eines Presets. Begrenzte relative Gewichte statt gespeicherter Bildschirm-Pixel; zugängliche Tastaturbedienung und Zurücksetzen gehören dazu. |
| Widgetkit-Django-Builder | Wiederverwendbare Registry, Auswahl, Reihenfolge und Persistenz. Geeignet für freie Dashboardflächen; für gekoppelte Editorbereiche zunächst einen eigenen Hostadapter vorsehen. |
| Vollständig freies Docking | Hoher Aufwand für Fokus, Mindestgrößen, mobile Ansicht und Zustandserhalt. Für die gegenwärtige Aufgabe nicht erforderlich. |

### Geprüfter Bestand

Das frameworkneutrale
[Widgetkit](../../../../widgetkit/README.md) liefert `WidgetSpec`,
Payload-/Adapterverträge und Jinja-Rendering. Es ist kein vorhandener
Client-Dockingmanager. `WidgetSpec` und der Django-Vertrag `WidgetMetadata`
sind zudem nicht identisch: etwa `min_w` und `resizable` stehen im
Django-Protokoll, nicht im geprüften Core-Datentyp.

[Widgetkit-Django](../../../../widgetkit-django/docs/host-integration.md)
liefert `CallbackWidgetRegistry`, `LayoutPlacement`, `LayoutState`,
`LayoutStore` und einen Builder mit `add`, `remove`, `save-order`, `reset`.
Die bestehende Reihenfolgeaktualisierung bewahrt Konfiguration und
Dimensionen überlebender Widget-IDs. Sein
[Grid-Helfer](../../../../widgetkit-django/widgetkit_django/layout.py)
packt zeilenweise in zwölf Spalten;
die [Laufzeit-CSS](../../../../widgetkit-django/widgetkit_django/static/widgetkit_django/css/layout-grid.css)
nutzt Breiten-Spans, aber keine freien `x`-/`y`-/`h`-Platzierungen.
Eine Editor-/Vorschau-Gruppe oder verschachteltes Docking ist dadurch
nicht automatisch abgebildet. Der Builder verwaltet Bereiche/Seiten;
ein Katalog benannter Editor-Presets und deren Versionierung kommt hinzu.

Der [alte Host](../../../../ki-knowledge/doc/architecture/DJANGO-WAGTAIL-WIDGETKIT.md#widgetkit-integration)
zeigt die passende Trennung: Registry, Routen, Rechte und ORM-Speicher im
Host, generische Mechanik im Paket. Sein
[LayoutStore](../../../../ki-knowledge/ki_knowledge/django_site/layout_store.py)
lädt persönlich vor gemeinsam vor Default; „fehlend“ und „explizit leer“
sind verschieden. Atomare Speicherung ist vorhanden, aber der geprüfte
`LayoutStore`-Vertrag hat keine erwartete Revision für konkurrierende
Schreibvorgänge. Diese Garantie müsste vor dauerhafter Next-Nutzung
explizit ergänzt werden. Der Next-Editor verwendet derzeit keines der
beiden Widgetkit-Pakete.

### Vertrag für einen nächsten Anschluss

- **Identität:** stabile Panel-IDs (`writing`, `preview`, `network`, `ai`),
  stabile Preset-ID und Schemaversion. Layoutdaten enthalten ausschließlich
  Darstellung, niemals Textpuffer, Zugangsdaten oder Promptkontext.
- **Gruppen:** Bei offener KI bilden Editor und Vorschau eine gemeinsame
  Hauptspalte, sonst steht die Vorschau rechts.
  Pflichtbereich `writing` ist nicht entfernbar; Ausblenden von KI bedeutet
  nicht Verwerfen eines Vorschlags. Fachliche Mindestanforderungen ergänzt
  der Host über die allgemeine Widgetauswahl hinaus.
- **Zustand:** Presetwechsel ändert CSS-Klassen/Variablen und Sichtbarkeit,
  nicht DOM-Instanzen. Auswahl, Undo-Verlauf, Fokus, ungespeicherte Eingaben
  und laufende Anfragen bleiben erhalten. Läuft ein Aufruf, bleibt dessen
  Status auch bei verborgenem Panel erkennbar.
- **Persistenz:** zunächst versionierte Produktpresets und flüchtige
  Abweichungen. Bei gewünschtem geräteübergreifendem Speichern persönliche
  DB-Präferenzen nach Nutzer und Arbeitsfläche; Domäne nur bei tatsächlichem
  Bedarf. YAML bleibt für Produkt-/Betreiberdefaults, nicht als zweiter
  Speicher persönlicher Vorlieben. Lokaler Browserzustand eignet sich
  ergänzend für gerätespezifische Breiten, nicht als alleiniger gemeinsamer
  Layoutspeicher.
- **Auflösung:** persönliche Abweichung → freigegebene gemeinsame Vorgabe →
  Produktpreset. „Zurücksetzen“ entfernt die Abweichung. Ein leerer
  generischer Widgetkit-Layoutzustand wird im Editor nicht ungeprüft
  übernommen, weil der Schreibbereich obligatorisch bleibt.
- **Validierung:** erlaubte IDs und Größen serverseitig prüfen, Schema- und
  Presetversion migrieren, unbekannte/entfallene Panels sichtbar melden.
  Schreibzugriffe benötigen Login/CSRF, eine Layoutrevision und HTTP 409
  bei Konflikten; gemeinsame Presets benötigen eigene Betreiberrechte.
- **Responsivität:** ein Preset definiert semantische Bereiche und
  Größenverhältnisse, nicht eine Anordnung für jeden Bildschirm.
  Mindestbreiten lösen Umbruch aus. Bei wiederverwendbaren Widgets sind
  [Container Queries](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Containment/Container_queries)
  passender als ausschließlich globale Fenstergrenzen.
- **Zugänglichkeit:** logische DOM-/Lesereihenfolge erhalten; CSS-Grid
  verändert laut [MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Grid_layout/Accessibility)
  nicht automatisch die Tastaturreihenfolge. Kein positives `tabindex`
  als Reparatur für visuelles Umordnen. Drag/Resize braucht eine
  gleichwertige Tastaturalternative.

Vor einem Paketanschluss sind Presetwechsel mit schmutzigem Puffer und
offenem Vorschlag, alle Panelkombinationen, schmale Container,
Tastaturbedienung, fehlende/alte Layouts, Reset und konkurrierende Saves
abzunehmen. Zuerst lokal zwei bis drei Arbeitslayouts erproben; bei
Persistenzbedarf einen kleinen Next-Adapter für die vorhandenen
Widgetkit-Django-Verträge bauen, nicht die Legacy-Dashboardmodelle kopieren.
