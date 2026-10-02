# T-90 · Persistenz auf SQLModel in `app/persistence/`

**Warum dieses Ticket:** StockInfo greift mit rohem SQLite auf seine
Datenbank zu, verteilt über mehrere Module. Der Hausstandard
(`code-standards/references/persistence.md`) verlangt dagegen eine schlanke
ORM-Schicht (SQLModel) in `app/persistence/`, nach außen ein
Repository-Interface (`typing.Protocol`) per Dependency Injection und kein SQL
außerhalb dieses Ordners. Die Regel gilt bei Berührung; T-89 hat sie
berührt, ein Teilumbau nur dort hätte aber zwei Datenbankzugänge
nebeneinander erzeugt.

**Beispiel:** `QuoteRepository.set_volatility` in `app/repository.py`
schreibt über `detail_store.put_provider` mit rohem SQL. Nach T-90 liegt der
Zugriff in `app/persistence/`, der Dienst kennt nur das Interface.

**Stand:** Angelegt am 2026-10-02. Mike: „Persistenz regelkonform umbauen“
(Codex-Befund B5 in T-89), nach Vorlage des Umfangs: „Eigenes Ticket T-90“.
Folgt nach dem Abschluss von T-89; Rollen und Aktivierung legt `STATUS.md`
fest. Für Mike steht kein Handgriff an.

## Ausgangslage (gemessen am 2026-10-02)

| | Umfang |
|---|---|
| Rohes SQLite in `app/repository.py`, `app/detail_store.py`, `app/db.py` | 1.846 Zeilen, 77 `execute`-Aufrufe |
| Weitere App-Module mit SQL | `app/data_versions.py`, `app/exchanges.py`, `app/migration.py`, `app/persistence/plugin_migration.py`, `app/providers/base.py`, `app/routers/migration.py`, `app/services/backup.py` |
| Nutzer von `QuoteRepository`/`detail_store` | 25 Dateien in `app` und `tests` |
| ORM | keines; SQLModel ist neue Abhängigkeit |

## Was zu klären ist (Scope-Vertrag vor Beginn)

- Schnitt in Teilschritte, die einzeln prüfbar sind (etwa: Ordner und
  Interface, dann Tabellen nacheinander auf SQLModel).
- Umgang mit den bestehenden Migrationen in `app/db.py` und den
  Datenversionen; Backup und Wiederherstellung dürfen nicht brechen.
- Ob rohes SQL für einzelne Abfragen im Repository bleibt (der Standard
  erlaubt das dort).
- Vor der ersten Verwendung ein aktuelles SQLModel-Beispiel aus der
  offiziellen Doku nachschlagen (Pflicht laut Standard).

### Akzeptanzkriterien

- [ ] Außerhalb von `app/persistence/` gibt es kein SQL, keine
      Verbindungs- oder Session-Objekte und keine ORM-Typen.
- [ ] Dienste und Router kennen nur Repository-Interfaces (Protocol) und
      bekommen sie per Dependency Injection.
- [ ] Bestehende Daten, Migrationen, Backup und Wiederherstellung
      funktionieren unverändert; Tests mit temporärer Datenbank belegen das.
- [ ] Die befristete Ausnahme für T-89 in `STATUS.md` entfällt.
- [ ] **Sichtbare Prüfung im Browser** mit Temp-Datenbank: Dashboard,
      Detailbereich, Backup.

### Side-Effects

Betrifft fast alle Backend-Module; keine Änderung an API oder Vertrag
beabsichtigt. StockPortfolio ist nur über die API betroffen.
