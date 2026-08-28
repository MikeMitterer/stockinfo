# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-23-plugin-registry.md`
- `handoff_commit`: `4e23cde`
- `review_round`: `3`
- `owner`: `codex`
- `updated_at`: `2026-08-28`
- `last_reviewed_ticket`: `T-23-plugin-registry.md`
- `last_reviewed_commit`: `e35d190`
- `last_reviewed_round`: `2`
- `workstream`: `plugin_mvp`
- `priority_chain`: `T-22-quellen-konfiguration.md > T-27a-contract-kit.md > T-27b-http-fake-real.md > T-23-plugin-registry.md`
- `priority_ticket`: `T-23-plugin-registry.md`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `portfolio_review` übergibt nach dem
letzten Kettenglied an Mike, `blocked` nur bei einem echten Hindernis.

## Kontext

> **Portfolio-Rebaseline Mike, 2026-08-27:** T-21 ist nach der freigegebenen
> Übergabe 3 eingefroren. Verbindliche Kette: **T-22 → T-27a → T-27b →
> T-23**. Ziel ist ein nachgewiesener Lauf eines Datei- und eines
> Entry-Point-Plugins über **Registry → Core → REST**.

> **Freigegebener T-21-Sockel:** Produktstand `2dd0dc3`, Review-Freigabe
> `d3fecb8`, Statusstand `ce55202`. Die späteren 4A-Stände `7a14d79` und
> `48fff52` bleiben eingefroren.

> **T-28:** Nach T-23 werden T-19, T-21 4A/4B, T-25, T-26 und T-29 bis T-34
> einzeln als Gate oder Follow-up klassifiziert. Sie blockieren den ersten
> Plugin-MVP nicht automatisch.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

_Keine offene Nachricht._


## OUTBOX → Codex

### T-23 · Runde 3 · sechs Befunde, zwei davon Laufzeitfehler von mir

Stand `4e23cde`. **Die ersten beiden habe ich in Runde 2 selbst eingebaut**, und
beide waren im Betrieb sichtbar, nicht theoretisch.

#### 1 · `daily` und `fx` bekamen das nackte Plugin

Ich hatte `contract` an der **Quelle** gesetzt, die Adaptertabelle hatte aber
nur zwei Einträge. Nachgestellt vor der Korrektur:

```
daily      yfinance  -> YFinancePlugin  hat fetch_daily_closes? False
fx         yfinance  -> YFinancePlugin  hat fetch_fx_rate?     False
```

Ein `AttributeError` beim ersten Abruf — und **kein einziger Test hat es
gesehen**, weil keiner diese Rollen durch den Container geführt hat. Jetzt gibt
es fünf Adapter und einen parametrisierten Test über alle fünf Rollen, der
nicht fragt *was* gebaut wurde, sondern ob das Gebaute die Methode **hat**, die
der Core ruft.

Dabei ist noch ein Fehler aufgefallen, den dein Rollentest gefangen hat:
`contract` gehört an die **Rolle**, nicht an die Quelle. yfinance spricht den
Vertrag für `quotes`/`daily`/`fx`, für `etf_meta` aber noch die
Core-Schnittstelle — ein Ja/Nein an der Quelle hätte der ETF-Kette ein Objekt
ohne `fetch` gegeben.

#### 2 · `handles()` machte den Schutzschalter wirkungslos

`CompositeResolver` ruft vor jedem `resolve` erst `handles`. Solange auch diese
Auskunft als Erfolg zählte, setzte sie den Zähler **vor jedem** Fehlschlag
zurück:

```
nach 5 Fehlschlägen mit handles davor:  failures = 1  | offen? False
nach der Korrektur, 3 Fehlschläge:      failures = 3  | offen? True
```

Eine dauerhaft ausgefallene Quelle, die brav ihre Zuständigkeit meldet,
erreichte die Schwelle nie — der Schalter war an genau der Stelle wirkungslos,
für die er gebaut wurde. `NON_RECORDING` nennt die Auskunftsmethoden jetzt
ausdrücklich.

#### 3 · Leseweg und Bauweg sagten Verschiedenes

`/sources` meldete eine Quelle als `usable`, die am Bau-Rand längst verworfen
war. Beide teilen sich jetzt **eine** Auswertung (`_evaluate`). Das war schon
vorher die Zusage im Docstring; sie stimmte nur nicht mehr, seit die
Konstruktion geprüft wird — dasselbe Muster wie der Befund aus T-22 Runde 1,
eine Ebene später.

#### 4 · Das Fondsvolumen war um den Wechselkurs falsch

`JustEtfProvider` liest `overview["fund_size_eur"]`. Ich habe den Betrag mit
`fund_currency` beschriftet — bei `IE00B4L5Y983` ist das **USD**. Der Wert
stimmte, seine Bedeutung nicht; zweiter Befund derselben Sorte in diesem
Ticket nach `adjusted`. Der Test nimmt bewusst einen Fonds, dessen Fondswährung
nicht EUR ist — mit einem EUR-Fonds wäre er grün gewesen, ohne etwas zu prüfen.

#### 5 · Der Installationsweg — **hier brauche ich Mikes Entscheidung**

Ich habe ihn **nicht** gebaut, und ich möchte begründen, warum das kein
Ausweichen ist:

Der Entry-Point-Weg funktioniert für **jedes** Paket in der Umgebung der App.
`pip install mein-plugin` genügt; den Rest macht `importlib.metadata`. Ein
fremdes Paket nimmt exakt denselben Weg wie das mitgelieferte Beispiel — daran
ist nichts besonders, und das mitgelieferte beweist den Mechanismus, nicht die
Herkunft.

Was der Launcher **zusätzlich** brächte: dass die Paketliste in `sources.yaml`
steht statt in einem `pip`-Aufruf, und dass die Installation ein Image-Update
überlebt, weil sie unter `/data` liegt. Das ist Bequemlichkeit und
Betriebsfrage — und es ist dieselbe Bauart (hash-benannte Umgebung,
Aktivierungszeiger), die gerade mit `#6c` gestrichen wurde. Sie ohne Auftrag
wieder aufzubauen wäre `P-09` zum dritten Mal.

Also: Was fehlte, war **Dokumentation**, nicht Code. `docs/plugins.md`
beschreibt jetzt beide Wege, die Auswahl über `sources.yaml` und das Verhalten
bei jedem Defekt. Verify `#2b` steht im Ticket als **offen** und wartet auf
Mike — eigenes Ticket oder in T-23 nachziehen.

#### 6 · Testfundament

`EUR→EUR` und der justETF-US-Abbruch berühren kein Netz und stehen jetzt in der
Unit-Suite — beide mit einem Anbieter, dessen Benutzung ein Fehler wäre; ohne
ihn bewiese der Test nur das Ergebnis, nicht den ausbleibenden Zugriff. Alle
**acht** Integrationsfälle fassen jetzt wirklich einen Dienst an. Der Test
liest `api_key` über die öffentliche Sicht statt `._client._api_key`.

Dazu die `QuoteProvider`-Signatur in allen Implementierern und Doubles; die
yfinance-Anbindung sagt in ihrem Docstring, dass sie das Core-Protokoll seit
T-23 **nicht** mehr erfüllt.

#### Verifikation

* `make test`: Backend **779 / 29 skipped** (vorher 772), Plugin-API
  **257 / 1 skipped**, Dashboard **259**.
* `pytest -m "not integration"`: **771 passed, 8 deselected**.
* `pytest -m integration`: **8 passed** — und alle acht fassen einen Dienst an.
* `ruff check app tests plugin_api` und `git diff --check` sauber.
