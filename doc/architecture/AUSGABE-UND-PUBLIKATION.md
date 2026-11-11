---
title: "Ausgabe und Publikation"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Bewertet alte Ausgabebausteine und entwirft eine gemeinsame Komposition für eingebettete Ansichten, statische Sites und zusammengefasste Downloads."
created: "2026-11-10T20:55:00+01:00"
updated: "2026-11-11 05"
update_reason: "Lokale Blockmetadaten und gezielte Blockrelationen ergänzt; keine doppelte Headerablage"
status: draft
relations:
  - target: "../features/IMPORT-PIPELINES-AND-DRAFTS.md"
    type: reference
    reason: "Implementierte Einzel-HTML- und flache Domänen-ZIP-Ausgabe"
  - target: "README.md"
    type: parent
    reason: "Architekturindex"
  - target: "ALTREPO-UEBERNAHME.md"
    type: reference
    reason: "Übernahmekarte und gemeinsame Ressourcenverträge"
  - target: "CMS-AND-PUBLISHING.md"
    type: reference
    reason: "CMS-Entscheidung bleibt von der Ausgabeimplementierung getrennt"
---

# Ausgabe und Publikation

## Ausgabebestand [ausgabebestand]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations: []
```

**Nutzerziel:** aus Blockressourcen schöne Ausgaben erzeugen — in der App,
als autonome Website und als Download ganzer tiefer Markdown-Bäume bis
zum PDF. **Bewertung:** dafür ist beträchtlicher Altbestand brauchbar,
aber noch kein einheitlicher, freigabegesteuerter Ausgabekern vorhanden.
Der tatsächlich implementierte Downloadumfang steht in
[Importpipelines und Entwürfe](../features/IMPORT-PIPELINES-AND-DRAFTS.md).

| Bestand | Tatsächliche Leistung | Übernahme |
|---|---|---|
| `infosite/generator.py` und `PageSpec` | Rekursiver Seitenbaum wird als Markdown geschrieben | Kleiner Baum-/Writer-Vertrag nützlich; nicht mit dem HTML-Generator verwechseln |
| `services/generator.py` | Originalkopien, Mapping/Hierarchie, Index, Übersicht, Metadaten und statisches HTML | Planungs-/Navigationsideen übernehmen, großen Service in Komposition und Renderer aufteilen |
| `knowledge/record_export.py` | Geordnete Records mit Quellkontext als Markdown zusammensetzen | Gute Basis für „Auswahl wird Dokument“; Anker, Revisionen, Assets und Freigabe ergänzen |
| `django_site/infosite_records.py` | Aus gespeicherten Blockrecords ein InfoSite-Projekt erzeugen | Übergang von Ressourcen zu Publikation adaptieren; alte ORM-/Pfadbindung entfernen |
| InfoSite-Hierarchie und Mapping-Regeln | Quellen Zielen, Titeln, Slugs und Reihenfolgen zuordnen | Als Vorlage für eigene Publikationsstruktur verwenden |
| `services/output_registry.py` | Dateien als `GeneratedDocument` mit Quellbezügen im CMS registrieren | Herkunftsbezug behalten; konkurrierende Dateibearbeitung und DB-Bearbeitung vermeiden |
| Wagtail-Katalogseiten | Redaktionelle Beschreibung über bestehenden Quellen und Projekten | Optionaler CMS-Adapter, nicht Inhaltsspeicher für alle Ressourcen |
| `knowledge/generate.py` | Quiz, Flashcards, Zusammenfassungen, Glossar, Study Guide | Abgeleitete Lernmaterialien behalten und in die Formatpipeline einhängen |
| Neuer Next-Prototyp | Einzel-HTML und Domänen-ZIP aus explizit freigegebenen Revisionen mit Manifest | Vorhandene Freigabegrenze beibehalten; noch flach, ohne Assets und PDF |

In den gesichteten Generatoren und der gezielten Suche nach PDF-
Ausgabetechnik wurde **kein entsprechender Baum-zu-PDF-Exporter belegt**.
Die umfangreiche PDF-Verarbeitung im Altprojekt betrifft vor allem
Import und Extraktion; sie ist kein vorhandener PDF-Publikationsweg.

## Publikationskomposition [publikationskomposition]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations:
- target: ../features/IMPORT-PIPELINES-AND-DRAFTS.md#static-output
  type: reference
  reason: Implementierter Ablauf zu diesem Konzept
```

