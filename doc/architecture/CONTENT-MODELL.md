---
title: "Content-Modell"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Beschreibt pfadunabhängige Ressourcen, typisierte Relationen und eigenständige Zusammenstellungen einschließlich historischer Markdown-Gliederungen."
created: "2026-11-11T14:30:00+01:00"
updated: "2026-11-11 19"
update_reason: "Betreiberkatalog und erhaltende Bearbeitung historischer Relationstypen verknüpft"
status: active
semantic_blocks:
  - graph-und-perspektiven
  - ressourcen-und-relationen
  - zusammenstellungen
  - markdown-und-revisionen
  - app-und-grenzen
relations:
  - target: "ui/ZUSAMMENSTELLUNGEN.md"
    type: reference
    reason: "Geplante Interaktion auf Ressourcen und Platzierungen"
  - target: "README.md"
    type: parent
    reason: "Architekturindex"
  - target: "DOKUMENTE-UND-BLOCKATTRIBUTE.md"
    type: reference
    reason: "Unterscheidung von Dokumentidentität und Blockkontext"
  - target: "../features/QUELLEN-UND-TEXTWERKSTATT.md"
    type: reference
    reason: "Bedienung der implementierten Zusammenstellungen"
---

# Content-Modell

## Grundentscheidung [graph-und-perspektiven]

```yaml block-meta
updated: "2026-11-11 14"
status: active
relations: []
```

Inhalte bilden kein einziges, global gültiges Buch. Ressourcen können beliebige
typisierte Beziehungen eingehen; eine Buchgliederung ist eine benannte
Perspektive darauf. Die Anwendung trennt deshalb **Identität**, **fachliche
Relation** und **Platzierung in einer Zusammenstellung**.

Reihenfolge bedeutet weder Zustimmung noch fachliche Abhängigkeit.
Über-/Unterordnung gilt nur innerhalb der jeweiligen Zusammenstellung.
Dokument- oder Ordnermetadaten werden nicht zu Blockattributen vererbt.
Bestehende Quellen, unveränderliche Revisionen und Freigaben bleiben erhalten.

## Ressourcen und Beziehungen [ressourcen-und-relationen]

```yaml block-meta
updated: "2026-11-11 19"
status: active
relations:
  - target: ui/RELATIONEN.md#betreiberkatalog
    type: reference
    reason: Betreiberpresets und gemeinsamer Vokabularvertrag für Wiki und DB
```

`ContentResource` besitzt eine UUID und einen Typ: Dokument, Block, Ordner
oder Zusammenstellung. Dokumente und ihre Blöcke verweisen auf das vorhandene
`ContentDocument`. Ordner sind ausdrücklich angelegte Gruppierungsressourcen,
keine automatisch synchronisierten Dateisystemverzeichnisse.
Zusammenstellungen sind selbst referenzierbare Ressourcen.

Eine explizite Markdown-ID bleibt innerhalb ihres Dokuments eindeutig.
Ihre technische Ressourcen-UUID ist vom Dateipfad, Titel und der Position
unabhängig. Ohne explizite ID wird eine technische UUID vergeben; unveränderte
Überschriften können eindeutig wiedererkannt werden. Umbenennung ohne
explizite ID begründet keine sichere Identitätsgleichheit. Entfernte Blöcke
bleiben als historische Relationsziele bestehen; sie werden nicht auf einen
anderen Block umgebogen.

`RelationType` hat einen stabilen Schlüssel, Bezeichnung und eine verpflichtende
Definition/Begründung. Erweiterungen sind möglich, aber keine unkontrollierten
Freitexttypen pro Kante. `ResourceRelation` verbindet beliebige Ressourcen,
auch domänenübergreifend und zyklisch. Eine optionale Begründung erklärt die
konkrete Relation. Relationstypen allein erzwingen keine Baumstruktur.
YAML-Relationen werden zunächst nicht automatisch als bestätigte DB-Relationen
übernommen; Quelldaten bleiben unverändert.

