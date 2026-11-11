---
title: "CMS und Veröffentlichung"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Trennt Redaktionsoberfläche, Wagtail-Option und statische Publikation und hält eine vorläufige Empfehlung für die Technologieentscheidung fest."
created: "2026-11-09T18:13:00+01:00"
updated: "2026-11-11 05"
update_reason: "Lokale Blockmetadaten und gezielte Blockrelationen ergänzt; keine doppelte Headerablage"
status: draft
relations:
  - target: "README.md"
    type: parent
    reason: "Architekturindex"
  - target: "KNOWLEDGE-DOMAIN-AND-LIFECYCLE.md"
    type: reference
    reason: "Fachliches Zielbild für Domänen und Lebenszyklus"
  - target: "../features/IMPORT-PIPELINES-AND-DRAFTS.md"
    type: reference
    reason: "Nutzerablauf bis zur statischen Veröffentlichung"
  - target: "AUSGABE-UND-PUBLIKATION.md"
    type: reference
    reason: "Übernahme des Ausgabebestands, autarker Buildkern und Baumexport bis PDF"
---

# CMS und Veröffentlichung

## Publikationsmodell [publishing-model]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations:
- target: ../features/IMPORT-PIPELINES-AND-DRAFTS.md#static-output
  type: reference
  reason: Implementierter Ablauf zu diesem Konzept
```

Die redaktionelle Anwendung und die veröffentlichte Site haben
unterschiedliche Aufgaben. Die Django-Anwendung verwaltet Anmeldung,
Arbeitsstände und Freigabe. Ein Exportprozess erzeugt aus freigegebenen
Revisionen eine statische HTML-Site, die unabhängig vom CMS ausgeliefert
werden kann.

Die gewünschte „schöne CMS-GUI“ ist der Arbeitsraum für Hierarchie,
gemeinsame Redaktion und Workflow. Die Navigation und die statische Ausgabe
sind daraus abgeleitete Publikation, kein zweiter Ort, an dem Inhalte parallel
bearbeitet werden.

## Redaktionsoberfläche [editorial-interface]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations: []
```

Für den Redaktionsablauf werden mindestens benötigt:

- Seiten und Inhalte hierarchisch ordnen und in der Navigation umsortieren;
- Entwürfe, Änderungen und Freigabestatus leicht erkennbar machen;
- mit anderen zusammenarbeiten, ohne Änderungen gegenseitig zu verlieren;
- Rollen für Autorenschaft, Prüfung und Veröffentlichung abbilden;
- eine Vorschau der späteren HTML-Ausgabe ermöglichen;
- nachvollziehbar halten, welche freigegebene Revision in einer Ausgabe
  enthalten ist.

Diese Anforderungen beschreiben den Bedarf, nicht bereits entschiedene
Modellklassen oder eine bestimmte CMS-Implementierung.

## Wagtail-Einordnung [wagtail-assessment]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations: []
```

**Projektstand:** Das neue Projekt nutzt Django 6 und `wissenswiki-django`.
Wagtail ist weder in `INSTALLED_APPS` registriert noch eine deklarierte
Projektabhängigkeit. Das Vorgängerprojekt hat Wagtail für redaktionelle
Hierarchien, Revisionen und Workflows eingesetzt; dieser Bestand ist eine
Erfahrungsquelle, aber kein automatischer Architekturentscheid für den
Neuaufbau.

Wagtail passt grundsätzlich zu hierarchischen Seiten, redaktionellen
Revisionen, Vorschau und Review-Workflows. Es bringt aber zusätzliche
Modelle, Abhängigkeiten, Bedienkonzepte und Integrationsaufwand mit. Vor
allem muss geprüft werden, wie Seiteninhalt, Wissensblöcke,
Quellherkunft und Importstatus zusammenspielen, ohne widersprüchliche
Wahrheiten oder doppelte Bearbeitungsflächen zu erzeugen.

Eine schlanke eigene Django-Oberfläche kann besser zum bestehenden
Markdown-/Wissenswiki-Kern passen, würde Hierarchie-Editor, Revisionen,
Rechte und Workflow jedoch selbst benötigen. Ein statischer Site-Generator
kann die Ausgabe bauen, ersetzt aber keine kollaborative CMS-Oberfläche.

## Vorläufige Empfehlung [recommendation]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations: []
```

**Wagtail jetzt nicht als gesetzt behandeln.** Zunächst den fachlichen
Redaktionsablauf, die Inhaltsstruktur und den statischen Export unabhängig
vom CMS festlegen. Danach Wagtail mit einem kleinen, realistischen
Redaktionsprototyp gegen eine schlanke Django-Oberfläche vergleichen.

Wenn hierarchische Seitenbearbeitung, Mehrbenutzer-Redaktion, Revisionen und
Freigabeworkflows von Anfang an zentrale Anforderungen sind, ist Wagtail ein
naheliegender Kandidat und sollte ernsthaft geprüft werden. Unabhängig davon
bleibt der Wissenskern CMS-neutral und der statische HTML-Build ein eigener
Ausgabeschritt.

## Entscheidungskriterien [decision-gates]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations: []
```

Eine Wagtail-Entscheidung wird fällig, sobald ein Prototyp mit echten
Redaktionsfällen folgende Fragen beantwortet:

1. Lassen sich Hierarchie und Inhalte so modellieren, dass Autoren sie ohne
   Django-Admin oder Dateipfade bearbeiten können?
2. Können gleichzeitige Änderungen, Revisionen, Vorschau und Freigaben
   verständlich und zuverlässig behandelt werden?
3. Bleiben Quellen, Wissensblöcke und CMS-Seiten konsistent, ohne Inhalte
   unkontrolliert zu duplizieren?
4. Kann der Export nur freigegebene Revisionen reproduzierbar als statisches
   HTML mit stabiler Navigation erzeugen?
5. Ist der zusätzliche CMS-Betrieb den Eigenbau einer schlanken Oberfläche
   wert?

Bis dahin lautet der Status **offen; kein Ersatz- oder Migrationsbeschluss**.
Das Produktziel und die Prozessgrenzen sind im [Domänen- und
Lebenszykluskonzept](KNOWLEDGE-DOMAIN-AND-LIFECYCLE.md) beschrieben.
Die Übernahme der alten Generatoren und der gemeinsame Weg zu eingebetteten
Ansichten, autarken Sites und PDF stehen in
[Ausgabe und Publikation](AUSGABE-UND-PUBLIKATION.md).
