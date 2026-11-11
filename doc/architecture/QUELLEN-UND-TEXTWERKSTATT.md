---
title: "Quellen und Textwerkstatt"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Begründet Quellidentität, unveränderliche Markdown-Extraktion und Revisionsvertrag; Bedienung und Iststand stehen in der verknüpften Featurebeschreibung."
created: "2026-11-10T23:50:00+01:00"
updated: "2026-11-11 06"
update_reason: "Dateisystem-Abbilder und DB-Jobmanagement an den bestehenden Revisionsvertrag angeschlossen"
status: active
relations:
  - target: "../features/QUELLEN-UND-TEXTWERKSTATT.md"
    type: reference
    reason: "Implementierter Bedienablauf von Registrierung bis Historie"
  - target: "../../README.md"
    type: reference
    reason: "Einrichtung und Aktualisierung der lokalen Instanz"
  - target: "README.md"
    type: parent
    reason: "Architekturindex"
  - target: "../README.md"
    type: reference
    reason: "Einstieg in die Projektdokumentation"
  - target: "ALTREPO-UEBERNAHME.md"
    type: reference
    reason: "Übernahme von Workbench-Fähigkeiten ohne paralleles Inhaltsmodell"
  - target: "../features/IMPORT-PIPELINES-AND-DRAFTS.md"
    type: reference
    reason: "Nutzerabläufe, Formatadapter und Ausgabe des Importprototyps"
---

# Quellen und Textwerkstatt

## Modellentscheidung [modellentscheidung]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations:
  - target: TEXTWERKSTATT-VERTRAG.md#demo-und-ziel
    type: reference
    reason: Originale UI zunächst als Demo ohne konkurrierenden Inhaltsspeicher
```

**Nutzervorgabe:** Bereitgestellte Dateien sind noch keine importierten
Quellen. Nach Registrierung und Zerlegung bleibt das entstandene Markdown
unveränderlich; redaktionelle Arbeit beginnt in einer eigenen, eindeutig
nachvollziehbaren Revisionslinie. YAML-Dokumentmetadaten gehören nicht in
den Texteditor.

**Implementierter erster Stand:** Die vorhandene App `knext.content`
übernimmt diese Aufgaben gemeinsam. Die Ideen der alten Textwerkstatt
werden an dieses Modell angeschlossen; es entsteht keine zweite Datenbank
mit konkurrierenden Originalen, Entwürfen und Freigaben.
Die originale UI ist zunächst eine synthetische Read-only-Demo unter
`/workbench/`; ihr späterer Anschluss braucht die Änderungen im
[Textwerkstatt-Vertrag](TEXTWERKSTATT-VERTRAG.md).
Der aktuelle Bedienablauf steht in
[Quellen und Textwerkstatt](../features/QUELLEN-UND-TEXTWERKSTATT.md).

```text
data_dir/DOMAIN/FILEFORMAT/DATEI                  bereitgestellt
    │ ausdrückliche Registrierung
    ▼
SourceAsset + SourceRegistration                 registrierte Originalbytes
    │ ausdrückliche Zerlegung, versionierter ImportRun
    ▼
ContentDocument + ExtractionSnapshot             unveränderliches Markdown
    │ Ausgangsrevision
    ▼
ContentRevision 1 → 2 → 3 → …                     Textwerkstatt
    │ ausdrückliche Freigabe einer konkreten Revision
    ▼
freigegebene Revision → HTML / statische Site     Ausgabe
```

Diese Begriffe sind keine einzige Statusspalte. Eine Quelle kann mehrere
versionierte Läufe haben; ein erfolgreicher Lauf mehrere Kapitel liefern.
Ein Dokument kann zugleich eine neuere Entwurfsrevision und eine ältere,
weiterhin freigegebene Revision besitzen.

## Bereitstellung und Quelle [bereitstellung-und-quelle]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations:
- target: ../features/QUELLEN-UND-TEXTWERKSTATT.md#quellen-registrieren
  type: reference
  reason: Implementierter Ablauf zu diesem Konzept
```

