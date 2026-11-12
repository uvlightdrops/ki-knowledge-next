---
title: "Konfiguration und KI"
project: ki-knowledge-next
agent_project: ki-knowledge-next
scope: architecture
purpose: "Bewertet den Konfigurationsstack und das übernehmbare Schema sowie den vollständigen KI-Funktionsumfang des Altprojekts."
created: "2026-11-10T20:55:00+01:00"
updated: "2026-11-12 00"
update_reason: "Umgesetzte Provider-/Schemaanbindung durch Featureverweise ersetzt und offenen Ausbau eingegrenzt"
status: draft
relations:
  - target: "../features/KONFIGURATION-UND-START.md"
    type: reference
    reason: "Implementierte YAML-Auflösung, lokale Startwege und Readiness"
  - target: "README.md"
    type: parent
    reason: "Architekturindex"
  - target: "ALTREPO-UEBERNAHME.md"
    type: reference
    reason: "Übergreifende Übernahmekarte und Ressourcenvertrag"
---

# Konfiguration und KI

## Konfigurationsentscheidung [konfigurationsentscheidung]

```yaml block-meta
updated: "2026-11-12 00"
status: active
relations:
- target: ../features/KONFIGURATION-UND-START.md#ki-konfiguration
  type: reference
  reason: Implementierter ki-core-Anschluss mit Betreiberaktivierung und neutralem Test
- target: ../features/KONFIGURATION-UND-START.md#konfiguration
  type: reference
  reason: Implementierter Ablauf zu diesem Konzept
```

Next verwendet `yaml-cfg-wizard` mit eigenem App-Schema und einem
gemeinsamen Loader für Django und `stackctl`. Layerpriorität, Pfade,
Credentials und Startwege stehen in
[Konfiguration und lokaler Start](../features/KONFIGURATION-UND-START.md).
Diese Basis ist implementiert.

