# T-91 · SQLModel für die Kerntabellen

**Warum dieses Ticket:** Der Hausstandard verlangt eine schlanke ORM-Schicht
(SQLModel) für Datenbankzugriffe. Nach T-90 liegt aller Zugriff in
`app/persistence/` hinter einem Protocol, aber noch als rohes SQLite. T-91
stellt die meistgenutzten Tabellen auf SQLModel um.

**Beispiel:** `QuoteRepository.set_volatility` schreibt heute per SQL in
`detail_values`. Nach T-91 nutzt es ein SQLModel-Modell; Aufrufer merken
keinen Unterschied, weil sie nur das Protocol kennen.

**Stand:** Angelegt am 2026-10-02 aus T-90 (Mike: „Drei Tickets
nacheinander“). Folgt nach T-90; Rollen und Aktivierung legt `STATUS.md`
fest. Für Mike steht kein Handgriff an.

## Umfang

- Tabellen: `instruments`, `quotes`, `daily_closes`, `detail_values`,
  `detail_overrides`.
- SQLModel als neue Abhängigkeit; vor der ersten Verwendung ein aktuelles
  Beispiel aus der offiziellen Doku (<https://sqlmodel.tiangolo.com/>)
  nachschlagen (Pflicht laut Standard).
- Bestehendes Schema bleibt; die Modelle bilden es ab, keine
  Schemaänderung. Die Altdaten-Migrationen bleiben in T-91 unberührt.
- Rohes SQL bleibt nur, wo das ORM schlecht passt, und dann im Repository.

### Akzeptanzkriterien

- [ ] Die genannten Tabellen werden über SQLModel gelesen und geschrieben.
- [ ] Bestehende Daten funktionieren ohne Migration; Tests mit temporärer
      Datenbank und einer Datenbank im Altformat belegen das.
- [ ] Außerhalb `app/persistence/` gibt es keine ORM-Typen.
- [ ] **Sichtbare Prüfung im Browser** mit Temp-Datenbank: Dashboard,
      Detailbereich, Aufnahme und Löschen eines Instruments.

### Side-Effects

Neue Abhängigkeit `sqlmodel` (zieht SQLAlchemy nach); Docker-Image wird
größer. Keine Änderung an API oder Vertrag.
