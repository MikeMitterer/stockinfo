# T-29 · Provider-Alias — Eigentümer, Lebenszyklus, Wechsel

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | **verworfen 2026-09-07** | 1 Tag | Eigentum an `symbol`, Wechselregeln, Backup-Pflicht, Importbericht | — |

> **Verworfen am 2026-09-07, Entscheidung Mike.** Der Anlass dieses Tickets ist
> durch andere Arbeit behoben, der eine verbliebene Rest ist nach
> [T-30](../T-30-plugin-boersenauskunft.md) übernommen, und den letzten
> eigenständigen Teil — den portablen JSON-Export/Import — hat Mike
> ausdrücklich gestrichen: *„JSON-Export, Import ist zu aufwendig — wird nicht
> weiter verfolgt."*
>
> Die Begründung im Einzelnen steht unter
> [Einordnung 2026-09-07](#einordnung-2026-09-07). Der ursprüngliche Text
> darunter bleibt unverändert als Nachweis der damaligen Lage stehen; er ist
> **kein Arbeitsauftrag mehr**.

<a id="einordnung-2026-09-07"></a>

## Einordnung 2026-09-07 · geprüft von Claude

Auftrag von Mike: „Überprüfe T-29, ist das Ticket überhaupt noch relevant und
wie wichtig ist es aus deiner Sicht?"

### Der Anlass ist behoben — durch T-21, T-23 und T-31

Das Ticket trägt einen einzigen begründenden Satz: `symbol` sei zugleich
App-eigener Anzeigewert **und** anbietergebundener Abrufschlüssel, weshalb ein
Wert nicht gleichzeitig `EUNL.DE` für Yahoo und `EUNL.XETRA` für EODHD sein
könne. Dieser Satz stimmt nicht mehr.

Seit `API_VERSION 2` trägt die Kursanfrage nur noch die Identität:

```python
class QuoteRequest:
    identity: Identity        # kein symbol
```

Jede Quelle bildet ihr Anbietersymbol daraus selbst
(`app/plugins/yfinance_quotes.py:142`). Der gespeicherte Wert entsteht
umgekehrt aus derselben Identität über `provider_alias(ticker, mic)` — eine
Richtung, eine Stelle. Der `QuoteAdapter` führt in seinem Docstring genau die
Begründung dieses Tickets und hält fest, dass der Core seit T-23 die Identität
hereinreicht.

**Damit gibt es keinen anbietereigenen Alias-Bestand.** Der Begriff existiert im
Code nicht als Datenhaltung. Die Zeilen `#1`, `#2`, `#3`, `#5` und `#6` verlieren
ihre Voraussetzung: Es ist nichts zu besitzen, zu entfernen oder zu berichten.

### Der eine Rest ist nach T-30 gewandert

`symbol` wird bei der Anlage einmal berechnet und danach nie wieder
geschrieben — er steht nicht in `_META_FIELDS`. Die Ableitungsvorschrift steht
aber in `EXCHANGES[mic].alias`, also in der Tabelle, die T-30 für Plugins
öffnet. Ändert sich dort ein bestehender Alias, tragen alte und neue Zeilen
verschiedene Konventionen. Die Regel dazu steht jetzt in T-30 samt Verify-Zeile
`#6c`; sie ist ein Absatz, kein Ticket.

### Der JSON-Export/Import ist gestrichen

Teil **(a)** der Backup-Tabelle unten existiert nicht: Es gibt nur `/backups`
und `/backups/{name}/restore`, also ausschließlich den SQLite-Snapshot **(b)**.
Der portable Weg hat mit Aliasen nichts zu tun und steckte nur deshalb hier,
weil Mikes Entscheidung vom 2026-08-24 Backup und Bestätigung im selben Atemzug
nannte. Am 2026-09-07 hat Mike ihn als zu aufwendig gestrichen.

Der Snapshot **(b)** ist dagegen gebaut und belegt: `VACUUM INTO` statt `cp`,
`test_eine_sicherung_entsteht_waehrend_geschrieben_wird` für den Schreibfall,
Manifest, Aufbewahrung von zehn Ständen, Ablehnung fremder Sicherungen. Das ist
in T-25 entstanden, nicht hier.

### Die Verweise dieses Tickets zeigen ins Leere

* `quote_service.py:255` rufe `fetch_quote(resolved.symbol)` — der Aufruf ist
  heute `fetch_quote(resolved)` in Zeile 679.
* „Revidiert T-25" mitsamt der Zitatstelle `T-25:94-110` zeigt in einen
  Abschnitt, der seit dem 2026-09-07 im Archivteil des neu geschriebenen T-25
  liegt.
* „Hängt an T-25 (Profilbegriff und **Rotation**)" — die Rotation ist im neuen
  T-25 ausdrücklich fallengelassen.
* `#7` verlangt, dass T-21, T-25 und die Plugin-Spec denselben Vertrag nennen.
  T-25 beantwortet die Frage „was passiert mit Daten, wenn das Plugin wechselt"
  inzwischen anders und neuer: plugin-deklarierte `data_version` mit
  plugin-gelieferter Migration statt Best-Effort-Import. Die Aufgabe lebt dort
  weiter, nicht hier.

### Verify · Stand bei der Verwerfung

`—` bedeutet **gegenstandslos**: Die Voraussetzung der Zeile ist entfallen.
`✗` bedeutet **verworfen** durch Mikes Entscheidung.
`➖` steht wie gehabt für automatisierte Belege ohne Live-Verifikation.

| # | Where | Stand |
|---|---|:--:|
| 1 | Alias einem Provider zugeordnet; `(ticker, mic)` providerunabhängig | — |
| 2 | kein Alias von A überlebt beim neuen Provider | — |
| 3 | nicht überführbarer Fall bleibt ohne Alias | — |
| 4 | Backup vor dem Wechsel verlangt und bestätigt | — |
| 4a | **(a) JSON** — Export im UI | ✗ |
| 4b | **(a) JSON** — Import, anderes Plugin | ✗ |
| 4c | **(b) Snapshot** — Erzeugung über SQLite-Backup-API | ➖ |
| 4d | **(b) Snapshot** — bitgenaues Rollback | ➖ |
| 4e | UI trennt (a) und (b) unverwechselbar | — |
| 5 | Importbericht der nicht wiederhergestellten Fälle | ✗ |
| 6 | kein alter Alias lebt über Endpunkte, Links oder Cache weiter | — |
| 7 | T-21, T-25 und Plugin-Spec nennen denselben Vertrag | → T-25 |
| 8 | `make test` grün | ➖ |

Zu `#8`, gemessen am 2026-09-07: `1069 passed, 29 skipped, 8 deselected` auf
frischem Datenpfad, Dashboard `331 passed`.

---

## Ursprünglicher Text · Nachweis der Lage vom 2026-08-24

Alles Folgende bleibt unverändert erhalten. Es beschreibt einen behobenen
Zustand und stellt keine Anforderung mehr.

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

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../../docs/superpowers/specs/2026-08-19-plugin-system-design.md)
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