Die Datenwurzel stammt aus `apps.ki_knowledge_next.paths.data`.
Beispiele sind `Books/epub/buch.epub` oder `Research/md/notizen.md`.
Unterhalb des Formatverzeichnisses sind weitere Verzeichnisse erlaubt.
Die Inventarisierung liest nur Dateinamen und Größen und verändert keinen
Quellbestand. Sie ist keine Registrierung.
Nur unterstützte Formatverzeichnisse werden weiter durchsucht; andere
Bestandsordner sind kein Teil dieses Importvertrags.

Erst die Registrierung übernimmt die aktuellen Originalbytes als
`SourceAsset` in die Datenbank. `SourceRegistration` hält den relativen
Bereitstellungspfad sowie Nutzer und Zeitpunkt fest. Das Original besitzt
eine UUID, SHA-256, Größe, Domäne und Format. Identität ist die Kombination
aus Domäne, Byteprüfsumme und Dateiformat: Identische Bytes in `.txt` und
`.md` haben unterschiedliche Interpretationsverträge.

Wiederholte Registrierung desselben Stands verwendet dieselbe Quelle.
Veränderte Dateibytes erzeugen eine neue Quelle, keine Aktualisierung des
alten Originals. Mehrere Pfade können auf denselben registrierten Stand
zeigen; der zuerst gespeicherte Originaldateiname bleibt erhalten.
Pfadregistrierung und heutiger Dateiinhalt sind deshalb getrennte Bezüge.

Die Zerlegung liest ausschließlich die gespeicherten Bytes. Eine anschließend
verschobene, geänderte oder gelöschte Bereitstellungsdatei verändert den
registrierten Stand nicht. Ein Upload bleibt als Abkürzung verfügbar und
führt Registrierung und Zerlegung unmittelbar nacheinander aus.

Die Registrierung akzeptiert nur reguläre Dateien bis 10 MiB, keine
Symlinks oder relativen Ausweichpfade. Dateiendung und Formatverzeichnis
müssen zusammenpassen; `markdown`, `htm` und `yml` werden als entsprechende
Formatverzeichnisse erkannt. Änderungen während des Lesens führen zu einem
Fehler statt zu einer unklaren Mischfassung. Eine fehlende Datenwurzel zeigt
einen leeren Bestand; nicht lesbare Wurzeln und zu große Verzeichnisbäume
werden als Fehler angezeigt.

## Zerlegung und Ausgangsstand [zerlegung-und-ausgangsstand]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations:
- target: ../features/QUELLEN-UND-TEXTWERKSTATT.md#markdown-zerlegen
  type: reference
  reason: Implementierter Ablauf zu diesem Konzept
```

Der `ImportRun` bindet eine registrierte Quelle an eine Pipeline-Version.
Die aktuelle Version heißt `content-import-v2`; ein bereits vorhandener
Lauf wird nicht stillschweigend neu ausgeführt. Fehlgeschlagene Läufe
können bewusst wiederholt werden. Eine neue Pipeline-Version erzeugt einen
eigenen Lauf, ohne alte Entwürfe zu überschreiben.
Ein fehlgeschlagener Lauf einer inzwischen abgelösten Pipeline kann nicht
unter seiner alten Versionsbezeichnung mit neuem Code wiederholt werden;
stattdessen wird die Quelle mit der aktuellen Pipeline neu zerlegt.

Der Formatadapter entscheidet über die Zerlegung: beispielsweise ein
Dokument je EPUB-Kapitel in Lesereihenfolge oder je Tabellenblatt.
`source_locator` und Adaptermetadaten halten die Herkunft fest.
Eine weitergehende semantische, gegebenenfalls KI-gestützte Zerlegung ist
ein späterer Verarbeitungsschritt, kein Grund, das Herkunftsmodell erneut
aufzubauen.

Jedes Ergebnis erhält einen `ExtractionSnapshot`: Markdown einschließlich
eventuell vorhandenem YAML-Header, extrahierter Titel, Adaptermetadaten,
Zeitpunkt und SHA-256 der UTF-8-Markdownbytes. Das ist der unveränderliche
Ausgangsstand, nicht die laufend bearbeitete Fassung.

Originalbytes und extrahiertes Markdown sind unterschiedliche Belege.
Ein Parser darf etwa Zeilenenden normalisieren oder EPUB-Markup in Markdown
übertragen; die exakten Ausgangsbytes bleiben im `SourceAsset`.
Ergebnisse eines Laufs werden gemeinsam mit ihren Ausgangsrevisionen
transaktional gespeichert. Ein Validierungsfehler darf keine halbe
Kapitelserie hinterlassen.

## YAML und Editor [yaml-und-editor]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations:
- target: ../features/QUELLEN-UND-TEXTWERKSTATT.md#text-bearbeiten
  type: reference
  reason: Implementierter Ablauf zu diesem Konzept
```

