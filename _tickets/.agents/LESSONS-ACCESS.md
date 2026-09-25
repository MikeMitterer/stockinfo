# Lessons lesen und pflegen

Lokale Originalerfahrungen stehen einzeln in [lessons/](lessons/).
`CLAUDE-LESSONS.md` und `CODEX-LESSONS.md` sind eingefrorene Linkeinstiege für
bisherige Verweise. Sie enthalten keine zweite bearbeitete Wissensfassung.
**Vor jedem Einstieg die Dateien unter `lessons/` inventarisieren:** Neue
Einträge müssen nicht in den alten Linklisten stehen. Autorenschaft steht im
YAML-Kopf unter `subject_author`, nicht in der aktuellen Rollenzuordnung.

1. Der Coder liest vor Umsetzung und Übergabe die zu seiner Autorenschaft
   gehörenden Lessons und die für den Auftrag einschlägigen gemeinsamen Regeln.
2. Der Verifier liest vor dem Review die Lessons des Autors der Prüffassung;
   bei gemischter Arbeit beide. Vorbeugung und Gegenprobe an der Fassung prüfen.
3. Der Observer berücksichtigt alle lokalen Lessons und den gemeinsamen Stand.
   Er ergänzt passende lokale Einzeldateien; neue IDs sind projektweit eindeutig.
   Globale Änderungen verlangen weiterhin einen entsprechenden Auftrag.

Die alten Einstiege allein erfüllen die Lesepflicht nicht. Im Ticket genügen
Kennung, benutzte Fassung und der zugehörige Prüfbeleg. Unklare Herkunft bleibt
`unknown`; die aktuelle Rolle belegt weder Autorenschaft noch Entdecker.

## Übersicht

