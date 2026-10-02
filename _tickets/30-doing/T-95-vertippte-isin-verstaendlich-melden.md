# T-95 · Eine vertippte ISIN wird als Symbol ohne Börsenzusatz gemeldet

**Warum dieses Ticket:** Die Browser-Gesamtprüfung aus T-93 (Weg W2,
Codex-Befund B5 in Runde 2) zeigt: Wer im Feld „ISIN or symbol“ eine ISIN
vertippt, liest „The symbol has no exchange suffix“. Die Meldung redet von
einem Symbol und einem Börsenzusatz. Sie sagt nicht, dass die ISIN falsch
ist. Wer sie liest, sucht den Fehler an der falschen Stelle.

**Beispiel:** `DE000110253X` (letztes Zeichen ein Buchstabe statt der
Prüfziffer). `POST /instruments/intake` antwortet mit
`symbol_without_exchange_suffix`; die Oberfläche zeigt den Satz oben.

**Stand:** Funktional in Runde 1 belegt; Doku-Nacharbeit angefordert.
Angelegt am 2026-10-02 aus T-93 als Folgeticket der visuellen
Tests (Mike: Folgetickets aus den Tests gehören zur SQL-Umstellung und
kommen in die `priority_chain`). Älter als die SQL-Umstellung. Aktiviert
wie T-94: von `t-93-visuelle-gesamtpruefung` abgezweigt, nach der Freigabe
zurück nach T-93. Für Mike steht kein Handgriff an.

## Ursache (gemessen)

- `IntakeService._store` (`app/services/intake_service.py`) wählt den Weg
  über `is_isin` (`app/exchanges.py`). Das prüft nur die **Form**
  `[A-Z]{2}[A-Z0-9]{9}[0-9]`.
- `DE000110253X` hat diese Form nicht (letztes Zeichen keine Ziffer) und
  geht deshalb den Symbolweg. Dort fehlt ein Börsenzusatz, also
  `symbol_without_exchange_suffix`.
- Die passende Kennung gibt es schon: `invalid_isin_format`
  (`app/routers/validation.py`), samt Text in beiden Sprachkatalogen
  („{isin} is not shaped like an ISIN.“). Der Aufnahmeweg nutzt sie für
  freie Eingaben nicht.

## Umfang

- Eine Eingabe, die **wie eine ISIN aussieht, aber keine gültige ist**,
  wird mit `invalid_isin_format` abgelehnt statt über den Symbolweg.
- „Sieht aus wie eine ISIN“ muss eng genug sein, dass echte Symbole ohne
  Börsenzusatz weiter ihre bisherige Meldung bekommen. Die genaue Regel
  legt der Umfangsvertrag fest und begründet sie.
- Eine formal richtige ISIN mit falscher Prüfziffer: prüfen, was heute
  passiert, und im Ticket festhalten. Mitbeheben nur, wenn es dieselbe
  Stelle ist.

### Akzeptanzkriterien

- [x] `POST /instruments/intake` mit `DE000110253X` liefert
      `invalid_isin_format` mit `params.isin`.
- [x] Ein echtes Symbol ohne Zusatz (etwa `AAPL`) bekommt weiter
      `symbol_without_exchange_suffix` bzw. sein bisheriges Ergebnis.
- [x] Ein Test am Aufnahmeweg ist ohne die Korrektur rot.
- [x] W2 der Browserprüfung erwartet für `DE000110253X` den ISIN-Text
      und ist grün.

### Umfangsvertrag (Claude, 2026-10-02)

- **Regel „sieht aus wie eine ISIN“** (`is_malformed_isin` in
  `app/exchanges.py`): zwei Buchstaben, dann zehn Buchstaben oder Ziffern,
  davon mindestens eine Ziffer, aber nicht die ISIN-Form. Ein Börsensymbol
  dieser Länge ohne Punkt gibt es praktisch nicht; die verlangte Ziffer
  schließt reine Buchstabenfolgen aus.