Vor der Übergabe an die Textwerkstatt trennt ein gemeinsamer Parser einen
am Dokumentanfang stehenden YAML-Header vom Markdown-Text. Der Header
bleibt als Rohtext erhalten, einschließlich Kommentaren, Anführungszeichen
und Begrenzungszeilen. Zusätzlich werden seine Werte als `frontmatter`
abgelegt; Datumswerte erhalten eine JSON-taugliche Darstellung.
Historische Adaptermetadaten bleiben daneben als Herkunftsinformation erhalten.

Der Editorvertrag liefert ausschließlich `body`; neue Textrevisionen
übernehmen den separat gespeicherten Header unverändert. Frontmatter im
Editor ist eine Vertragsverletzung, keine Aufforderung zur stillen
Metadatenänderung. Downloads rekonstruieren Header und Text.

Ungültige, doppelte oder nichttextuelle Schlüssel, nichtendliche Zahlen,
übermäßige Verschachtelung und übergroße Header werden abgelehnt.
Ein späterer Metadateneditor muss dieselbe Revisionslinie verwenden:
Headeränderung, Bearbeiter und Ausgangsrevision gehören zusammen.

Der bearbeitbare Redaktionstitel ist heute ein eigenes Revisionsfeld.
Ein eventuell im ursprünglichen YAML vorhandener `title` bleibt als
Quellmetadatum erhalten und wird bei einer Titeländerung nicht automatisch
umgeschrieben. Ein Export mit gezielt neu erzeugtem, aktuellem
Publikationsheader ist davon zu unterscheiden und noch nicht implementiert.

## Revisionslinie und Freigabe [revisionslinie-und-freigabe]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations:
- target: ../features/QUELLEN-UND-TEXTWERKSTATT.md#historie-und-wiederherstellung
  type: reference
  reason: Implementierter Ablauf zu diesem Konzept
```

Revision 1 übernimmt den Extraktionsstand mit getrenntem Header und Text.
Jede Bearbeitung erzeugt eine weitere `ContentRevision` mit:

- stabiler Revisions-ID und fortlaufender Nummer innerhalb des Dokuments;
- direktem Vorgänger, Bearbeiter, Zeitpunkt und Anlass;
- Titel, Text, rohem YAML-Header und Herkunftsmetadaten;
- Inhaltsprüfsumme über Titel, Text, Header und Herkunftsmetadaten.

Die erwartete aktuelle Revisionsnummer wird beim Speichern atomar geprüft.
Ein veralteter Editor erhält einen Konflikt, statt die inzwischen entstandene
Arbeit eines anderen Nutzers zu überschreiben. Revisionen selbst werden
nicht aktualisiert. Der veränderliche Dokumentkopf zeigt lediglich auf den
aktuellen Arbeitsstand und die ausdrücklich freigegebene Revision.

Eine Wiederherstellung erzeugt eine neue Revision mit `restored_from`;
sie setzt weder die Nummer zurück
noch löscht sie spätere Arbeit. Gleicher Inhalt kann deshalb dieselbe
Inhaltsprüfsumme haben, aber zu einem anderen Ereignis in der Linie gehören.

Freigabe bleibt ein eigener Vorgang mit Berechtigung. Bearbeitung und
Wiederherstellung verändern eine bestehende Freigabe nicht. Der statische
Export verwendet weiterhin exakt die freigegebene Fassung; das Site-Manifest
enthält zusätzlich Revisions-ID, Revisionsprüfsumme und Extraktionsprüfsumme.

## Integration des Altbestands [integration-des-altbestands]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations: []
```

