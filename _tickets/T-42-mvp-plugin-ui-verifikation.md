# T-42 · MVP plugin UI verification

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (laufender Stack) | offen | Konzept 2 h, Lauf 3 h | risikobasierte Browser-Abnahme der fertigen Plugin-Kette; danach dieselbe kurze Matrix für Mike | — |

- **Angelegt:** 2026-08-31, nach technischer Freigabe von T-39
- **Hängt ab von:** T-31, T-38, T-37, T-41, T-35 und T-39 freigegeben
- **Reihenfolge:** nächstes aktives Ticket; T-40 ruht bis zu Mikes
  ausdrücklichem Kommando

**Löst:** Die Plugin-Implementierung ist technisch geprüft, aber Mike braucht
eine kurze, belastbare Abnahme aus Benutzersicht. Claude entwirft zuerst die
Browser-Matrix aus den tatsächlich umgesetzten Tickets; Codex prüft das
Konzept. Erst danach läuft Claude die freigegebenen Fälle im Browser, behebt
kleine eindeutig lokale Fehler und übergibt dieselbe Matrix an Mike.

---

## Scope-Vertrag

### Phase A · Konzept, noch kein Browserlauf

- Die freigegebenen Plugin-Tickets werden als Inventar gelesen; alte
  Zwischenstände und T-28 erzeugen keine Anforderungen.
- Höchstens **12 sichtbare Fälle** decken die Risikogrenzen ab, nicht jede
  frühere Verify-Zeile einzeln.
- Jeder Fall nennt Profil, Eingabe, sichtbares Ergebnis, erwartete Quelle und
  den einen Fehler, den er unterscheiden soll.
- Das Konzept geht vollständig an Codex. Vor dessen `approved` gibt es weder
  Browserlauf noch Produktänderung.

### Phase B · Claude-Browserlauf

- Zwei reale Profile: reines Ein-Datei-YAML und Online/YFinance mit demselben
  YAML-Plugin als letztem Fallback.
- Sichtbare Kernfälle: normale Aktie/ETF, `BTC-EUR`, Anleihe mit manueller
  History, `fund`, mindestens eine Online-/YAML-Überlappung sowie FX.
- Geprüft werden Aufnahme, Liste, Drilldown, Preis/Herkunft, Historie,
  Metadaten, `/sources`-Diagnose, Neustart/Persistenz und relevante
  Fehlermeldungen — aber nur dort, wo der Fall die Plugin-Kette wirklich
  unterscheidet.
- Claude dokumentiert Konsole und fehlgeschlagene Requests. Ein grüner
  Screenshot ohne Datenherkunft ist kein Beleg.

### Fehlerbehandlung und Grenze

- Ein kleiner, eindeutiger lokaler Fehler darf im Ticket korrigiert und erneut
  geprüft werden. Sobald Vertrag, Schema, neue UI-Fläche, Abhängigkeit oder
  mehr als drei Produktdateien nötig werden, stoppt Claude vor dem Edit am
  Scope-Checkpoint.
- Keine neue Browser-Testinfrastruktur, kein Record/Replay, keine dauerhafte
  E2E-Suite und keine Wiederholung aller Backend-/Contract-Tests als eigene
  Fälle.
- Human-Spalte bleibt bis zu Mikes Lauf leer. Claude schreibt dort niemals.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ bestätigt mit Einschränkung · ◑ teilweise ·
➖ keine Live-Verifikation · `AI` nur KI · `Human` nur Mensch.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Konzept-Handoff an Codex | höchstens 12 Fälle; jeder unterscheidet einen benannten Plugin-Fehler und nennt Profil, Eingabe, Ergebnis und Quelle | ➖ | |
| **2** | YAML-Profil im Browser | BTC, Anleihe/History und Fonds lassen sich aufnehmen und bleiben nach Neustart mit korrekter Gattung und Herkunft sichtbar | ➖ | |
| **3** | Online-Profil im Browser | Online gewinnt bei Überlappung; YAML schließt eine echte Lücke; Aktie/ETF, BTC, Bond und `fund` sind vertreten | ➖ | |
| **4** | Rollen im UI/Netzwerk | Resolver, Quote, Daily, Metadaten und FX werden mindestens einmal über einen echten Eintrittspfad unterschieden | ➖ | |
| **5** | Diagnose und Fehler | `/sources`, sichtbare Fehlermeldungen, Konsole und fehlgeschlagene Requests widersprechen dem angezeigten Zustand nicht | ➖ | |
| **6** | Regression | betroffene Tests, beide Profil-Smokes, Ruff, Build und vollständiges `make test` sind nach dem finalen Browserstand grün | ➖ | |
| **7** | Mike-Handoff | dieselben kurzen Schritte sind ohne Entwicklungswissen nachvollziehbar; Human-Spalte ist leer und bereit zur Abnahme | ➖ | |

---

## Nicht-Ziele

- Keine neue Asset-Klasse `cash`, keine Immobilien.
- Keine neuen Provider oder Plugin-Rollen.
- Keine Universalisierung des Agenten-Regelwerks; das bleibt T-40.
- Kein Anspruch, jede Kombination abzudecken. Die Matrix beantwortet, ob die
  gebaute Plugin-Kette im MVP aus Benutzersicht stimmt.

## Auflösung

_(offen — zuerst Claudes Konzept, dann Codex-Freigabe, dann Browserlauf und
Mikes unveränderte Human-Spalte)_