- **Aufnahme** (`IntakeService._store`): nach dem ISIN-Weg, vor dem
  Symbolweg, `IntakeRejected(invalid_isin_format, isin=…)`. Damit bleibt es
  bei `400` mit `{code, params}` wie jede Ablehnung der Aufnahme; das
  Dashboard übersetzt die Kennung schon (DE und EN).
- **Kennung an einer Stelle:** `REASON_INVALID_ISIN` zieht von
  `app/routers/validation.py` nach `app/exchanges.py`, weil auch der Dienst
  sie meldet; `validation.py` übernimmt sie von dort.
- **Falsche Prüfziffer bei richtiger Form** (gemessen, Offline-Profil):
  `DE0001102532` → `400 instrument_not_found` („None of the configured
  sources found a security …“). Verständlich und eine andere Stelle (die
  Auflösung durch die Quellen); nicht mitbehoben.

## Review-Verlauf (neueste Runde zuerst)

### Verifier-Prüfung · Runde 1 (Codex, 2026-10-02)

**Ergebnis: `changes_requested` für die Vertragsaussage.** Geprüft wurde
`f200fa3` gegen `b39ff26`. Rollen, Owner, Priorität und Branch stimmten;
Paket-VERSION `df699dd1d7583c59030030ad44e3ab896d4660be8d84575662e652f754624da1`
war unverändert. Der App-Fix selbst hat keinen offenen Funktionsbefund.

- Die echte Aufnahme-Kette in `tests/test_identity_intake_paths.py` ist mit
  31/31 gezielten Fällen grün. Eine nur im Testprozess eingesetzte
  Fehlvariante (`is_malformed_isin` immer `False`) macht alle drei neuen
  Fehlformfälle rot: Der alte `symbol_without_exchange_suffix`-Code und
  `params.identifier` erscheinen statt `invalid_isin_format` und
  `params.isin`. Produktcode blieb dabei unverändert.
- Das Browser-Orakel W2 erwartet jetzt den ISIN-Text und schließt
  „exchange suffix“ aus. Claudes sichtbarer W2-Lauf meldete 2/2; den
  Screenshot `W2-malformed.png` aus seinem Lauf habe ich gelesen. Ein
  weiterer eigener Browserstart erfolgte nicht, da Mikes Hauptmonitor-
  Vorgabe erst für T-93 Runde 3 in den Startweg eingebaut wird.
- `make check` unabhängig grün: 1305 netzfreie Backend-Tests, 399
  Dashboard-Tests, 324 Plugin-API-Tests, 50 Beispieltests, ESLint, Ruff
  und `vue-tsc`. `git diff --check` sauber. Python-AST-Inventar aller
  vier geänderten Python-Dateien und TS-Compiler-API-Inventar des
  JavaScript-Skripts: Bezeichner englisch; deutsche Testnamen sind erlaubt.

**B1 · Die Doku verspricht mehr als die Umsetzung.**
`docs/rest-core-contract.md` sagt, eine ISIN-ähnliche Eingabe, die „keine
gültige ist“, erhalte `invalid_isin_format`. Dasselbe steht im
Ticketumfang. Eine formal richtig aufgebaute ISIN mit falscher Prüfziffer
ist ebenfalls ungültig, wird aber bewusst **nicht** hier erkannt:
`is_isin('DE0001102532') == True`,
`is_malformed_isin('DE0001102532') == False`, und die Übergabe nennt
`instrument_not_found`. Der neue Vertrag führt Konsumenten dadurch in
die Irre. Bitte in der aktuellen Vertragsdoku und im Ticketumfang exakt
„ISIN-ähnliche Eingabe mit ungültiger **Form**“ schreiben; den Fall einer
falschen Prüfziffer und seine heutige Antwort knapp abgrenzen. Kein
zusätzlicher Produktumbau ist für diesen Befund verlangt.

