---
title: "Konfigurierbares Relationsvokabular"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Definiert Betreiberpresets, stabile Typbedeutungen und den gemeinsamen Katalogvertrag für Wiki und Next."
created: "2026-11-11 19"
updated: "2026-11-11 19"
update_reason: "Betreiberkonfiguration und erhaltender Presetwechsel ausgearbeitet"
status: active
relations:
  - target: README.md
    type: parent
    reason: UI-Konzepte
---

# Konfigurierbares Relationsvokabular

## Betreiberkatalog und Presets [betreiberkatalog]

```yaml block-meta
updated: "2026-11-11 19"
status: active
relations:
  - target: ../CONTENT-MODELL.md#ressourcen-und-relationen
    type: reference
    reason: Fachliche Relationstypen mit stabilen Schlüsseln und Definitionen
  - target: ../../features/KONFIGURATION-UND-START.md#relationenkatalog
    type: reference
    reason: Konfiguration des Vokabulars in YAML
  - target: ../../features/ui/INDEX.md#wiki-ui
    type: reference
    reason: Gemeinsamer Katalog für Sidebar und neue Beziehungen
```

Relationstypen sind ein betreiberbestimmtes Vokabular, keine universell
festgelegte Werteliste. Drei mitgelieferte Presets bilden unterschiedlich
umfangreiche Ausgangskataloge:

| Preset | Umfang |
|---|---|
| `basic` | `reference`, `part-of`, `composed-of`, `depends-on` |
| `documentation` | Basis plus `implements`, `extends`, `references`, `deprecates`, `parent`, `child` |
| `knowledge` | Dokumentation plus `supports`, `contradicts`, `questions` |

Standard ist `documentation`, damit die bisherigen sieben Wiki-Typen
verfügbar bleiben. Jeder Typ besitzt Schlüssel, Bezeichnung, Definition,
Farbe und Freigabe für neue Beziehungen. Individuelle Typen ergänzen das
Preset. Bestehende Presetschlüssel dürfen anders bezeichnet, eingefärbt oder
deaktiviert, aber nicht mit einer anderen Definition umgedeutet werden.
`reference` und das ältere `references` bleiben getrennte Schlüssel:
kein automatisches Umschreiben historischer Daten.

Die Wiki-API liefert den effektiven Katalog neben den Blockdaten.
Die Auswahl zeigt alle freigegebenen Typen, auch bislang unbenutzte.
Schreibaktionen im Arbeitsraum und Netz verwenden denselben Katalog.
Gespeicherte, nicht mehr freigegebene Typen bleiben lesbar, ohne automatisch
wieder anlegbar zu werden. Ein Vokabularwechsel verändert keine bestehende Kante.

Next ergänzt den Betreiberkatalog um eigenständig registrierte DB-Typen.
Bei neuen DB-Kanten wird eine benötigte Betreiberdefinition erst im
Schreibvorgang gespeichert; Seitenaufrufe legen keine Typen an.
Solche katalogverwalteten DB-Einträge bleiben nach einem Presetwechsel
historisch erhalten. Abweichende Bedeutungen derselben Schlüssel führen
zu einem ausdrücklichen Konflikt statt stiller Neuinterpretation.

Die Speicher bleiben getrennt: Wiki-Dateibeziehungen sind keine automatisch
importierten Next-Ressourcenrelationen. Geteilt wird das Vokabular,
nicht die Identität oder Speicherung der Kanten. Eine domänenspezifische
Vokabularauswahl ist nicht Teil dieses ersten Betreibervertrags.
