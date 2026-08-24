# T-29 · Provider-Alias — Eigentümer, Lebenszyklus, Wechsel

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | offen | 1 Tag | Eigentum an `symbol`, Wechselregeln, Backup-Pflicht, Importbericht | — |

**Löst:** Die Spalte `symbol` trägt heute zwei Bedeutungen, ohne sich zu
entscheiden. Der Plugin-Entwurf nennt sie einen *stabilen, App-eigenen
Anzeigewert* (`2026-08-19-plugin-system-design.md:323-329, 379-411`), das
Vertragsartefakt schwächer *„Anzeigename beim Kursanbieter"*
(`contract/core-contract.json:13-16, 49, 55`). Tatsächlich ist sie beides
zugleich: `app/services/quote_service.py:255` ruft
`fetch_quote(resolved.symbol)` — der Wert ist **abrufrelevant** und damit an
den Provider gebunden, steht aber in einer providerlosen Spalte.

Solange Yahoo die einzige eingebaute Quelle ist, fällt das nicht auf. Mit einer
zweiten Quelle fällt es sofort auf: Ein einzelnes `symbol` kann nicht
gleichzeitig `EUNL.DE` für Yahoo und `EUNL.XETRA` für EODHD sein.

**Herkunft:** Codex-Review zu T-21 Teil 3, Runde 9, Finding 1 (HOCH). Aus T-21
herausgeschnitten, weil es die Bedeutung einer Vertragsspalte ändert, in T-25
eingreift und die Plugin-Spec berührt — Entscheidung Mike, 2026-08-24.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)
· Entwurf für dieses Ticket steht aus.

**Hängt an:** T-21 (liefert die kanonische Identität `(ticker, mic)`, von der
der Alias getrennt bleiben muss), T-22 und T-25 (Profilbegriff und Rotation).
**Revidiert T-25**, siehe unten.

---

## Was Mike entschieden hat (2026-08-24)

Im Wortlaut aus `STATUS.md`:

> Vor einem solchen Einschnitt darf StockInfo vom Benutzer ein Backup und eine
> ausdrückliche Bestätigung verlangen. Ein Restore/Import dieses Backups in ein
> anderes Plugin ist Best-Effort: eindeutig und einfach überführbare Daten
> werden übernommen; nicht sicher überführbare Daten dürfen entfallen, müssen
> dem Benutzer aber vorab als Risiko und danach konkret als nicht
> wiederhergestellt gemeldet werden. Alte Provider-Aliase werden nie still
> weiterverwendet.

Daraus folgt:

* **Aliase gehören dem Provider** oder der Quellenprofil-Generation, eindeutig.
  Die kanonische Identität `(ticker, mic)` bleibt davon getrennt und
  providerunabhängig.
* **Beim Wechsel werden alle Aliase des alten Providers entfernt** und, soweit
  eindeutig und einfach, durch Aliase des neuen ersetzt.
* **Nicht sicher überführbare Fälle bleiben ohne Alias** und erzeugen eine
  sichtbare, verständliche Meldung. Es wird nicht geraten.
* **Kein massiver Migrationsumbau** nur zum Erhalt alter Aliase.

## Was dieses Ticket an T-25 ändert

`T-25-quellenprofil-wechseln.md:94-110` sagt heute: *„Eine Sicherung aus Profil
A in Profil B einzuspielen ist ein Fehler, kein Sonderfall."* Mikes Entscheidung
hebt das auf: Es ist ausdrücklich erlaubt und **Best-Effort**, mit Vorab-Warnung
und nachträglichem Bericht.

T-21, T-25 und die Plugin-Spec müssen am Ende **denselben** Vertrag nennen. Das
ist Teil der Abnahme dieses Tickets, nicht eine Nebenwirkung.

## Die offene Entwurfsentscheidung

Zwei zulässige Wege stehen zur Wahl, und der Entwurf muss festlegen, **welcher
Wechsel welchen Weg nimmt**:

1. **Profilrotation mit frischer Datenbank** — bereits in T-25 beschlossen.
2. **Providerbezogene Alias-Speicherung** in derselben Datenbank, mit atomarem
   Löschen und Neuaufbau.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Datenmodell | ein Alias ist eindeutig einem Provider bzw. einer Generation zugeordnet; `(ticker, mic)` bleibt providerunabhängig | | |
| 2 | Wechsel A → B | **kein** Alias von A überlebt beim neuen Provider — auch dann nicht, wenn Restore oder Neuberechnung einzelner Listings scheitert | | |
| 3 | nicht überführbarer Fall | bleibt ohne Alias, wird nicht geraten, erscheint im Bericht | | |
| 4 | vor dem Wechsel | Backup wird verlangt und ausdrücklich bestätigt; das Risiko unvollständiger Wiederherstellung steht vorher da | | |
| 5 | nach dem Wechsel | Importbericht listet die nicht wiederhergestellten Fälle **konkret** und nennt das weitere Vorgehen | | |
| 6 | Symbol-Endpunkte, Links, Cache | kein alter Alias lebt über sie weiter | | |
| 7 | T-21, T-25, Plugin-Spec | nennen denselben Vertrag; die alte T-25-Aussage ist ersetzt, nicht nur ergänzt | | |
| 8 | `make test` | Backend, Plugin-API und Dashboard grün | | |