## Zwei Backup-Arten, die nichts miteinander zu tun haben

*(Mike, 2026-08-24, nach Runde 9 — im Entwurf und in der Oberfläche strikt zu
trennen. Sie zu verwechseln hieße, einen Best-Effort-Import für ein bitgenaues
Rollback zu halten.)*

| | **(a) Portables JSON** | **(b) SQLite-Snapshot** |
|---|---|---|
| Zweck | Umzug, auch **über Plugins hinweg** | **exakter Rollback** derselben Instanz |
| Wo | im UI exportieren **und** importieren | Datei mit Datum-/Zeit-Suffix |
| Semantik | **Best-Effort** | bitgenau, alles oder nichts |
| Vorher | Vorschau und ausdrückliche Bestätigung, Hinweis auf mögliche Auslassungen | — |
| Nachher | konkreter Importbericht der nicht übernommenen Fälle | — |
| Aliase | alte werden **nicht** importiert; neue nur, wo eindeutig | unverändert, es ist dieselbe Datenbank |

**Der Snapshot ist trotz des simplen Ergebnisses nicht simpel herzustellen.**
Ein rohes `cp` einer aktiven WAL-Datenbank genügt **nicht** — committete
Einträge fehlten dann. Er entsteht über die SQLite-Backup-API oder eine Sperre,
die **alle** Schreiber umfasst, Scheduler und Requests. Dieselbe Lehre steckt
schon in `T-21-smoke.sh` (Codex, Runde 2) und in T-25.

**Wenn das den Ein-Tages-Rahmen sprengt**, werden (a) und (b) getrennt
geschnitten. Der Entwurf entscheidet das, nicht die Umsetzung.

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
| 4 | vor dem Wechsel | Backup wird verlangt und ausdrücklich bestätigt; das Risiko unvollständiger Wiederherstellung steht **vorher** da | | |
| 4a | **(a) JSON** — Export im UI | versioniert, portabel, enthält **keine** Provider-Aliase | | |
| 4b | **(a) JSON** — Import im UI, anderes Plugin | Vorschau und Bestätigung; Best-Effort; neue Aliase nur, wo eindeutig | | |
| 4c | **(b) Snapshot** — Erzeugung | vollständige Kopie mit Datum-/Zeit-Suffix, über SQLite-Backup-API oder Sperre über **alle** Schreiber; ein rohes `cp` fällt durch | | |
| 4d | **(b) Snapshot** — Rollback | stellt denselben Stand bitgenau wieder her, ohne Best-Effort-Semantik | | |
| 4e | UI | (a) und (b) sind in Benennung, Zweck und Restore-Semantik **nicht** verwechselbar | | |
| 5 | nach dem Wechsel | Importbericht listet die nicht wiederhergestellten Fälle **konkret** und nennt das weitere Vorgehen | | |
| 6 | Symbol-Endpunkte, Links, Cache | kein alter Alias lebt über sie weiter | | |
| 7 | T-21, T-25, Plugin-Spec | nennen denselben Vertrag; die alte T-25-Aussage ist ersetzt, nicht nur ergänzt | | |
| 8 | `make test` | Backend, Plugin-API und Dashboard grün | | |
