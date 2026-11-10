---
title: "Dokumente und Blockattribute"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Unterscheidet Dokumente, Abschnitte und die Herkunft ihrer Attribute im Wissensnetz und schlägt eine klarere Darstellung sowie Anzeige-Presets vor."
created: "2026-11-10T07:47:00+01:00"
updated: "2026-11-10T09:04:00+01:00"
update_reason: "Umgesetzte Attributansichten und offene Frage zur Entstehung von Dokumenten ergänzt"
status: draft
semantic_blocks:
  - ausgangspunkt
  - bestehendes-verhalten
  - dokument-und-abschnitt
  - attributebenen
  - anzeige-presets
  - knoten-und-beziehungen
  - inhaltsanzeige
  - beispiel
  - umsetzung-und-pruefung
  - offene-entscheidungen
relations:
  - target: "README.md"
    type: parent
    reason: "Architekturindex mit diesem Konzept"
---

# Dokumente und Blockattribute

**Gesprächsentwurf mit teilweise umgesetzter Attributanzeige:** Ausgangspunkt sind die
Beobachtungen des Nutzers zur Vermischung von Block- und Dateiattributen und
zur Dokumentblase mit H1 und Einleitung. Die folgenden Vorschläge sollen diese
Unterschiede sichtbar machen, ohne vorhandene Beziehungen umzudeuten.
Die drei Attribut-Presets und die Gruppierung nach Herkunft sind umgesetzt.
Die weitergehenden Vorschläge zu Dokumentknoten und Einleitung bleiben offen.

## Ausgangspunkt [ausgangspunkt]

Das Netz stellt unterschiedliche Dinge mit ähnlichen Blasen und einer
gemeinsamen Attributtabelle dar. Dadurch erscheinen etwa die ID eines
Abschnitts und das Projekt aus dem YAML-Header wie gleichartige Eigenschaften.
Auch die Blase mit dem Dateititel wirkt zunächst wie ein weiterer
Inhaltsabschnitt.

Die zentrale Frage ist nicht nur, welche Attribute angezeigt werden, sondern:
**Was wurde ausgewählt, woher stammt eine Eigenschaft, und worauf bezieht sich
eine Beziehung?** Die Oberfläche sollte diese Fragen beantworten können, ohne
dass man die Quelldatei oder das Speicherformat kennt.

## Bestehendes Verhalten [bestehendes-verhalten]

Geprüft an `wissenswiki-core` am 2026-11-10:

- `documents.py` trennt den Text vor der ersten H2-Überschrift von den
  nachfolgenden H2-Abschnitten. H1 und Einleitung liegen gemeinsam in `intro`;
  H3 und tiefere Überschriften bleiben Teil ihres H2-Abschnitts.
- `domains.py` erzeugt pro Datei einen Dokumentknoten, auch ohne H1. Der erste
  H1 im Einleitungsbereich liefert seinen Titel, sonst dient der relative
  Dateipfad als Titel. Es gibt keine Prüfung auf genau einen H1.
- Der Dokumentknoten hat beispielsweise die ID `doc:BEISPIEL.md`, ein
  Abschnitt `doc:BEISPIEL.md#idee`. Ein `block_id` wie `idee` ist damit nicht
  domänenweit eindeutig, sondern zunächst innerhalb der Datei.
- Dokument und Abschnitt erhalten `datei`, `ordner` und
  `dokument_metadaten`. Die YAML-Metadaten der Datei werden also auch bei jedem
  Abschnitt mitgegeben; dadurch werden sie nicht zu abschnittseigenen Angaben.
- Eine YAML-Relation ohne `source` geht vom Dokument aus. Eine Relation mit
  `source: "#idee"` geht von diesem Abschnitt aus.
- Die Attributdarstellung flacht verschachtelte Daten ab. Im Vergleich und in
  den Einstellungen wird oft nur der letzte Namensteil angezeigt bzw.
  ausgeblendet. Dadurch ist die Herkunft eines Attributs schwer erkennbar.

Eigene Wiki-Blöcke im Arbeitsraum sind ein anderer Fall: Dort repräsentiert
eine Datei einen eigenen Block. Ihre Metadaten dürfen nicht allein deshalb
als dokumentweiter Kontext klassifiziert werden, weil sie in YAML gespeichert
sind. Entscheidend ist das fachliche Bezugsobjekt, nicht das Dateiformat.

## Dokument und Abschnitt [dokument-und-abschnitt]