- [Gemeinsame Regeln](#gemeinsame-regeln)
- [Einzeldateien](#einzeldateien)
- [Lokale Einordnung · StockInfo](#lokale-einordnung--stockinfo)

## Gemeinsame Regeln

Die Anwendung und ihre Anleitung liegen im eigenständigen Projekt
[AgentLessons](../../../../../DevKI/Production/AgentLessons/README.md).
Der gemeinsame Wissensbestand liegt unter
`${XDG_DATA_HOME:-$HOME/.local/share}/agent-lessons/`.
`INDEX.md` erschließt die Regeln unter `shared/` und die archivierten
Projekt-Lessons unter `collected/`. Die lokalen Originale bleiben in StockInfo;
der Collector liest sie und erhält frühere Fassungen im zentralen Archiv.

```bash
agent-lessons --info                  # Datenorte und Quellenstatus nur lesen
agent-lessons --resolve SI-CX-01 -p stockinfo  # Archivierte Lesson finden
agent-lessons --collect               # Registrierte Quellen ins Archiv sammeln
```

`--collect` aktualisiert den gemeinsamen Bestand und die Laufberichte.
Den Aufruf nur im beauftragten Umfang ausführen; eine reine Statusprüfung
verwendet `--info`. Ein periodischer Lauf und KI-Ableitung sind noch nicht
umgesetzt. `needs_review` kennzeichnet die ausstehende fachliche Prüfung einer
Regel; ein erfolgreicher Sammellauf ersetzt diese Prüfung nicht.

Bei gesetztem absolutem `XDG_DATA_HOME` diesen Ort verwenden; bei leerem Wert
gilt der Standardort unter Home. Relative Werte weist die CLI ab. Dasselbe gilt für
`XDG_CONFIG_HOME`, `XDG_STATE_HOME` und `XDG_CACHE_HOME` mit `.config`,
`.local/state` und `.cache`. Grundlage ist die
[XDG Base Directory Specification](https://specifications.freedesktop.org/basedir/latest/).
Keinen relativen Verzeichnisaufstieg vom Projektvolume zum Home fest einbauen.

Projektbasis und Quellenregistrierung stehen gemeinsam in
`${XDG_CONFIG_HOME:-$HOME/.config}/agent-lessons/config.yaml` unter
`project_root` und `projects`. Die Projektpfade unter `projects` sind relativ
zu `project_root`, der Lessons-Pfad relativ zum jeweiligen Projekt. Im
Wissensbestand liegt keine zweite Registrierungsdatei. Bei fehlender
Konfiguration nicht aus einer Restdatei im Bestand ergänzen oder Werte erraten;
die fehlende Konfiguration sichtbar nennen. `agent-lessons --info` zeigt die
verwendete Konfiguration und die aufgelösten Quellenpfade. StockInfo ist mit
`_tickets/.agents/lessons` als Quelle registriert.

Die Sammlung ist ein eigenständiges Git-Repository ohne Remote. Ihre Quellen
sind relativ zu der benannten Projektbasis registriert. Zum Lesen gemeinsamer
Regeln sind die Quell-Repositories nicht erforderlich: kompakte Belege und der
Archivstand liegen in der Sammlung. Dortige Projektbelege nennen ergänzend die
ursprüngliche Herkunft; sie sind keine lokal auflösbaren Sammlungslinks.

Fehlt der gemeinsame Bestand, die Lücke im Ticket nennen und die lokalen
Lessons weiter verwenden. Keinen erfolgreichen Abgleich behaupten. Daraus
entsteht kein pauschaler Arbeitsstopp; ein ausdrücklich erforderlicher und
fehlender Nachweis bleibt jedoch offen. Änderungen während eines Reviews für
den nächsten zuständigen Schritt vormerken, die Prüffassung stabil halten.

Neue Projekte wählen passende Regeln nach Architektur, Betrieb und Testgrenzen.
Übernahme, Anpassung oder Auslassung mit Regel-ID, Fassung und Grund lokal
festhalten, ohne Quellbelege als eigene Vorfälle zu zählen. Der Collector
überschreibt keine lokalen Originale.

[↑ Übersicht](#übersicht)

## Einzeldateien

Eine Lesson ist eine Markdown-Datei mit YAML-Kopf, `schema_version: 1`,
projektweit eindeutiger `id` und `project`. Getrennt erfassen: `kind`,
`discovery_phase`, `affected_work`, `subject_author`, `discovered_by`,
`recorded_by`, `prevention_roles` und `provenance`. Der Text enthält Erkennung,
Implementer-Regel, Verifier-Prüfung und Originalbelege. Eine ausdrückliche
menschliche Vorgabe bleibt eine Vorgabe; ein Vorschlag wird nicht allein wegen
seines Absenders zur geprüften Regel. Der Workflow bestimmt die Aufnahme.

Eine Datei heißt `<ID>-<titel-in-kleinschreibung>.md`. Die ID bleibt exakt
erhalten; der Titelteil verwendet nur `a-z`, `0-9` und einfache Bindestriche.
Leerzeichen und Satzzeichen werden Bindestriche; `ä/ö/ü/ß` werden `ae/oe/ue/ss`.
Der erste Markdown-Titel nach dem YAML-Kopf lautet `# <ID> · <Titel>` und
liefert denselben Titel. Beispiel:
`SP-CX-02-entscheidungen-in-allen-aktuellen-aussagen-nachziehen.md` mit
`# SP-CX-02 · Entscheidungen in allen aktuellen Aussagen nachziehen`.

Umlaute können als zusammengesetztes Zeichen (NFC) oder als Grundbuchstabe
mit kombinierendem Zeichen (NFD) vorliegen. Die Behandlung hängt von
Dateisystem und Werkzeug ab; nicht jedes macOS-Dateisystem speichert pauschal
NFD. Git beschreibt dafür auf macOS `core.precomposeUnicode`; APFS erhält die
angelieferte Normalisierung. ASCII-Dateinamen vermeiden diese Unterschiede.
[Git-Konfiguration](https://git-scm.com/docs/git-config#Documentation/git-config.txt-coreprecomposeUnicode),
[Apple-Dateisystembeschreibung](https://developer.apple.com/library/archive/documentation/FileManagement/Conceptual/APFS_Guide/FAQ/FAQ.html).

Die ID ist der Referenzschlüssel. Lokale Lessons über die YAML-Köpfe
inventarisieren; Kommentare und Belegtext sind keine Kennungsquelle.
Archivierte Fassungen mit `agent-lessons --resolve ID --project stockinfo`
auflösen; `--sha256 ORIGINAL_SHA256` grenzt auf eine bestimmte Fassung ein.
`sources[].id` und `sources[].sha256` bestimmen die Archivfassung einer Regel.
Der Collector erzeugt daraus `sources[].path` relativ zur Regeldatei.
Ein alter Pfad entscheidet nicht über die gefundene Lesson. Fehlende oder
mehrdeutige Kennungen und abweichende Fassungen sichtbar melden.

Bei Titeländerung ID beibehalten, Datei und Überschrift zusammen ändern und
lokale Markdown-Verweise nachziehen. Beim nächsten beauftragten Sammellauf
aktualisiert der Collector den zentralen Index und bekannte Regelverweise.
Beliebige alte Markdown-URLs repariert er nicht automatisch.

Die vollständige Formatbeschreibung liegt im Skill `task-verification-workflow`
unter `references/lesson-format.md`. Formatänderungen in den Lesekanälen aller
Autoren ankündigen; unbekannte Fassungen nicht still als Fassung 1 behandeln.
Verfahrensregeln gehören in den Workflow, nicht als Lessons in dieses Verzeichnis.

[↑ Übersicht](#übersicht)

## Lokale Einordnung · StockInfo

`SI-…` bezeichnet die Originalerfahrungen dieses Projekts. Gemeinsame Regeln
sind zusätzliche Ableitungen, keine neuen lokalen Episoden. Die Test- und
Betriebsvorgaben von StockInfo gelten weiter; StockPortfolios Beschränkungen
für injizierte Antworten werden nicht hierher übernommen. Die bisherigen
Verfahrensabschnitte stehen in [LESSONS-PROCESS.md](LESSONS-PROCESS.md).

[↑ Übersicht](#übersicht)