Die alte Textwerkstatt liefert brauchbare Prinzipien: Quellstände festhalten,
private Arbeitsfassungen nachvollziehbar entwickeln und Vorschläge an eine
konkrete Revision binden. Die neue Umsetzung übernimmt zunächst diese
Herkunfts- und Revisionsgrenzen, nicht die alten Django-Modelle und Ansichten.

Bereits integriert sind Quellenregistrierung, unveränderlicher
Markdown-Ausgangsstand, headerfreier Editor, Revisionshistorie, Vergleich
und Wiederherstellung durch neue Revisionen. Vorhandene Next-Inhalte bleiben
in derselben App und behalten ihre IDs.

Noch nicht portiert sind private Kopien/Verzweigungen, Annotationen,
Anker-Rebasing, Chat und KI-Vorschläge samt Annahme. Spätere Vorschläge
referenzieren eine konkrete `ContentRevision`; ihre Annahme erzeugt eine neue
Revision über dieselbe Konfliktprüfung. Sie dürfen weder Original noch
Extraktionssnapshot ersetzen. Die
[Übernahmekarte](ALTREPO-UEBERNAHME.md) hält den breiteren Funktionsumfang fest.

## Bestehende Daten [bestehende-daten]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations: []
```

Die Migrationen `content.0003` und `content.0004` ergänzen das Modell und
übernehmen bereits importierte Next-Dokumente. Aus Revision 1 entsteht der
Extraktionssnapshot; ein zuvor nur als Metadaten erfasster Markdown-Header
wird aus dem gespeicherten Original rekonstruiert. Historische Revisionen
erhalten getrennte Header, Vorgänger und Inhaltsprüfsummen.

Dokument-/Revisions-IDs, Originalbytes und Freigabeverweise bleiben erhalten.
Die bestehenden Zeitpunkte werden nicht als neue Bearbeitungsereignisse
ausgegeben. Übernommene Revisionen tragen den Anlass `legacy`.
Dies ist keine Migration der privaten Datenbank des Altprojekts.

Vor einer lokalen Datenmigration ist eine geschützte SQLite-Sicherung
anzulegen; das ist kein automatisch vom Migrationscode ausgeführter Schritt.
Die Datenmigration ist bewusst nicht automatisch rückgängig
ausführbar; ein Rückweg benötigt das Backup und den passenden vorherigen
Code-/Schemastand.

## Grenzen und Ausbau [grenzen-und-ausbau]

```yaml block-meta
updated: "2026-11-11 06"
status: active
relations:
- target: ../features/QUELLEN-UND-TEXTWERKSTATT.md#freigabe-und-grenzen
  type: reference
  reason: Implementierter Ablauf zu diesem Konzept
```

Die Unveränderlichkeit wird derzeit an den Modell-, QuerySet- und
Admin-Grenzen der Anwendung durchgesetzt. Sie ist kein manipulationssicheres
Archiv: Direkte SQL-Zugriffe, Datenbankadministration und interne
Low-Level-ORM-Zugriffe müssen zusätzlich betrieblich eingeschränkt werden.
Prüfsummen sind Herkunfts-/Vergleichsbelege, keine digitale Signatur.

Alle angemeldeten Nutzer teilen weiterhin den Prototypbestand.
Domänenrechte, private Werkstätten, unveränderliche Auditprotokolle,
Aufbewahrungs-/Löschregeln und DB-seitige Schreibschutzregeln sind eigene
Ausbauschritte. Einzelverarbeitung bleibt synchron; ein separater serieller
Worker ergänzt Batchjobs und prüfbare Wiederaufnahme.
Harte Zeit-/Speicherlimits und Multi-Host-Verarbeitung fehlen noch.

Immutable Extraktionen werden nun als Dateisystem-Abbilder in die
dateibasierte Domäne geschrieben, ohne die aktuelle Revision oder Freigabe
zu verändern; siehe [Import und Jobs](IMPORT-UND-JOBS.md).
Publikationskomposition, semantisch
eigenständige Blockressourcen und spätere KI-Bearbeitung müssen an diese
Quell- und Revisionsverträge anschließen, statt neue Inhaltswahrheiten
daneben aufzubauen.