Eine Publikation ist eine **eigene, geordnete Sicht auf Ressourcen**.
Sie darf verschiedene Originaldokumente kombinieren oder ein Dokument
auf mehrere Seiten verteilen. Das physische Markdown-Layout ist dafür
eine mögliche Ausgangsstruktur, aber nicht zwingend das Endprodukt.

**Vorgeschlagener gemeinsamer Weg:**

```text
Ressourcen / Quelldokumente / Blockrevisionen
    -> explizite Auswahl + Rechte + freigegebene Stände
    -> geordnete Publikationsstruktur
    -> aufgelöster Build-Snapshot
    -> Markdown | HTML-Ansicht | HTML-Site | Druck/PDF
    -> Artefakt + Manifest
    -> optionaler, separater Veröffentlichungsauftrag
```

Diese Begriffe sind ein Entwurf, noch keine vorhandenen Next-Klassen.
Der Snapshot hält mindestens fest: Domäne, Ressourcen-IDs und Revisionen,
Reihenfolge, Strukturrevision, Freigabestand, Theme-/Renderer-Version,
Assets und deren Prüfsummen sowie Behandlung ausgeschlossener Inhalte.
Auch die Zusammenstellung selbst braucht eine Freigabe: Nur freigegebene
Textbausteine zusammenzusetzen ergibt nicht automatisch eine freigegebene Site.

Ein privater Arbeitsstand darf als autorisierte Vorschau sichtbar sein;
er darf nicht über denselben unmarkierten öffentlichen Exportweg
veröffentlicht werden. Wiederholte Builds sollen dieselben Inhalts- und
Navigationsentscheidungen ergeben. Eine byte-identische PDF-Datei ist
eine gesonderte Anforderung, etwa wegen Zeitstempeln und Schriftmetadaten.

## Formate und Umfang [formate-und-umfang]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations: []
```

| Auswahl | Mögliche Ausgabe | Status und Nutzen |
|---|---|---|
| Einzelblock / Abschnitt | Eingebettete Ansicht, Markdown, HTML-Ausschnitt | Ausbau; Quellbezug und Kontext optional sichtbar |
| Ein Dokument | Markdown, HTML, Druckansicht, PDF | Einzel-HTML aus Freigaberevision bereits vorhanden; weitere Formate Ausbau |
| Teilbaum einer Publikation | Markdown-Baum als ZIP oder zusammengefasstes Markdown | Ausbau; Baumstruktur und Lesereihenfolge ausdrücklich wählen |
| Teilbaum / kuratierte Sammlung | Eine HTML-Leseseite, ein PDF-Dokument | Ausbau; Inhaltsverzeichnis, stabile Anker und Herkunft pro Beitrag |
| Ganze Publikation | Autarke mehrseitige HTML-Site als ZIP | Flacher Domänenexport vorhanden; Hierarchie/Themes/Assets noch Ausbau |
| Lernmaterial | Webmodule, Karten-/Quizdaten, druckbare Lernhefte | Altgeneratoren vorhanden; Integration und Qualitätssicherung nötig |
| Weitere Zielformate | EPUB, DOCX oder Präsentationen | Option, kein belegter fertiger Export; EPUB-Import ist kein EPUB-Exporter |

Die Auswahl muss nicht auf einem gemeinsamen Dateiverzeichnis beruhen.
Eine kuratierte Sammlung kann beispielsweise Blöcke aus mehreren Quellen
mit eigener Einleitung und Reihenfolge enthalten, ohne diese Quellen
umzuschreiben. Redaktionelle Zusammenstellung ist damit auch für digitale
Inhalte ein sichtbarer Entstehungsschritt.

## Tiefe Bäume [tiefe-baeume]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations: []
```

„Diesen Baum herunterladen“ braucht einen klaren Vertrag:

1. **Start und Kanten:** aus der gewählten Publikationshierarchie absteigen;
   `related-to`, Zitate und andere semantische Relationen sind nicht
   automatisch weitere Kapitel. Bei Dateiimport kann der Ordnerbaum
   eine vorgeschlagene Hierarchie liefern.
2. **Reihenfolge:** gespeicherte Geschwisterreihenfolge verwenden;
   nicht zufällig Dateisystem-, Alphabet- oder Graphreihenfolge.
3. **Identität und Mehrfachverwendung:** Ressource und Einbauposition
   unterscheiden. Derselbe Block kann in mehreren Kontexten vorkommen.
   Ob er mehrfach erscheint oder nur referenziert wird, ist explizite
   Exportpolitik; Zyklen in der Publikationsstruktur zurückweisen.
4. **Inhaltsgrenzen:** Dokumenttitel und Einleitung als Dokumentkontext
   behandeln. Bei Abschnittsauswahl Einleitung nicht unbemerkt mitnehmen;
   bei Dokumentauswahl nicht doppelt als eigener Block ausgeben.