Der [Betreiberkatalog](ui/RELATIONEN.md#betreiberkatalog) ergänzt Presets
und eigene Definitionen. Deaktivierte oder aus einem Preset entfernte Typen
bleiben in gespeicherten Kanten erhalten, werden aber nicht für neue Kanten
angeboten. Bestehende DB-Kanten in einer Zusammenstellung dürfen bei einer
Bearbeitung erhalten bleiben; neue Kanten brauchen eine aktuelle Freigabe.

## Zusammenstellungen [zusammenstellungen]

```yaml block-meta
updated: "2026-11-11 14"
status: active
relations: []
```

`ContentCollection` benennt eine Perspektive mit Beschreibung und Domäne.
Vier Strukturformen werden unterstützt:

| Form | Vertrag |
|---|---|
| Sequenz | Flache, geordnete Einträge |
| Hierarchie | Geordnete Wurzeln und Kinder; keine Elternzyklen |
| Sammlung | Flache, fachlich ungeordnete Mitgliedschaft |
| Netz | Flache Mitgliedschaft mit expliziten Kanten zwischen Platzierungen |

`CollectionEntry` referenziert eine Ressource. Sein lokaler Schlüssel,
Elterneintrag und seine Position gehören ausschließlich zur Zusammenstellung.
Eine Ressource darf mehrfach erscheinen, auch unter unterschiedlichen Eltern.
Optional bindet ein Eintrag eine konkrete Dokumentrevision; bei Blöcken muss
der Block in dieser Revision vorhanden sein. Ohne Bindung wird keine
automatische Veröffentlichungszusage gemacht.

`CollectionLink` verbindet zwei Einträge derselben Zusammenstellung mit einem
Relationstyp und einer Begründung. So sind kontextuelle Kanten von globalen
Ressourcenrelationen unterscheidbar. Sie dürfen auch in Sequenzen oder Bäumen
zusätzliche Querverweise ausdrücken. Netzzyklen sind erlaubt; Elternzyklen
nicht. Referenzierte Zusammenstellungen werden als Verweise dargestellt,
nicht automatisch rekursiv expandiert; auch zyklische Verweise führen deshalb
nicht zu Endlosschleifen.

Bearbeitungen ersetzen die Zusammenstellung atomar und prüfen ihren erwarteten
Versionszähler. Veraltete Formulare erzeugen einen sichtbaren Konflikt statt
einer stillen Überschreibung. Es handelt sich noch nicht um eine vollständige
Revisionshistorie redaktioneller Zusammenstellungen.

## Markdown und Revisionen [markdown-und-revisionen]

```yaml block-meta
updated: "2026-11-11 14"
status: active
relations: []
```

Jede erfasste Revision erhält eine eigene, schreibgeschützte
Hierarchie-Zusammenstellung. H2 bis H6 bleiben als eigene Blöcke erhalten;
weitere H1 sind ebenfalls Gliederungspunkte. Ein führender Dokument-H1 bleibt
Teil der Einleitung. Übersprungene Ebenen hängen am nächsten tatsächlich
vorhandenen Vorfahren. ATX- und Setext-Überschriften werden außerhalb von
Codeblöcken erkannt. Die Indexierung ist ein Dokumentprofil, kein vollständiger
Markdown-Containerparser: Überschriften in Listen und Blockzitaten werden nicht
als eigenständige Dokumentabschnitte erfasst.

`BlockSnapshot` hält Titel, Quellzeilen, Ebene und direkten Abschnittstext
unveränderlich pro Ressource und Revision. Der direkte Text endet vor der
nächsten Überschrift, enthält also nicht nochmals sämtliche Kindertexte.
Einleitung, Originalmarkdown und YAML bleiben über die Revision zugänglich.
Dokument ohne Abschnitt bleibt eine gültige Ressource mit leerer Gliederung.
Doppelte explizite Block-IDs werden sichtbar abgewiesen, nicht still umbenannt.

Neue Extraktionen, Textrevisionen und Wiederherstellungen werden innerhalb
ihrer bestehenden Transaktion indexiert. Der wiederholbare Verwaltungsbefehl
`python manage.py index_content` ergänzt alte Revisionen ohne deren IDs, Texte,
Freigaben oder Prüfsummen zu verändern. Fehler werden mit Revisionsbezug
gemeldet; eine einzelne Revision wird nie teilweise indexiert.

## App und Grenzen [app-und-grenzen]

```yaml block-meta
updated: "2026-11-11 15"
status: active
relations:
  - target: "ui/ZUSAMMENSTELLUNGEN.md#anschluss"
    type: reference
    reason: "Datenzugänge und Zuständigkeit für den geplanten Widget-Anschluss"
  - target: "../features/QUELLEN-UND-TEXTWERKSTATT.md#gliederungen-und-zusammenstellungen"
    type: reference
    reason: "Implementierter Bedienablauf"
```

Die [Bedienung in der Textwerkstatt](../features/QUELLEN-UND-TEXTWERKSTATT.md)
beschreibt die konkreten Wege durch die Oberfläche.

Die Werkstatt verlinkt auf die jeweilige Gliederung. Der Bereich
„Zusammenstellungen“ bietet Lesen, Anlegen und Bearbeiten; ein strukturierter
JSON-Editor erfasst Platzierungen und Querverweise ohne feste Baumtiefe.
Ressourcenkatalog, Einzelansicht, Ordneranlage und Relationstypverwaltung
machen IDs und Bezüge auffindbar. Lesbare Tabellen ergänzen das Austauschformat.
Der Prototyp folgt den bestehenden gemeinsamen Schreibrechten angemeldeter
Nutzer; Freigaberechte für Inhalte werden dadurch nicht erweitert.

Diese Implementierung gehört zur DB-basierten Textwerkstatt. Die eingebundene
dateibasierte Wissenswiki-Netzansicht wird nicht heimlich umgestellt. Die
automatische Indexierung des gesamten Dateibestands, automatische
YAML-Relationsauflösung, visuelles Drag-and-drop, Publikationsgeneratoren für
Zusammenstellungen und deren versionierte Freigabe sind eigene Anschlüsse.
Eine gespeicherte Zusammenstellung veröffentlicht keine Entwurfsinhalte.

Der Editor erwartet ein Objekt mit `entries` und `links`. Ein Eintrag enthält
`key`, `resource` (UUID), optional `parent` (lokaler Schlüssel), `position`
(nichtnegative Ganzzahl) und `revision` (Datenbank-ID, nicht Revisionsnummer).
Eine Kante enthält `source` und `target` als Eintragsschlüssel, `type` als
Relationstyp-Schlüssel und optional `reason`. Der JSON-Download der
Zusammenstellungsansicht liefert die Struktur unter `structure` sowie die
Metadaten. Maximal 5000 Einträge/Abschnitte und 10000 Querverweise pro
Zusammenstellung begrenzen den Prototyp; die Hierarchietiefe hat kein eigenes
Limit. Katalogansichten sind paginiert.

Der geplante [Wiki-Anschluss](ui/ZUSAMMENSTELLUNGEN.md) verbindet
Ressourcenauswahl, Gliederung und Inhaltsvergleich. Er ersetzt die
JSON-Eingabe im normalen Arbeitsweg, ist aber noch nicht implementiert.
