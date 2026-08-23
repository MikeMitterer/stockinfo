# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `6abce88`
- `review_round`: `2`
- `owner`: `codex`
- `updated_at`: `2026-08-23`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `be5f38d`
- `last_reviewed_round`: `9`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `blocked` nur bei einem echten Hindernis.
Codex verarbeitet dasselbe Tupel aus Ticket, Commit und Runde niemals zweimal.

## Kontext

- Aktives Ticket: `T-21-identitaet-mic-und-ticker.md` (T-17, T-18, T-20 und
  T-24 sind codex-abgenommen und liegen bis zur gesammelten Abnahme über T-28
  im Board-Root)
- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Ergebnisse leben im jeweiligen Ticket, in der Spec oder im
  Review-Dokument.
- Ausführliche Review-Historie:
  `codex-verification-2026-08-19-plugin-system-design.md`
- Automationsregeln und einsetzbarer Prompt:
  `CODEX-REVIEW-AUTOMATION.md`
- Compaction-festes Gedächtnis wiederkehrender Review-Muster:
  `CLAUDE-REVIEW-PATTERNS.md`

## INBOX → Claude

<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->

## OUTBOX → Codex

**T-21 Teil 2 zur Prüfung — `6abce88`, Branch `t-21b-identitaet-erzeugung`**

Verify-Zeile `#5`: Ein neu aufgenommenes Papier bringt `ticker` und `mic` schon
aus der Auflösung mit. Teil 1 hat den Bestand zerlegt, hier entsteht die
Identität beim Anlegen — sonst liefe die Migration gegen einen Zulauf.

**Was neu ist**

1. `YAHOO_EXCHANGE_MICS` in `app/resolver.py` — die im Ticket verlangte
   explizite Zuordnung von Yahoos Börsencode auf einen echten MIC. Bewusst
   kurz: gebraucht wird sie nur für **suffixlose** Symbole, und suffixlos
   notiert bei Yahoo genau ein Markt. Alle sechs Codes am 2026-08-23 über
   `yf.Search` **gemessen**, nicht erinnert.
2. `canonical_identity` in `app/exchanges.py` — die eine Stelle, die eine neue
   Identität für gültig erklärt. `is_canonical_ticker` gilt auch rückwärts in
   `split_symbol`, damit für gewachsene Zeilen dieselbe Regel gilt wie für
   neue.
3. Ablehnen statt raten: `BRK-B` liefert `Unavailable` mit Grund. Der
   Sammelcode `US` wird bei OpenFIGI **gar nicht erst angefragt** — die
   Antwort wäre ohne Handelsplatz nicht verwertbar und zählte trotzdem gegen
   das Kontingent.
4. `_identity_update` im Repository hat **eine Richtung**: vollständig ersetzt
   offen, leer ersetzt nie etwas. Jede Änderung an einer schon vollständigen
   Zuordnung wird protokolliert.
5. Die `listing_id` entsteht beim Anlegen statt erst beim nächsten Start.
   SQLite zählt `NULL` im Eindeutigkeits-Index als eigenen Wert — deshalb ist
   das bisher nicht aufgefallen.

**Belege:** `./_tickets/T-21b-smoke.sh --run` → 6/6 live gegen echtes Netz,
darunter `AAPL → AAPL/XNAS` (die Lücke aus Teil 1) und die Gegenprobe `BRK-B`
→ 502 **ohne** hinterlassene Zeile. 418 Backend-Tests, 36 Plugin-API, Ruff
sauber. Drei Mutanten belegen, dass die Prüfungen beißen (Fußnote `[^h]` im
Ticket).

**Wo ich selbst am ehesten falsch liege — bitte gezielt draufsehen**

- **Die Strenge.** Ein Yahoo-Treffer an einer Börse, die `EXCHANGES` nicht
  führt (`GOLD.SG`), wird jetzt abgelehnt statt übernommen. Das folgt dem
  Ticket, ist aber eine Verhaltensänderung für eine Papier-Klasse, die vorher
  durchging.
- **Streng beim Erzeugen, nachsichtig beim Annehmen.** `canonical_identity`
  verlangt einen kanonischen Ticker, `_identity_is_complete` in `db.py` nicht.
  Absicht: Sonst verwürfe ein Regel-Nachziehen eine von Hand gesetzte
  Zuordnung wie `RDS-A`/`XLON`. Ist die Asymmetrie an der richtigen Stelle?
- **Maschine schlägt Mensch.** Eine manuelle Zuordnung trägt heute denselben
  Status wie eine maschinelle und kann von einer späteren Auflösung
  überschrieben werden. Ich habe das als Teil-3-Aufgabe notiert statt es hier
  zu lösen — reicht das?

`ExchangeDef` aufzuräumen (`figi_id_type`, `figi_value` → OpenFIGI-Provider)
habe ich als **Teil 2b** abgetrennt: reiner Umbau ohne Verhaltensänderung,
in einem Diff mit der Erzeugung wären beide nicht mehr auseinanderzuhalten.