`ki-core` ist eine deklarierte Next-Abhängigkeit und stellt Providerclients
sowie die gemeinsam konsumierten `llm`-/`http`-Schemaabschnitte.
Die [KI-Konfiguration](../features/KONFIGURATION-UND-START.md#ki-konfiguration)
bleibt in der projektlokalen Auflösung; die automatische Schema-/Home-Suche
des Altprojekts erweitert ihre Zuständigkeit nicht.

App-spezifische Felder gehören in das Next-Schema; gemeinsame
KI-Felder werden aus dem gemeinsamen Paket konsumiert.
Offen bleibt ein berechtigter Runtime-Editor über den generischen Dienst.
Ein gespeicherter Runtime-Wert kann durch höhere Konfigurationslayer
übersteuert bleiben und muss entsprechend angezeigt werden.

Das gemeinsame Schema kennt auch `llm.provider: auto`. Der Chatvertrag
unterscheidet bewusst zwischen Anzeigen ohne Netzwerkprobe und tatsächlicher
Providerauflösung beim Aufruf. Die Next-Textwerkstatt verlangt bereits
einen konkreten Provider und lehnt Auto-/Mockbetrieb für echte
Editoraufträge ab; das gemeinsame Basisschema bleibt allgemeiner.

## Schemaauswahl [schemaauswahl]

```yaml block-meta
updated: "2026-11-12 00"
status: draft
relations: []
```

**Empfehlung:** einen gemeinsamen Basisteil konsumieren und nur benötigte
Appfelder definieren. `apps.ki_knowledge_next` ist bereits der implementierte
Next-Namensraum für Pfade und Django; die nachfolgenden weiteren
Schemaabschnitte bleiben Übernahmevorschläge.

| Vorhandener Schemapfad | Entscheidung | Anpassung für Next |
|---|---|---|
| `version`, `system`, `logging` | Gemeinsame Basis prüfen | Nur benötigte Abschnitte konsumieren |
| `llm.provider`, `llm.providers.{ki,openai,ollama}`, `http` | In Next konsumiert | Konkreter Provider und Modell in Betreiberkonfiguration; Textwerkstatt ohne Auto-/Mock-Fallback |
| `profiles`, `stages` | Übernehmen | Aktivierung und Layer-Herkunft anzeigen; ausgewählte Layer, nicht alle Hosts zusammen laden |
| `stack` aus `config/defaults/stack.yaml` | Betriebsvertrag übernehmen | Eigene Dienste, Pfade, Ports und Startmodule; nicht den alten Vier-Dienste-Stack voraussetzen |
| `knowledge.default_domain`, `knowledge.embed_model` | Fachlich weiterführen | Zuständigkeit für aktive Domäne und Embedding-Profil festlegen |
| `knowledge.data_root`, `knowledge.paths.*` | Teilweise übernehmen | Explizite Wurzeln für Originale, Markdown, Zustandsdaten und Ausgabe; Next-Datenbank und Wiki-Quellen berücksichtigen |
| `knowledge.cache_db`, `knowledge.graph_db` | Nicht blind als Pflichtfelder | Nur bei gewähltem Storage-Adapter; keine fest einkodierten Legacy-Dateien |
| `infosite.{enabled,title,output_base_dir,domain}` | Als Migrationsquelle verwenden | Build-/Publikationsdefaults statt globalem zweitem Content-Modell; Titel und Struktur gehören überwiegend zur Zusammenstellung |
| `jira.*` | Optionaler Connector-Abschnitt | Verbindung und Importoptionen erhalten; Jira-spezifische DB-/Graphfelder nicht zu globalen Pflichten machen |
| `apps.ki_knowledge.nextcloud.*` | Optional übernehmen und umbenennen | Input-/Output-Trennung, TLS und Transferlimits erhalten; App-Passwort bleibt geheim |
| `apps.ki_knowledge.django.*` | Betriebliche Felder übernehmen | DB/Secret/Hosts/CSRF/HTTPS/Static/Media; `wagtail_admin_base_url` nur mit gewähltem Wagtail-Adapter |
| `apps.ki_knowledge.uberspace{7,8}.*` | Für gewählte Zielprofile übernehmen | Domain, DocumentRoot und BackupRoot; U8-Sonderbehandlung nicht global einschalten |
| `apps.ki_knowledge.distributed.*` | Später, separat | Federation ist nicht Voraussetzung für KI, Import oder gemeinsame Redaktion |

**Neue, noch zu spezifizierende Felder:** Importlimits, Adapteraktivierung,
Joblaufzeiten, Ausgabeformate/Themes, Ressourcenlimits für PDF, Embedding-
Versionsvertrag. KI-Eingabegrenzen stehen bereits in der
[KI-Konfiguration](../features/KONFIGURATION-UND-START.md#ki-konfiguration).
Weitere Werte brauchen Schemafelder
mit Bounds und Zuständigkeit, nicht versteckte Konstanten in Views.

Das alte App-Schema erlaubt in vielen Abschnitten `additionalProperties: true`;
dadurch sind unbekannte Felder dort nicht grundsätzlich ausgeschlossen.
Next sollte eigene abgegrenzte Objekte strenger definieren und Erweiterungen
gezielt zulassen. Fehlende Pflichtkonfiguration muss als Fehler erscheinen,
nicht durch weitere Default-Kaskaden unsichtbar werden.

## Wizard und Zuständigkeit [wizard-und-zustaendigkeit]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations:
- target: ../features/KONFIGURATION-UND-START.md#prioritaet-und-pfade
  type: reference
  reason: Implementierter Ablauf zu diesem Konzept
```

Der jüngere generische Runtime-Dienst ist weiter als der ältere Sync-Editor:
Er entdeckt geeignete Felder aus dem Schema, behandelt geheime/unsichere Werte
besonders und kennt Neustartgrenzen. Die App sollte diese gemeinsame
Implementierung verwenden und nicht noch einen YAML-Editor bauen.

Für Next sind fünf Klassen zu unterscheiden:

1. **Schema/Defaults:** versionierte, nicht geheime Produktvorgaben.
2. **Stage/Profile:** versionierte Umgebungs- und Nutzungsprofile.
3. **Runtime:** erlaubte lokale Overrides mit Validierung und Konflikterkennung.
4. **Secrets:** Zugangsdaten außerhalb öffentlicher Anzeigen und Git;
   niemals vollständige aufgelöste Config an Browser oder Supportausgabe senden.
5. **DB-/Nutzereinstellungen:** Redaktion, Berechtigungen und private
   UI-Präferenzen; keine konkurrierende YAML-Kopie derselben Entscheidung.

Schemafelder sollten explizit `x-secret`, `writeOnly` oder passende
Passwort-Metadaten verwenden; die Namensheuristik des Runtime-Dienstes allein
ist kein vollständiger Secretvertrag. Zulässige Schreibziele bleiben
serverseitig festgelegt, Änderungen benötigen administrative Rechte.

Die aktuelle Attribut-/Viewport-Auswahl im Browser ist eine
Benutzerpräferenz, keine Serverkonfiguration. Der Wizard ersetzt sie nicht.
Neustartbedürftig sind unter anderem Datenbank-/Pfad-/Dienständerungen.
Ein Embedding-Modellwechsel braucht zusätzlich einen Index-Neuaufbau;
„ohne Neustart gespeichert“ bedeutet nicht „vorhandene Vektoren kompatibel“.

## KI-Funktionskarte [ki-funktionskarte]

```yaml block-meta
updated: "2026-11-12 00"
status: draft
relations:
  - target: ../features/QUELLEN-UND-TEXTWERKSTATT.md#ki-textvorschlaege
    type: reference
    reason: Implementierter erster Textworkflow mit gesicherter Annahme
  - target: ui/EDITOR-UND-KI.md#ki-vorschlaege
    type: reference
    reason: Vereinbarter erster Anschluss mit ausgewähltem Text und Attributen
```

Der erste Anschluss verwendet `ki-core` und OpenAI für begrenzte
Editoraufträge und ist als
[KI-Textworkflow](../features/QUELLEN-UND-TEXTWERKSTATT.md#ki-textvorschlaege)
implementiert. Kontextwahl und Vorschlagsbedienung stehen im
[UI-Entwurf](ui/EDITOR-UND-KI.md#ki-vorschlaege). Die weiteren Fähigkeiten
bleiben Ausbauoptionen; ihr Umfang bestimmt nicht den ersten Arbeitsweg.

| Fähigkeit | Übernehmbarer Bestand | Anschluss und Aufwand |
|---|---|---|
| Provider und Modellauswahl | `ki_core.chat` | Erster Next-Anschluss implementiert; Konfiguration und Grenzen in der Featurebeschreibung |
| Allgemeiner Domänenchat | `django_site/chat_service.py`, `views_chat.py` | Späterer Ausbau; Speicherung und Kontextauswahl separat festlegen |
| Auswahlbezogene Aufträge | Next-Textworkflow | Textauswahl/Body und ausdrücklicher Zusatztext implementiert; Ressourcenpicker und Attributkontext bleiben offen |
| KI-Änderungsvorschläge | Next-Textworkflow | Textvorschläge mit Ausgangspuffer, Modell, Promptversion und Annahmerevision implementiert; strukturierte Attribute/Blockgrenzen bleiben offen |
| Promptbibliothek und Batch | `prompt_library.py` | Vorlagen und Backlog erhalten; Dateischreiben, Batchstatus und Konflikte an gemeinsamen Lauf-/Revisionsvertrag anpassen |
| Embeddings | `integrations/embeddings.py`, `block_embedder.py`, `block_embeddings.py` | Batchverarbeitung, Präfixe und veraltete Blöcke erhalten; Textbegrenzung und Modellidentität explizit versionieren |
| Semantische Suche | `django_site/block_search.py`, `KnowledgeStore.similar_blocks` | Retrieval aus erlaubten Quellen und gewähltem Revisionsstand; SQLite/pgvector nicht ungeprüft austauschen |
| Quellenbasierter Chat / RAG | `support_chat.py` | Kontextbelege, Block-IDs, Fehler bei fehlendem Index und explizite Nichtbeantwortbarkeit erhalten |
| Begriffe, Ontologien, Graph | `integrations/semantic_terms.py`, `integrations/knowledge_graph.py`, `knowledge/ontology_ingest.py`, Jira-Retrieval | Fachlich mitnehmen; source-spezifische Verfahren als Plugins, nicht als Pflicht für jede Domäne |
| Struktur und Qualität | `document_pipeline.py`, `structure_eval.py`, PDF-/TEI-Verarbeitung | Erkennung, Qualitätsmetriken und Evaluation weiterverwenden; nicht jedes Ergebnis ist KI-generiert |
| Lern- und Textartefakte | `knowledge/generate.py` | Quiz, Karten, Zusammenfassung, Glossar, Lernleitfaden erhalten; heutige Generatoren sind überwiegend deterministische Ableitungen |
| Älteres InfoSite-Refinement | `infosite_views.py:878–940` | Modi verbessern/strukturieren/zusammenfassen als Fähigkeiten erhalten, direkten Datei-Overwrite nicht übernehmen |

Retrieval, Quellenchat und Wissenserschließung erhalten eigene
Kontext- und Indexverträge, wenn sie angeschlossen werden.

## KI-Bereinigung [ki-bereinigung]

```yaml block-meta
updated: "2026-11-12 00"
status: draft
relations:
  - target: ../features/QUELLEN-UND-TEXTWERKSTATT.md#ki-textvorschlaege
    type: reference
    reason: Bereits umgesetzter Vorschlags- und Sicherungsvertrag als Grundlage des weiteren Anschlusses
```

Der weitere Anschluss baut auf dem
[implementierten Textworkflow](../features/QUELLEN-UND-TEXTWERKSTATT.md#ki-textvorschlaege)
und den Next-Inhaltsrevisionen auf. Strukturierte Attribute und neue
Blockgrenzen benötigen zusätzlich fachliche Ergebnisvalidierung.

Für den weiteren Ausbau bleiben folgende Paket- und Datenverträge wichtig:

- Der alte Config-Editor greift auch auf private `ki-core`-Hilfen zu.
  Gemeinsame öffentliche Verträge verwenden oder dort ergänzen, statt
  diese Paketkopplung in Next zu vervielfachen.
- Chat ist providerneutral, Embeddings sind im Altprojekt explizit
  Ollama-basiert. Diese Grenze zuerst erhalten oder bewusst migrieren;
  Chatproviderwechsel darf Vektorräume nicht heimlich verändern.
- Ein Embedding-Profil muss Modell, konkrete Version, Dimension,
  Vorverarbeitung/Präfix und Inhaltsrevision identifizieren. Der alte
  `model_key` vereinheitlicht `:latest`; das beweist keine Modellstabilität.
- Rechte und Freigabestand vor Auswahl des Retrievalkontexts prüfen.
  Quellenangaben müssen die verwendete Revision belegen, nicht nur den
  inzwischen veränderten Dateipfad.
- Strukturierte Antworten und fehlende Indizes brauchen nachvollziehbare
  Fehlerzustände zusätzlich zur bestehenden Behandlung von Text-/Providerfehlern.

## Abnahme und Quellen [abnahme-und-quellen]

```yaml block-meta
updated: "2026-11-11 05"
status: draft
relations: []
```

**Übernahme muss nachweisen:** dieselbe Configauflösung in CLI, Web und Worker;
sichtbare Layer-Herkunft; Secretredaktion; sichere und konfliktgeschützte
Runtime-Änderungen; Providerwechsel ohne Metadatenverlust; keine doppelte
Provideranfrage bei Wiederholung; Vorschlagsannahme nur auf passender
Revision; Rechtefilter im Retrieval; veraltete Embeddings nach Modell-/Textwechsel.

Codebelege und geeignete Tests zum Mitnehmen:

- [`ki_core/config.py`](../../../ki-core/src/ki_core/config.py):133–160 und
  277–295; [`Basisschema`](../../../ki-core/src/ki_core/schema/config.schema.yaml):25–145.
- [`App-Schema`](../../../ki-knowledge/schema/ki_knowledge.schema.yaml):1–296;
  [`app_config.py`](../../../ki-knowledge/ki_knowledge/app_config.py):20–116 und 186–225.
- [`RuntimeSettings`](../../../ki-core/src/ki_core/runtime_settings.py):19–120;
  [`live_settings.py`](../../../ki-knowledge/ki_knowledge/django_site/live_settings.py):14–53;
  [`config_editor.py`](../../../ki-knowledge/ki_knowledge/django_site/config_editor.py):113–175.
- [`llm_provider.py`](../../../ki-knowledge/ki_knowledge/llm_provider.py):1–76;
  [`ki_core/chat.py`](../../../ki-core/src/ki_core/chat.py):30–112;
  [`workbench_proposals.py`](../../../ki-knowledge/ki_knowledge/django_site/workbench_proposals.py):59–234;
  [`support_chat.py`](../../../ki-knowledge/ki_knowledge/django_site/support_chat.py):79–212.
- [`block_embedder.py`](../../../ki-knowledge/ki_knowledge/integrations/block_embedder.py):32–110;
  [`block_search.py`](../../../ki-knowledge/ki_knowledge/django_site/block_search.py):20–58.
- Tests:
  [`test_llm_provider.py`](../../../ki-knowledge/tests/test_llm_provider.py),
  [`test_config_editor.py`](../../../ki-knowledge/tests/test_config_editor.py),
  [`test_app_config_cache.py`](../../../ki-knowledge/tests/test_app_config_cache.py),
  [`test_workbench_backend.py`](../../../ki-knowledge/tests/test_workbench_backend.py),
  [`test_workbench_proposals.py`](../../../ki-knowledge/tests/test_workbench_proposals.py),
  [`test_domain_chat.py`](../../../ki-knowledge/tests/test_domain_chat.py).

Diese Quellen belegen den vorhandenen Ansatz; eine vollständige
Funktions-/Lastabnahme ist Teil der späteren Portierung.
