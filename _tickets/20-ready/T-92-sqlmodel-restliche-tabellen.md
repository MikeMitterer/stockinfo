# T-92 · SQLModel für die übrigen Tabellen

**Warum dieses Ticket:** Nach T-91 nutzen die Kerntabellen SQLModel. T-92
zieht die übrigen Tabellen nach und schließt damit den Persistenzumbau ab.
Danach endet die befristete Ausnahme aus T-89.

**Beispiel:** Wechselkurse (`fx_rates`) und Metadaten (`meta`) werden heute
noch per SQL gelesen; nach T-92 über SQLModel-Modelle.

**Stand:** Angelegt am 2026-10-02 aus T-90 (Mike: „Drei Tickets
nacheinander“). Folgt nach T-91; Rollen und Aktivierung legt `STATUS.md`
fest. Für Mike steht kein Handgriff an.

## Umfang

- Tabellen: `daily_meta`, `fx_rates`, `meta`, `instrument_overrides`,
  `migration_rejections`.
- Altdaten-Migrationen (`app/persistence/db.py`, `migration.py`), Backup
  (`VACUUM INTO`, `PRAGMA user_version`) und die Plugin-Migration bleiben
  begründet rohes SQL im Persistenzordner; die Begründung steht je Stelle
  im Code.
- Die befristete Ausnahme aus T-89 in `STATUS.md` wird entfernt.

### Akzeptanzkriterien

- [ ] Die genannten Tabellen werden über SQLModel gelesen und geschrieben.
- [ ] Jedes verbleibende rohe SQL steht in `app/persistence/` und ist dort
      begründet.
- [ ] Backup, Wiederherstellung und Migrationsvorschau funktionieren
      unverändert; Tests mit temporärer Datenbank belegen das.
- [ ] Die T-89-Ausnahme in `STATUS.md` ist entfernt.
- [ ] **Sichtbare Prüfung im Browser** mit Temp-Datenbank: Wechselkurse,
      Backup, Einstellungen.

### Side-Effects

Keine Änderung an API oder Vertrag.