5. **Überschriften:** Titel im Zielkontext einordnen, Quellmarkdown nicht
   verändern. Bei Tiefe über H6 eine strukturelle Darstellung mit Pfad,
   Nummerierung oder gestalteten Abschnittstiteln statt ungültiger H7+.
6. **Anker und Links:** eindeutige Ausgabeanker aus Ressourcen- und
   Einbauidentität bilden; Markdown-/Blocklinks auf die enthaltenen
   Zielseiten oder Sammeldokumentanker umschreiben. Externe oder bewusst
   ausgelassene Ziele kennzeichnen, nicht auf private Serverpfade verweisen.
7. **Assets:** Bilder, Tabellen und benötigte Schriften/CSS nach
   Berechtigungs- und Lizenzprüfung bündeln; relative Pfade umschreiben.
   Nicht beim Rendern beliebige lokale Dateien oder Netzwerkziele nachladen.
8. **Grenzen und Fehler:** maximale Tiefe, Ressourcenanzahl, Gesamtgröße,
   Bilddimensionen und Laufzeit prüfen. Fehlende Assets/Revisionen
   sichtbar melden; fehlende Rechte nicht durch Manifest oder Links verraten.

Ein öffentlicher vollständiger Export scheitert an fehlender Freigabe,
statt still Teile wegzulassen. Eine ausdrücklich gewählte gefilterte
Ausgabe darf nur erlaubte Inhalte enthalten und muss ihren Umfang
verständlich ausweisen, ohne verborgene Ressourcentitel offenzulegen.
Das private Buildprotokoll darf detaillierter sein als das öffentliche
Ausgabemanifest.

## Generator und CMS [generator-und-cms]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations: []
```

**Empfehlung: eingebettet und autark, aber mit einem gemeinsamen Kern.**
Nicht zwei unabhängige Generatoren bauen.

| Schicht | Aufgabe |
|---|---|
| Headless Buildkern | Snapshot und Publikationsbaum auflösen, Links/Assets planen, Formate rendern; ohne Request oder Django-View nutzbar |
| Django-Adapter | Rechte, Auswahl, Vorschau, Freigabe, Jobs, Download und CMS-Integration |
| CLI-/Worker-Adapter | Denselben versionierten Snapshot außerhalb eines HTTP-Requests bauen |
| Statisches Artefakt | Ohne Django, Wagtail, KI oder laufende Datenbank auslieferbar |
| Zieladapter | Bewusstes Publizieren nach Dateisystem, WebDAV oder anderem gewählten Ziel |

„Autark“ hat zwei Bedeutungen: Die **erzeugte Site** muss unabhängig
laufen. Ein **Build ohne Django** benötigt zusätzlich ein exportierbares,
versioniertes Snapshot-/Assetpaket; ein CLI-Aufruf, der weiterhin auf die
Live-Datenbank zugreift, erfüllt das noch nicht.

Wagtail bleibt eine mögliche Redaktionsoberfläche für Hierarchie und
Workflow, nicht der unvermeidliche Renderer. Das ändert die offene
[CMS-Entscheidung](CMS-AND-PUBLISHING.md) nicht.
Ein Site-Generator wie MkDocs oder Hugo wäre ebenfalls nur ein Adapter
auf die vorbereitete Komposition. Noch ist keiner gewählt.

Für einen Vergleich reicht ein realistischer Prototyp: derselbe Snapshot
als eingebettete Ansicht, autarke Site und Sammel-HTML — mit tiefer
Hierarchie, Querverweisen, Tabellen/Bildern und einer späteren PDF-Ausgabe.
Dann entscheiden Theming, Wartbarkeit, Linkkontrolle und Druckqualität,
ob der bereinigte eigene Renderer oder ein externer Generator besser passt.

## PDF und Druck [pdf-und-druck]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations: []
```

„One page PDF“ ist noch mehrdeutig. Als erster Anwendungsfall wird hier
**ein zusammenhängendes PDF-Dokument aus dem gewählten Baum** vorgeschlagen,
normalerweise mit mehreren Druckseiten. Eine buchstäblich einzige, sehr
lange PDF-Seite ist eine andere Option und bleibt zu bestätigen.
Es ist keine stillschweigende Produktentscheidung für eines von beiden.