**Vorschlag:** Die Anwendung unterscheidet ausdrücklich drei Begriffe:

| Begriff | Bedeutung | Darstellung |
|---|---|---|
| Dokument | Das gesamte Werk mit Titel, Einleitung und Abschnitten | Eigener Dokumentknoten |
| Dokumentabschnitt | Ein über H2 abgegrenzter Teil dieses Dokuments | Abschnittsknoten mit Bezug zum Dokument |
| Eigener Wiki-Block | Eigenständig verfasster Inhalt des Arbeitsraums | Wiki-Block mit eigener Identität |

Ein Dokumenttitel ist nicht dasselbe wie ein Dateiname. `BEISPIEL.md` kann
„Gedanken zur Zusammenarbeit“ heißen. Der H1 ist im vorgeschlagenen
Dokumentationsprofil der menschenlesbare Titel; der Dateiname bezeichnet den
Speicherort. Umbenennungen oder Verschiebungen sind davon getrennte Vorgänge.

Für dieses Profil ist **ein H1 pro Datei** sinnvoll. Der folgende Text bis zum
ersten H2 gilt als Einleitung. Sie ist Inhalt des Dokuments, aber zunächst kein
zusätzlicher, unabhängig identifizierter Block. Ein späteres ausdrückliches
Herauslösen in einen eigenen Abschnitt bleibt möglich.

Das ist eine Konvention für unsere Dokumentation, keine Behauptung über jede
beliebige Markdown-Quelle. Fehlender oder mehrfacher H1 sollte bei einer
entsprechenden Prüfung als Hinweis erscheinen, nicht stillschweigend zu
zusätzlichen Knoten führen.

Ein Dokumentabschnitt ist außerdem nicht automatisch ein fachlich bestätigter
Wissensblock: Die Überschriftengrenze beschreibt zunächst Textstruktur.

**Weitere Überlegung des Nutzers:** Die sequentielle Anordnung von Text ist
historisch durch das Papier geprägt. Ein längeres Dokument kann durch
Zusammenstellen ursprünglich eigenständiger Themen entstehen oder durch
Aufgliedern eines übergeordneten Themas in Aspekte. Die fertige Textfolge
allein macht diese unterschiedlichen Entstehungsweisen nicht transparent;
digitale Medien lösen diese Unklarheit nicht automatisch.

**Noch offene Folgerung:** Leseabfolge, Zugehörigkeit und Entstehungszusammenhang
sind möglicherweise verschiedene Beziehungen. Vor einer Modellentscheidung
sollten wir klären, was ein Gesamtdokument fachlich zusammenhält und ob seine
Entstehung überhaupt ausdrücklich festgehalten werden soll. Daraus werden
vorerst weder neue Relationstypen noch automatische Ableitungen aus H1/H2.

## Attributebenen [attributebenen]

**Vorschlag:** Die Attributtabelle gruppiert Angaben nach ihrem Bezug:

| Gruppe | Beispiele | Bedeutung |
|---|---|---|
| Ausgewähltes Objekt | Typ, vollständige Knoten-ID, Titel; bei Abschnitten lokale Block-ID | Identität und Eigenschaften der Auswahl |
| Dokumentkontext | Dokumenttitel, `project`, `scope`, dokumentweiter `status`, Zeitstempel | Angaben zum zugehörigen Dokument |
| Ablage und Technik | Relativer Pfad, Ordner, technische Revision | Speicher- und Betriebsinformationen |

Dokumentweite Angaben werden am Abschnitt als **Kontext aus dem Dokument**
gezeigt, nicht als dort eigens gepflegte oder fachlich vererbte Werte. Ein
dokumentweiter `status: draft` besagt beispielsweise nicht, dass jeder
Abschnitt eine unabhängig gepflegte Statusentscheidung besitzt.

Wenn später Abschnittsmetadaten hinzukommen, muss ihre Herkunft ausdrücklich
angegeben werden. Ein lokaler Abschnittsstatus und ein Dokumentstatus können
nebeneinander bestehen; eine automatische Überschreibungs- oder
Vererbungsregel ist hier nicht beschlossen.

Bei unterschiedlicher Auswahl, etwa Dokument links und Abschnitt rechts,
steht deshalb „nicht anwendbar“ bei der lokalen Block-ID des Dokuments.
„Nicht angegeben“ bezeichnet einen fehlenden Wert; beides ist von einem leeren
Text zu unterscheiden.

## Anzeige-Presets [anzeige-presets]

**Umgesetzt für Einstellungen pro Domäne im Browser:**