| Standards aus `/Users/macminipro/.codex/skills/code-standards/SKILL.md` | Ergebnis |
|---|---|
| Architektur | ✅ Erkennung im Fachmodul, Ablehnung im Dienst, HTTP-Abbildung am bestehenden Router. |
| Shell | ➖ Nicht berührt. |
| CLI | ➖ Kein neuer CLI-Aufruf. |
| Frontend | ✅ i18n-Kennung schon in Deutsch und Englisch vorhanden; W2 verwendet den bestehenden Katalog. |
| Python | ✅ Typen, Namen und Fehlerweg am Eintrittspunkt geprüft. |
| Persistenz | ➖ Kein DB-Code berührt; der Test nutzt die temporäre Testdatenbank. |
| Qualität | ✅ Positiver Aufnahmeweg, Symbol-Nachbarn und negative Fehlvariante. |
| Dokumentation | ⚠️ B1: Gültigkeit und Format werden im aktuellen Vertrag verwechselt. |

Gelesene Referenzen: `references/architecture.md`, `python.md`,
`persistence.md`, `quality.md`, `documentation.md` und `frontend.md`.
**DRY-Abgleich:** ISIN-Form, neue Heuristik, Kennung und Texte im Projekt
gesucht. `REASON_INVALID_ISIN` hat jetzt eine Quelle in `app/exchanges.py`;
die Heuristik für *Ähnlichkeit* ist eine andere Regel als das bestehende
ISIN-Format. Keine doppelte Fachlogik im Diff. **Doku-Abgleich:** Der
betroffene Abschnitt in `docs/rest-core-contract.md` ist B1.
`README.md`, `docker/README.md` und `unraid/README.md` führen keine
Aufnahme-Fehlerkennungen; keine Änderung dort nötig. Die getrennte
Board-Übernahme der Paketfassung `df699dd1` bleibt offen.

### Übergabe Runde 1 (Claude, 2026-10-02)

Prüffassung `f200fa3` gegen `1c69db2` (Stand T-93 nach Runde-2-Befund).

- **Tests am Aufnahmeweg** (`tests/test_identity_intake_paths.py`):
  `test_eine_vertippte_isin_wird_als_isin_abgelehnt` (drei Fälle, darunter
  `DE000110253X`) prüft Status, Kennung und `params.isin` und dass keine
  Zeile entsteht. Gegenprobe: mit altem `app/` (per `git stash`) alle drei
  rot. Nachbarn in `test_was_keiner_isin_aehnelt_bleibt_beim_symbolweg`
  (zu kurz, nur Buchstaben, zu lang) bleiben beim Symbolweg, vorher wie
  nachher grün.
- **Messung mit dem Offline-Profil** (eigene Temp-Datenbank):
  `DE000110253X` → `invalid_isin_format`; `IE00B4L5Y983` → `201`;
  `AAPL` → `symbol_without_exchange_suffix`; `DE0001102532` →
  `instrument_not_found`.
- **Browser:** W2 erwartet „DE000110253X is not shaped like an ISIN.“ und
  schließt „exchange suffix“ aus; `ONLY=W1,W2` 2/2 grün, Screenshot
  `W2-malformed.png` angesehen.
- **`make check`:** Exit 0 (1305 Backend, 399 Dashboard, Ruff, `vue-tsc`).
- **Doku-Abgleich:** `docs/rest-core-contract.md` (Aufnahmeweg) nennt die
  Ablehnung. `README.md`, `docker/README.md`, `unraid/README.md`
  unverändert: Sie listen keine Fehlerkennungen der Aufnahme. StockPortfolio
  nutzt den Aufnahmeweg nicht.

### Side-Effects

Nur der Aufnahmeweg für freie Eingaben. Die ISIN-Pfade
(`/quote/{isin}` usw.) prüfen schon heute über `InvalidIsinError`.