Für das normale Sammel-PDF braucht es Inhaltsverzeichnis, Dokumenttitel,
Abschnittsanker, sinnvolle Seitenumbrüche, druckbare Links, Kopf-/Fußzeilen,
Seitenzahlen und verlässliche Behandlung von Code und breiten Tabellen.
Gedruckte Herkunftsangaben müssen auf den verwendeten Stand zeigen.

**Technikvorschlag:** aus derselben Komposition eine Druck-HTML-Fassung mit
eigenem CSS erzeugen und einen begrenzten, isolierten PDF-Worker einsetzen.
WeasyPrint und Headless Chromium sind zu vergleichende Kandidaten,
keine bereits installierten oder ausgewählten Projektabhängigkeiten.
Beim Renderercheck sind Fonts, Sprache/Silbentrennung, SVG/Bilder,
lange Tabellen, Seitenzähler und interne PDF-Links entscheidend.

Eine echte Einseitenfassung benötigt zusätzlich eine maximale Seitenlänge
und definierte Zoom-/Lesbarkeitsgrenzen. Tiefe Bäume können PDF-/Viewerlimits
überschreiten; nicht still abschneiden und nicht ungefragt auf
mehrseitig umstellen. Ressourcenintensive Druckjobs gehören nicht in
einen synchronen Webrequest.

## Bereinigung und Abnahme [bereinigung-und-abnahme]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations: []
```

Konkrete Altlasten in `InfoSiteGeneratorService.generate_html_site`:
Die Navigation wird alphabetisch sortiert statt nach redaktioneller
Hierarchie. Ein aus `index.md` erzeugtes `index.html` wird anschließend
durch den generischen Navigationsindex überschrieben. Navigationslinks
werden umgerechnet; für normale Markdown-Links im Body ist in diesem
Pfad keine entsprechende Umschreibung zu sehen. Der HTML-Body wird dort
ohne die im Next-Prototyp vorhandene Sanitizerstufe eingebettet.

Auch die Record-Ausgabe ist zunächst schlicht: `records_to_markdown`
bewahrt Eingabereihenfolge und Quellpfadkontext, löst aber keine
verschachtelte Publikationsstruktur und keine stabilen Exportanker.
Quizfragen im heuristischen Altgenerator setzen die richtige Antwort
immer auf Option A; das ist keine fertige didaktische Qualität.

**Übernahmeabnahme:** Ein synthetischer tiefer Baum mit mehreren Quellen
muss in Site und Sammeldokument dieselbe Lesereihenfolge haben;
Titel/Einleitung nur einmal enthalten; alle internen Links und Assets
auflösen; identische Ressourcen mehrfach einbauen können, ohne
Ankerkollisionen zu erzeugen; Drafts und private Metadaten ausschließen.
Fehlende Ziele und ein während des Builds geänderter Live-Stand dürfen
kein teilweise veröffentlichtes Artefakt erzeugen.

Für PDF zusätzlich tatsächliche Seitenzahl/-größe und Vollständigkeit
prüfen, lange Codezeilen/Tabellen visuell kontrollieren und Grenzen mit
einem absichtlich zu großen Baum testen. Erst danach gilt der konkrete
PDF-Anwendungsfall als umgesetzt, nicht schon nach erfolgreicher
HTML-Erzeugung.

**Quellen und vorhandene Testansätze:**

- [`services/generator.py`](../../../ki-knowledge/ki_knowledge/services/generator.py):
  Zeilen 79–156 Komposition, 203–263 HTML, 657–844 Mapping/Reihenfolge.
- [`record_export.py`](../../../ki-knowledge/ki_knowledge/knowledge/record_export.py):10–31;
  [`infosite_records.py`](../../../ki-knowledge/ki_knowledge/django_site/infosite_records.py);
  [`output_registry.py`](../../../ki-knowledge/ki_knowledge/services/output_registry.py).
- [`PageSpec`](../../../ki-knowledge/ki_knowledge/infosite/models.py):59–72;
  [`Wagtail-Katalog`](../../../ki-knowledge/ki_knowledge/wagtail_cms/models.py):1–145.
- [`Lernartefakte`](../../../ki-knowledge/ki_knowledge/knowledge/generate.py):20–158;
  [`Next-Renderer`](../../knext/content/rendering.py):22–72.
- [`test_infosite.py`](../../../ki-knowledge/tests/test_infosite.py),
  [`test_infosite_from_records.py`](../../../ki-knowledge/tests/test_infosite_from_records.py),
  [`test_infosite_catalog.py`](../../../ki-knowledge/tests/test_infosite_catalog.py)
  und [`tests/test_content.py`](../../tests/test_content.py):
  Ausgangspunkte für Übernahmetests, noch keine Abnahme dieses Zielbilds.