| Preset | Sichtbare Angaben |
|---|---|
| Nur Blockattribute | Eigenschaften des ausgewählten Objekts, ohne Dokumentkontext und Ablagetechnik |
| Alle Attribute | Alle Gruppen, jeweils mit sichtbarer Herkunft |
| Benutzerdefiniert | Individuelle Auswahl anhand eindeutig zugeordneter Attribute |

„Nur Blockattribute“ ist die gewünschte Kurzbezeichnung. Eine Erklärung sollte
präzisieren: Bei Auswahl eines Dokuments werden dessen eigene Eigenschaften
angezeigt, nicht ein erfundener H1-Block. Ob „Objekteigenschaften“ als
allgemeinere Bezeichnung verständlicher ist, bleibt zu erproben.

Als Einstieg bietet sich „Nur Blockattribute“ an; „Alle Attribute“ bleibt
direkt erreichbar. Typ und Identität sollten unabhängig von der frei
konfigurierbaren Tabelle in der Auswahlüberschrift erkennbar bleiben.

Die individuelle Auswahl muss den vollständigen Attributbezug verwenden,
nicht nur Kurznamen wie `status`. Sonst würde das Ausblenden des
Dokumentstatus versehentlich einen späteren Abschnittsstatus mit ausblenden.
Kurze Labels bleiben möglich, ergänzt um Gruppierung oder Herkunftshinweis.

Ein Preset blendet nur Angaben aus. Es entfernt keine Metadaten, verändert
keine Beziehungen und beschränkt nicht stillschweigend Suche oder Filter.
Eine vorhandene Browserkonfiguration mit ausgeblendeten Kurznamen wird
zunächst unverändert als benutzerdefinierte Ansicht gelesen. Beim Bearbeiten
wird ihre Wirkung für die aktuell vorhandenen Attribute in vollständige Pfade
überführt; die alte Konfiguration wird nicht gelöscht. Noch unbekannte
Attributpfade lassen sich aus dieser alten Auswahl nicht eindeutig ableiten.

Die Oberfläche gruppiert die tatsächlich gelieferten Attribute als
„Eigenschaften der Auswahl“, „Dokumentkontext“ und „Ablage und Technik“.
`dokument_metadaten.*` gehört zum Dokumentkontext; `datei`, `ordner` und
`revision` zur Technik. Die `metadaten.*` eigener Wiki-Blöcke bleiben dagegen
Blockattribute. Es werden keine zusätzlichen Attribute erfunden.
Die Auswahl gilt sowohl für den Vergleich als auch für die Einzelansicht.

## Knoten und Beziehungen [knoten-und-beziehungen]

**Empfehlung:** Den Dokumentknoten behalten, aber klar als Dokument
kennzeichnen, beispielsweise durch ein sichtbares Typetikett und eine andere
Form oder Kontur. Farbe allein sollte den Typ nicht vermitteln, weil sie
bereits für Ordner und Auswahl verwendet wird.

Ein Netzfilter könnte „Dokumente und Abschnitte“, „Nur Abschnitte“ und
„Nur Dokumente“ anbieten. Das ist eine eigene Einstellung, unabhängig vom
Attribut-Preset. Beim Ausblenden von Dokumenten bleiben deren Beziehungen
gespeichert; sie werden nicht auf die Einleitung oder sämtliche Abschnitte
umgebogen. Eine Anzeige wie „3 Dokumentknoten ausgeblendet“ macht die
eingeschränkte Sicht nachvollziehbar.

Die Dateistruktur stellt bereits fest, dass ein Abschnitt zu einem Dokument
gehört. Diese Struktur kann bei Bedarf als gesonderte, schaltbare
Containment-Verbindung dargestellt werden. Sie sollte nicht als manuell
angelegte fachliche Relation gespeichert werden müssen und nicht mit
redaktionellen Beziehungen vermischt werden.

Bei „Beziehung anlegen“ müssen die Endpunkte ihren Typ nennen:
„Dokument: Zusammenarbeit“ oder „Abschnitt: Zuständigkeiten“. Eine Relation
zwischen Dokumenten trifft keine automatische Aussage über jeden enthaltenen
Abschnitt. Ebenso beschreibt die Nachbarschaft zweier Abschnitte noch keine
Begründung oder Zustimmung.

## Inhaltsanzeige [inhaltsanzeige]

Das Widget „Blockinhalt“ sollte den Typ der Auswahl kenntlich machen:

