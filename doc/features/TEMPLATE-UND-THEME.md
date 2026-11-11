---
project: ki-knowledge-next
scope: features
created: "2026-11-11 05"
updated: "2026-11-11 15"
update_reason: "Wiki-Interaktionsgrundlagen mit der vorhandenen Hosteinbindung verknüpft"
status: active
agent_project: ki-knowledge-next
relations:
  - target: ../architecture/ui/WISSENSWIKI.md
    type: reference
    reason: Fachliche Grundlagen der gemeinsam verwendeten Wiki-Oberfläche
  - target: README.md
    type: parent
    reason: Index der implementierten Features
---

# Templates und Theme

## Oberflächen und Django [oberflaechen-und-django]

```yaml block-meta
updated: "2026-11-11 15"
status: active
relations:
  - target: ../architecture/ui/WISSENSWIKI.md#local-workspace
    type: reference
    reason: Auswahl und zusammenwirkende Inhaltsansichten als UI-Grundlage
```

Django bleibt Anwendungshost und Backend: Anmeldung, Session, CSRF,
Berechtigungen, ORM/Migrationen sowie Import- und Revisionsdienste.
Eine React-Oberfläche ersetzt diese Aufgaben nicht. Wagtail ist nicht installiert.

| Bereich | Darstellung | Zuständigkeit |
|---|---|---|
| Import, Quellen, echter Editor, Domänen | Django-Templates | `knext/content/templates/content/base.html` als gemeinsame Basis; Domänenseite unter `knext/templates/domains.html` |
| Arbeitsraum, Wissensnetz, Einstellungen | HTML-Templates mit `string.Template` aus `wissenswiki_core/pages/` | `knext/wiki.py` verbindet gemeinsamen Renderer und API mit der erweiterten Domänenregistry |
| Textwerkstatt-Demo | Django-Shell und originale React-/Monaco-Assets | `knext/templates/workbench_demo.html`, `knext/workbench_demo.py` |
| Administration | Django Admin | `knext/templates/admin/base_site.html`; nur Staff-Nutzer sehen den Navigationslink |

`knext/templates/navigation.html` liefert Menü, Bereichslinks und Switcher
für die angemeldeten Anwendungsseiten. Die Wiki-Shell erhält dieses
vertrauenswürdige Host-Markup als `app_navigation`; ihre Vorlagen werden nicht
ins Hostprojekt kopiert. Statische HTML-Ausgaben enthalten keine App-Navigation.
Die Content-Herkunftsmodelle sind im Admin nur lesbar; Änderungen erfolgen
über ihre revisionsbewussten Anwendungsansichten.

## Arbeitsraum im Dark Theme [arbeitsraum-theme]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations: []
```

Der Arbeitsraum unter `/wiki/` verwendet nun ein dunkles Host-Theme für
Hintergrund, Blockbrowser, beide Editorflächen, Eingaben, Schaltflächen,
Vorschau und Statusmeldungen. Sichtbare Fokusrahmen bleiben erhalten.
Speichern, Blockauswahl und Beziehungen arbeiten unverändert.

`knext/content/static/knext/theme.css` definiert `--knext-*`-Farben und
gezielte Arbeitsraum-Overrides. Die Navigation bindet es nur im Arbeitsraum
ein, nach dessen ursprünglichem `workspace.css`. Damit bleiben Struktur und
responsive Regeln der gemeinsamen Komponente erhalten. Die Demo lädt dieselben
Grundfarben ausdrücklich in ihrer eigenen Shell.

Andere Bereiche behalten ihre vorhandenen Styles: Content-Seiten
`content/workbench.css`, Navigation `knext/navigation.css`, Wissensnetz und
Einstellungen die Styles aus dem Wissenswiki-Kern, Django Admin sein eigenes
Theme. Ein zentraler Hell/Dunkel-Umschalter ist nicht implementiert.

## Originale Textwerkstatt als Demo [textwerkstatt-demo]

```yaml block-meta
updated: "2026-11-11 05"
status: active
relations:
  - target: ../architecture/TEXTWERKSTATT-VERTRAG.md#demo-und-ziel
    type: depends-on
    reason: Grenze zwischen originaler UI-Demo und echtem Next-Revisionsvertrag
```

`/workbench/` zeigt die originale React-/Monaco-UI des Altprojekts.
Die gebauten Assets einschließlich Manifest, Markdown-Modul, Editorworker
und Lizenzhinweisen wurden unverändert aus Altstand `295ce7b` übernommen:
`knext/content/static/django_site/workbench/`.
Das ist keine Einbindung der alten Django-App oder ihrer Datenbank.

Die Read-only-Demo enthält ausschließlich synthetische Quellen,
eine Referenz, eine Arbeitskopie und Beispielmarkierungen. Alle angemeldeten
Benutzer können diese ansehen; Staff-Rechte sind dafür nicht erforderlich.
Die Quellenansicht wird über das alte Bootstrap-Feld `canCapture` eingeblendet.
Dieses Feld ist hier ausdrücklich **keine Schreibberechtigung**:
`/workbench/demo-api/` lehnt sämtliche Schreibmethoden mit HTTP 405 und einer
klaren Fehlermeldung ab. Der alte E1-/Staff-Hinweis erscheint dadurch nicht.

Die Arbeitskopie darf im lokalen Editorpuffer verändert werden, aber nicht
gespeichert werden. Eingaben gehen beim Neuladen verloren; der originale
Ungespeichert-Hinweis bleibt bestehen. Alte Aktionsknöpfe sind zum
UI-Vergleich weiterhin sichtbar. Kein Import, Archivieren oder KI-Aufruf
wird ausgeführt; der Provider-Endpunkt meldet ausdrücklich HTTP 501.
Leere Archiv-, Chat- und Vorschlagslisten sind der echte Bestand dieser
synthetischen Demo, nicht Ersatzantworten einer fehlenden Next-Anbindung.

Das ist noch **keine Read-only-Ansicht aller echten Next- oder Altinhalte**.
Echte Quellen und Dokumente bleiben unter `/content/sources/` und
`/content/documents/` erreichbar. Der spätere Anschluss wird im
[Vertragskonzept](../architecture/TEXTWERKSTATT-VERTRAG.md) beschrieben.

Die Demo-Shell erweitert CSP nur für ihre Monaco-Anforderungen:
Inline-Styles, `data:`-Schriften und Worker von derselben Origin beziehungsweise
`blob:`. Skripte bleiben auf dieselbe Origin beschränkt; `unsafe-eval` ist nicht
erlaubt. Andere Seiten behalten die strengere Standard-CSP.