- Bei einem Abschnitt: Abschnittstitel und vollständiger Abschnittstext.
- Bei einem Dokument: Dokumenttitel und ausdrücklich als **Einleitung**
  bezeichneter Text vor dem ersten H2.
- Bei einem eigenen Wiki-Block: Titel und vollständiger Blocktext.

Die Anzeige der Einleitung darf nicht den Eindruck erwecken, sie sei der
gesamte Dokumentinhalt. Eine Aktion „Ganzes Dokument ansehen“ könnte später
Einleitung und Abschnitte in ihrer Reihenfolge lesbar zusammenführen.
Ein Dokument ohne Einleitung erhält einen entsprechenden Hinweis, bleibt
aber als Dokument und Relationenziel vorhanden.

Der Dokumenttitel muss nicht nochmals als rohe `#`-Zeile im
Einleitungstext erscheinen. Eine spätere Darstellung kann ihn von der
Einleitung trennen, ohne die Markdown-Quelle zu verändern. Dafür ist eine
saubere Unterscheidung im Parser nötig; bloßes Abschneiden der ersten
Textzeile wäre bei fehlendem H1 oder Codebeispielen fehlerhaft.

## Beispiel [beispiel]

Eine Datei `ZUSAMMENARBEIT.md` enthält:

```markdown
---
project: ki-knowledge-next
status: draft
---
# Gemeinsames Arbeiten

Ein kurzer Einstieg in das Thema.

## Zuständigkeiten [zustaendigkeiten]

Autor und Prüfer übernehmen unterschiedliche Aufgaben.
```

Es entstehen ein Dokumentknoten „Gemeinsames Arbeiten“ und ein
Abschnittsknoten „Zuständigkeiten“, kein zusätzlicher Einleitungsknoten.
Beim ausgewählten Abschnitt zeigt „Nur Blockattribute“ etwa Typ,
vollständige Knoten-ID, Titel und lokale Block-ID. „Alle Attribute“ ergänzt
getrennt den Dokumentkontext (`project`, Dokumentstatus) und die Ablage.

Eine Beziehung auf `ZUSAMMENARBEIT.md` meint das ganze Dokument. Eine
Beziehung auf `ZUSAMMENARBEIT.md#zustaendigkeiten` meint den Abschnitt.
Die Einleitung erklärt den Gegenstand des Dokuments, ersetzt aber nicht
dessen Identität.

## Umsetzung und Prüfung [umsetzung-und-pruefung]

Die Gruppierung vorhandener Attribute und die drei Presets sind umgesetzt,
einschließlich vollständiger Attributpfade und Übergang bestehender
Browserauswahlen. Die darüber hinausgehenden Vorschläge bleiben Entwurf.

Die ursprüngliche Schrittfolge:

1. Typ und Attributherkunft im bestehenden Vergleich sichtbar machen.
2. Presets ergänzen; bestehende individuelle Auswahl und Speicherübergang
   ausdrücklich behandeln.
3. Dokumentknoten visuell unterscheiden und einen separaten Typfilter anbieten.
4. Inhaltswidget zwischen Einleitung und Abschnittstext unterscheiden lassen.

Vorhandene IDs und Relationsziele bleiben dabei unverändert. Eine spätere
pfadunabhängige Dokumentidentität ist eine gesonderte Entscheidung.

Für die Umsetzung sind insbesondere folgende Fälle zu prüfen: Dokument mit
und ohne Einleitung; fehlender oder mehrfacher H1; Dokument ohne H2;
gleichnamige lokale Block-IDs in verschiedenen Dateien; Auswahl von Dokument
und Abschnitt nebeneinander; gleichnamige Attribute verschiedener Herkunft;
ausgeblendete Dokumentknoten mit bestehenden Relationen; eigene Wiki-Blöcke
mit ihren tatsächlich blockbezogenen YAML-Metadaten.

## Offene Entscheidungen [offene-entscheidungen]

Soll das Netz standardmäßig Dokumente und Abschnitte zeigen oder bevorzugt
nur Abschnitte? Welche Unterscheidung der Knotentypen ist am lesbarsten?
Genügt zunächst Einleitung plus Dokumentverweis oder ist eine vollständige
Dokumentleseansicht schon für den ersten Schritt wichtig?

Die Empfehlung dieses Entwurfs ist: **Dokumente nicht entfernen, sondern
ihren Typ erklären; Abschnittseigenschaften und Dokumentkontext trennen;
Anzeige-Presets ergänzen, ohne fachliche Vererbung zu erfinden.**
