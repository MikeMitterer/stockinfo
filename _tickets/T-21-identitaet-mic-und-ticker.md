# T-21 · Identität auf MIC + Ticker umstellen

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | Teil 1 abgenommen | 1 Tag | Schema-Migration, Symbolerzeugung | — |

**Löst:** Der Identifikator eines Papiers ist heute das **Yahoo-Symbol**
(`EUNL.DE`) — in der Datenbank, in der API, im Dashboard. Damit ist yfinance
nicht ersetzbar, sondern nur ergänzbar. Jede zweite Kursquelle müsste Yahoos
Suffix-Schreibweise nachbilden.

**Der Brocken der Serie.** Alles andere ist klein dagegen.

> **Stand nach Codex-Runde 4.** Zwei frühere Fassungen sind überholt: `symbol`
> wird **nicht** `NULL`-fähig (es bleibt am REST-Rand zugesagt), verliert aber
> seinen **globalen Eindeutigkeits-Index** — der gehört auf `(ticker, mic)`.

**Hängt an: T-24** — erst muss feststehen, was die API zusagt und wie eindeutig
adressiert wird. **Blockiert:** T-23 (ein Plugin, das Yahoo-Symbole erwarten
muss, ist kein Plugin).

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

> **Drei Übergaben statt einer** *(Claude, 2026-08-22)* — ein Tag Arbeit ist für
> einen Diff-Review zu viel am Stück. Die Schnitte liegen dort, wo das Ticket
> selbst schon trennt:
>
> | | Umfang | Zeilen | Commit |
> |---|---|---|---|
> | **Teil 1** | Schema, Migration, Meldung offener Fälle, Index-Umzug | `#1`, `#2`, `#3b` | `be5f38d` ✔ abgenommen |
> | **Teil 2** | Erzeugung neuer Papiere, Yahoo-Normalisierung | `#5` | `6abce88` ✔ abgenommen |
> | **Teil 2b** | `ExchangeDef` aufräumen (`figi_id_type`, `figi_value` zum Provider) | — | `556c23d` ✔ abgenommen |
> | **Teil 3** | in **vier** Übergaben, siehe Entwurf: 1 Börsenkatalog · 2 Migration **samt ihrer Meldung** · 3 Aufnahmeweg samt `core_version 2.0.0` · 4 Börsenabweichung, Fehlerpfad, Inventur | `#2b`, `#2d`, `#2e`, `#3`, `#4` | offen |
> | ~~Handzuordnung~~ | ~~offene Zuordnungen von Hand setzbar, eigener Status~~ | ~~`#2c`~~ | **gestrichen**, siehe Kasten |
>
> **Teil 2b abgetrennt** *(Claude, 2026-08-23)* — das Aufräumen von
> `ExchangeDef` ist ein reiner Umbau ohne Verhaltensänderung und hat mit der
> Erzeugung nichts zu tun. In einer Übergabe mit ihr vermischt, stünde ein
> Diff zur Prüfung, in dem sich Verhalten und Verschiebung nicht trennen
> lassen — bei einem Ticket, das in Teil 1 neun Runden gebraucht hat, ist das
> der schlechtere Schnitt.
>
> `#6` (`make test`) läuft in jeder Übergabe mit.

> **Teil 3 ist aufgeteilt** *(Entscheidung Mike, 2026-08-24, nach Codex-Runde 9)*
>
> Der Entwurf war über das Ticket hinausgewachsen. Zwei Themen liegen jetzt als
> eigene Tickets im Board:
>
> * [`T-29`](T-29-alias-lebenszyklus-und-providerwechsel.md) — **Provider-Alias:
>   Eigentümer, Lebenszyklus, Wechsel.** Wer `symbol` besitzt, was beim
>   Providerwechsel damit geschieht, Backup-Pflicht und Best-Effort-Restore.
>   **Revidiert `T-25:94-110`.**
> * [`T-30`](T-30-plugin-boersenauskunft.md) — **plugin-deklarierte
>   Börsenauskunft.** Neuer `plugin_api`-Typ samt Merge-, Vorrang-, Kollisions-,
>   Provenienz- und Invalidierungsregeln.
>
> **Teil 3 stärkt die Zusage zu `symbol` deshalb nicht.** Der Sprung auf
> `core_version 2.0.0` betrifft `ticker`, `mic`, `listing_id` und den strengeren
> Aufnahmeweg — nicht die Bedeutung von `symbol`. Die wird in T-29 geklärt.

> **Die Handzuordnung ist gestrichen — der Symbolweg verlangt die Kombination
> künftig im Vertrag** *(Claude, 2026-08-24; Entscheidungen Mike)*
>
> **Entwurf:** [`docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md`](../docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md)
>
> **⚠️ Codex: die Messungen bitte eigenständig nachvollziehen**, nicht anhand
> dieser Zusammenfassung. Der ganze Zuschnitt hängt an ihnen.
>
> **Erster Anlauf, und warum er falsch war.** Zuerst stand hier, der
> automatische Weg hole die offenen Fälle von selbst ein — gemessen am
> ISIN-Weg, und dort stimmt es: `VTI` → `ARCX`, `AAPL` → `XNAS` über
> `YAHOO_EXCHANGE_MICS`. Diese Messung übersah aber einen **zweiten
> Aufnahmeweg**. Mikes Rückfrage, ob es hier überhaupt um die Migration gehe,
> hat ihn aufgedeckt:
>
> | Quelle | Wann | Heilt sich selbst? |
> |---|---|---|
> | Migration (`app/db.py:277`) | beim Start, offline, Altbestand | ja, sobald eine ISIN-Auflösung läuft |
> | Symbolweg (`app/services/quote_service.py:179`) | laufend, bei jedem suffixlosen Symbol | **nein** |
>
> Eine über `GET /quote?symbol=AAPL` angelegte Zeile bleibt bei jedem weiteren
> Abruf offen. Der Grund steht im Kommentar von `get_quote_for_known` selbst —
> *„der Scheduler löst nichts auf, er holt nur Kurse."* Die Auffrischung zieht
> die Zuordnung aus `split_symbol(symbol)`, und das liefert für `AAPL`
> dauerhaft `(None, None)`.
>
> **Die Lösung ist deshalb nicht Reparatur, sondern Verhinderung.** Der
> Symbolweg verlangt künftig die vollständige Kombination: bekanntes Suffix
> **oder** `mic` als Parameter. Ein suffixloses Symbol ohne `mic` wird mit 400
> abgelehnt, statt stillschweigend eine dauerhaft offene Zeile anzulegen. Damit
> entstehen die Fälle gar nicht erst, die `#2c` hätte aufräumen sollen.
>
> **Das ist eine bewusste Umkehr gegenüber Teil 2**, dessen Kommentar wörtlich
> dagegen argumentiert (*„nähme ihm eine Abfrage weg, die es heute gibt"*). Neu
> ist das Wissen, dass genau diese Abfrage die unzuordenbaren Zeilen erzeugt.
> Der Parameter ist zudem seit jeher als *„Vollständiges Yahoo-Symbol inkl.
> Suffix"* dokumentiert — suffixlose Symbole waren nie zugesagt.
>
> **`core_version` steigt auf `2.0.0`** (Entscheidung Mike): Eine Anfrage, die
> heute 200 liefert, liefert künftig 400.
>
> ~~**Der Migrationspfad wird nicht eng gesehen** (Entscheidung Mike): Was sich
> einfach migrieren lässt, wird migriert; der Rest bleibt offen und bekommt
> eine verständliche Meldung.~~ **Überholt nach Runde 16** — der Rest bleibt
> *nicht* offen, er kommt gar nicht erst in den Bestand. Es gilt der Kasten
> „Der Zwischenzustand — aufgehoben" weiter unten. `GOLD.SG` löst weiterhin ein
> Eintrag `XSTU`/`.SG` in `EXCHANGES`, und **der muss vor der Migration da
> sein** — sonst kostet die Ablehnung 257 Tageskurse.
>
> **Was damit ebenfalls entfällt:** die Entwurfsfrage aus Runde 3 nach einem
> eigenen Status für von Hand gesetzte Zuordnungen. Den braucht es nur, *weil*
> es manuelle Zuordnungen gibt. ~~`identity_status` bleibt zweiwertig.~~
> **`identity_status` entfällt ersatzlos** — die Spalte hätte nur noch einen
> Wert.
>
> **Was dazukommt:** Sichtbar zu machen sind ~~zwei Zustände — offene
> Zuordnungen *und*~~ **seit Runde 16 zwei verschiedene Dinge:** der
> **Migrationsbericht** über Zeilen, die *nicht* in den Bestand gekommen sind,
> und im laufenden Betrieb „von der Vorzugsbörse abgewichen" mit beiden MICs
> und Währungen (erwartet `XETR`/EUR, tatsächlich `ARCX`/USD). Heute ist
> Letzteres nur die Logzeile `resolve_foreign_exchange`; im Dashboard sieht
> niemand, dass ein Papier in USD hereinkommt, obwohl XETR eingestellt ist.
> Eine **offene Zuordnung als Instrumentzustand** gibt es nicht mehr.
> 3. Eine **falsche** automatische Zuordnung überschreiben. Der einzige Fall,
>    in dem wirklich ein Mensch entscheiden muss — und es ist Korrektur, nicht
>    Erstzuordnung. Taucht er auf, ist er ein eigenes Ticket.

> **Verify `#2` verlangt für `AAPL` mehr, als die Migration wissen kann**
> *(Claude, 2026-08-22)*
>
> Die Zeile erwartet `AAPL` → `AAPL`/**`XNAS`** direkt nach der Migration. Das
> Ticket sagt zwei Absätze weiter aber selbst: Für suffixlose Symbole liefert
> die Börsentabelle nur den Sammelcode `US`, und „welcher echte MIC gilt,
> **steht dort nicht** — das muss aus dem aufgelösten Listing kommen".
>
> Beides zusammen geht nicht. Die Migration läuft beim Start und offline; sie
> müsste OpenFIGI fragen, um `XNYS` von `XNAS` zu unterscheiden — ein Start,
> der Netz braucht und in ein Rate-Limit laufen kann, und das für jede
> bestehende Zeile.
>
> ~~**Umgesetzt ist deshalb:** Die Zeile bekommt
> `identity_status = legacy_unresolved` und erscheint in der Liste offener
> Zuordnungen; den echten MIC trägt der nächste erfolgreiche Auflösungslauf
> nach.~~
>
> **Seit Runde 16 gilt stattdessen:** Ein suffixloses Symbol wird weiterhin
> **nicht geraten** — aber die Zeile bleibt auch nicht offen liegen. Sie wird
> **abgelehnt** und erscheint im Migrationsbericht mit Grund und verlorenen
> Kurspunkten; der Weg zurück ist die Neuerfassung über den Aufnahmeweg. Der
> Kern des Kastens stimmt unverändert: Die Migration läuft offline und **kann**
> den echten MIC nicht wissen. Nur die Folge daraus ist eine andere.
>
> Verify `#2` prüft entsprechend `EUNL.DE` → `EUNL`/`XETR` und `XIC.TO` →
> `XIC`/`XTSE` **nach der Migration**, `AAPL` dagegen als **abgelehnten** Fall.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | bestehende Datenbank, Migration laufen lassen | zerlegbare Instrumente haben `ticker` und `mic`; **nicht** zerlegbare werden abgelehnt und gemeldet, nicht geraten | ➖ [^a] | |
| 1b | dieselbe Migration auf einer **Kopie des echten Bestands** | ~~keine Zeile und kein Kurspunkt geht verloren~~ **neu:** kein Kurspunkt einer *migrierten* Zeile geht verloren, auch beim zweiten Start nicht; abgelehnte Zeilen verschwinden **absichtlich** und stehen mit ihrer Kurspunktzahl im Bericht | ➖ [^g] | |
| 2 | Stichprobe nach der Migration | `EUNL.DE` → `EUNL`/`XETR`, `XIC.TO` → `XIC`/`XTSE`; `AAPL` wird **abgelehnt** statt geraten | ➖ [^b] | |
| 2b | Instrument mit Fremdsymbol (`BRK-B`) | erscheint im **Migrationsbericht** mit Grund und verlorenen Kurspunkten — nicht mehr als offene Zeile im Bestand | ➖ [^c] | |
| 2b4 | Bericht und Ablehnung | entstehen in **derselben Transaktion**; ein zweiter Start dupliziert sie nicht; der Eintrag bleibt abrufbar, **nachdem** die aktive Zeile weg ist | | |
| 2b5 | Auslieferung von Teil 2 | **zweiphasig:** Phase 1 erkennt die ausstehende Migration und rechnet vor, ohne etwas zu ändern; erst die Bestätigung löst sie aus. Gleichzeitigkeit im Commit genügt **nicht** — `init_db()` läuft im Lifespan, bevor das UI erreichbar ist | | |
| 2b6 | Phase 1, serverseitig verriegelt — **Routentabellen-Test** | jeder Pfad der Allowlist (statische UI, `/health`, Healthcheck-Endpunkt, `/ready`, Vorschau, Bestätigung, Bericht) antwortet; je ein normaler **Lese-** und **Schreibpfad** (`/quote`, `/refresh`, `PUT`, `DELETE`) wird mit stabiler Kennung abgewiesen; DB und Vorschau bleiben unverändert | | |
| 2b6b | `/ready` in Phase 1 | antwortet **`503`** mit `status: "migration_pending"`, unterscheidbar vom `503` bei unerreichbarer DB; `status` ist ein `Literal`, kein freier `str` | | |
| 2b6e | `GET /operational` (neu) | `200`/`migration_pending` in Phase 1, `200`/`serving` im Normalbetrieb, `503`/`degraded` bei unerreichbarer DB. Der Docker-`HEALTHCHECK` zieht hierher um | | |
| 2b6f | eine Routenquelle | Guard und Routentabellen-Test lesen **dieselbe** Allowlist-Konstante; ein Test vergleicht die `HEALTHCHECK`-URL im `Dockerfile` gegen genau diesen Pfad — sonst driften sie unbemerkt bis zum Deployment | | |
| 2b6g | Diagnose-Verbraucher | `README.md:31-32` und `:202-205`, `docker/Dockerfile:71-75`, `app/main.py:70-76` und `tests/test_api.py:204-240` sind auf die **drei** Fragen abgeglichen; die widerlegte Restart-/Traffic-Begründung steht nirgends mehr | | |
| 2b6c | Image-Test | Pending-Zustand überdauert `start-period` + 3 × `interval`; Healthcheck-Endpunkt bleibt `200`, `/ready` bleibt `503`, Vorschau und Bestätigung durchgehend erreichbar. **Keine** Restart-/Routing-Zusage — die gälte nur für eine konkrete Orchestrator-Konfiguration | | |
| 2b6d | Bestätigung | gegen parallele und doppelte Aufrufe verriegelt; Scheduler und normale Endpunkte werden **genau einmal** freigegeben | | |
| 2b7 | Vorschau, Bericht und Meldungen | **stabile Reason-Codes** statt freier Texte, DE/EN übersetzt — in Teil 2, nicht erst in Teil 4 | | |
| 2b2 | nach erfolgreichem Start | Invariante `COUNT(*) WHERE ticker IS NULL OR mic IS NULL = 0`; kein Instrument-/Quote-Endpunkt serialisiert eine halbe Identität | | |
| 2b3 | Reihenfolge Katalog vor Migration | `GOLD.SG` migriert (257 Tageskurse bleiben), wird **nicht** abgelehnt — der Katalog mit `XSTU` steht vorher | | |
| ~~2c~~ | ~~derselbe Fall, manuelle Zuordnung~~ | **gestrichen** — der Symbolweg verlangt die Kombination künftig im Vertrag, damit entstehen die Fälle nicht mehr. Siehe Kasten „Die Handzuordnung ist gestrichen" | ➖ | |
| 2d | Aufnahmefeld: nackter Ticker `AAPL` | 400, Text nennt beide Auswege mit Beispiel; `AAPL.XNAS` legt die Zeile `resolved` an | | |
| 2d2 | `EUNL.DE` und `EUNL.XETR`, dazu `GOLD.SG` und `GOLD.XSTU` | je Paar **dieselbe** Identität *und* **derselbe** Provider-Alias; geprüft wird auch, womit die Quelle aufgerufen wurde | | |
| 2e | Papier abseits der Vorzugsbörse (`VTI` bei `XETR`) | erscheint als „abgewichen" mit beiden MICs; tatsächliche Währung aus den Kursdaten, nicht aus der Tabelle | | |
| 2e2 | `AAPL`/`XNAS` bei `DEFAULT_EXCHANGE=US` | **keine** Abweichung — der Sammelcode umfasst die US-Plätze | | |
| 2e3 | `VOD`/`XLON` bei `DEFAULT_EXCHANGE=US` | Abweichung mit `kind: collector` und erwarteter Währung `USD`, **ohne** erwarteten MIC | | |
| 2f | Aufnahmeweg über den **echten** Weg Router → Intake-Service → Repository, für ISIN, `TICKER.DE`, `TICKER.XETR` und unbekannte Form | keine eigene Core-Komponente gemockt, nur die Außengrenzen; geprüft wird auch die **Methode** (`POST`) und dass im Router keine Fachregel sitzt | | |
| 2h | Börsenauskunft (`catalog`) | serialisiert **keinen** Sammelcode in ein `mic`-Feld; `US` erscheint als eigener Eintragstyp und bleibt als `DEFAULT_EXCHANGE` samt Mitgliedern nutzbar; **kein** Börseneintrag trägt eine eigene Mitgliedschaftsliste | | |
| 2i | `POST /instruments/intake` | Neuanlage `201` mit `InstrumentSummary`, bestehendes Papier `200` mit demselben Typ, unauflösbar `400`, Quelle tot `502` — je im OpenAPI-Snapshot zugesagt und über die echte Kette geprüft | | |
| 2j | Schichtengrenze am Aufnahmeweg | der Intake-Service liefert `IntakeResult(summary, created)`; im Router steht **kein zweiter Existenz-Check** und keine Repository-Abfrage, er mappt nur `created` auf `201`/`200` | | |
| 2j2 | `created` unter Parallelität | kommt aus der **schreibenden Transaktion**, nicht aus einem Preflight; im abgefangenen UNIQUE-Rennen ist `created=false`, nicht `201` | | |
| ~~2j3~~ | ~~`GET /instruments` mit einer `legacy_unresolved`-Zeile~~ | **entfällt** — mit der Entscheidung nach Runde 16 gibt es diesen Zustand nicht mehr. `ticker`, `mic` und `listing_id` sind Pflicht, siehe `#2b2` | ➖ | |
| 2k | Übergabe 2 als Einheit | `core_version 2.0.0`, Vertragsartefakt und Snapshot kommen **mit** der ersten Änderung am geschlossenen Core, nicht danach — zwischenzeitlich gibt es keinen öffentlich geänderten, aber unzugesagten Endpunkt | | |
| 2g | Fehlerpfad im Dashboard, **je in DE und EN** | bekannte Kennung, unbekannte Kennung, kaputtes JSON, leerer Rumpf, Netzwerkfehler — alle ergeben einen übersetzten Text, nie `statusText` und nie rohes JSON | | |
| 3 | `GET /instruments` | `symbol` weiterhin vorhanden und unverändert (Profil-Links hängen daran) | ✅ [^d] | |
| 3b | Datenbank-Schema | Eindeutigkeit liegt auf `(ticker, mic)`; `symbol` ist **nicht mehr** global unique | ✅ [^e] | |
| 4 | Dashboard, Assets-Tabelle | unverändert; Yahoo- und extraETF-Links funktionieren | | |
| 5 | neues Papier aufnehmen — **auf jedem Weg** | `ticker`/`mic` werden gefüllt, `symbol` daraus erzeugt | ✅ [^h] | |
| 6 | `make test` | Backend, Plugin-API und Dashboard grün | ✅ [^f] | |

> **⚠️ Zu allen Fußnoten unterhalb dieser Zeile** *(2026-08-24, nach Runde 16)*
>
> Sie beschreiben **Belege des alten Zielzustands** und stehen als Historie da,
> nicht als geltende Erwartung. Wo sie offene `NULL`-Zeilen,
> `identity_status = legacy_unresolved` oder „bleibt offen" als richtiges
> Ergebnis führen, ist genau das seit der Entscheidung **falsch**: Solche Zeilen
> kommen nicht mehr in den Bestand.
>
> Deshalb stehen die betroffenen Zeilen `#1`, `#1b`, `#2` und `#2b` in der
> AI-Spalte wieder auf `➖`. Sie werden erst hochgestuft, wenn neue Tests
> Ablehnung, Bericht und die `NULL`-Invariante belegen. Die **Human-Spalte
> bleibt unberührt** — sie gehört Mike.

[^a]: `tests/test_identity_migration.py`, **zwanzig** Tests gegen eine
    nachgestellte Alt-Datenbank mit vier bezeichnenden Fällen. Zerlegt werden `EUNL.DE` und
    `XIC.TO`; `AAPL` (suffixlos) und `BRK-B` (fremde Schreibweise) bleiben
    offen. Die Migration läuft zweimal — sie muss idempotent sein.
[^b]: `test_bekannte_suffixe_werden_zerlegt` und die beiden Gegenproben
    `test_suffixloses_symbol_wird_nicht_geraten` /
    `test_fremde_schreibweise_wird_nicht_geraten`. Dazu
    `tests/test_exchanges.py` mit der Rückrechnung selbst — einschließlich
    `test_kein_suffix_ist_doppelt_vergeben`: Käme eine Börse mit belegtem
    Suffix dazu, wäre `split_symbol` stillschweigend mehrdeutig, und dieser
    Test schlägt an, statt dass die Migration falsch zuordnet.
[^c]: **Nur als Protokollmeldung.** `test_die_offenen_faelle_werden_gemeldet`
    belegt, dass die Migration `identity_unresolved` mit Anzahl und Symbolen
    schreibt. Eine abfragbare *Liste* offener Zuordnungen ist Teil 3 — dort
    steht auch der Grund je Fall.
[^d]: Der Index auf `symbol` ist weg, die Spalte nicht: `symbol TEXT NOT NULL`
    steht unverändert im Schema, und die 370 Tests der Suite fahren die
    bestehenden Symbol-Endpunkte weiter durch.
[^e]: `test_die_eindeutigkeit_liegt_auf_ticker_und_mic` prüft beides:
    `idx_instruments_symbol` ist verschwunden, `idx_instruments_ticker_mic`
    ist eindeutig. Zwei weitere Tests halten die Folgen fest — mehrere offene
    Zeilen dürfen nebeneinander stehen (SQLite zählt `NULL` als eigenen Wert),
    ein echter Konflikt fällt weiterhin auf.
[^f]: `.venv/bin/pytest tests/ -q` → `392 passed, 29 skipped`;
    `make test-plugin-api` → 36; Ruff sauber.
[^h]: `./_tickets/T-21b-smoke.sh --run` — **sechs Checks live gegen das echte
    Netz**, auf frischen temporären Datenbanken, über den HTTP-Weg. Zwei
    Läufe, weil die Kaskade zwei Wege hat: `VGWL.DE → VGWL/XETR` über die
    eigene Börsentabelle (`#5a`) mit der Rückrechnung `VGWL + Suffix(XETR) =
    VGWL.DE` (`#5b`), und `AAPL → AAPL/XNAS` über Yahoos Börsencode (`#5c`).

    **Damit ist die Lücke aus Teil 1 geschlossen**, und zwar dort, wo das
    Ticket sie verortet hat: Der echte MIC kommt aus dem aufgelösten Listing,
    nicht aus der Börsentabelle und nicht geraten.

    Die **Gegenprobe** trägt den Lauf: `BRK-B` wird abgelehnt (`#5d`, HTTP
    502) und hinterlässt **keine** Zeile (`#5e`). Ohne sie prüfte das Script
    nur, dass Erfolgsfälle gelingen. Dazu `#5f`: jede Zeile eine eigene
    `listing_id` — die entsteht jetzt beim Anlegen statt erst beim nächsten
    Start.

    Dazu 15 neue Tests (`tests/test_resolver_identity.py`,
    `tests/test_identity_creation.py`). **Drei Mutanten belegen, dass sie
    beißen**: `canonical_identity` alles durchwinken lassen (2 Tests fallen),
    Yahoos Bindestrich zum Punkt raten (1), eine leere Identität die
    gespeicherte überschreiben lassen (1).

    **Runde 3 hat gezeigt, dass dieses ✅ zu früh kam** (Codex): Geprüft war
    der ISIN-Weg. StockInfo hat aber drei Aufnahmewege, und zwei gingen an der
    Identitätsbildung vorbei — wer ein unbekanntes `VGWL.DE` über
    `GET /quote?symbol=` aufnahm, bekam `ticker=NULL, mic=NULL,
    legacy_unresolved`, obwohl das Symbol eindeutig zerlegbar ist.

    Unsichtbar blieb das, weil meine Tests an beiden Enden ansetzten: Die
    Speicherung bekam die fertige Identität **von Hand** übergeben, der
    Service-Test prüfte nur den ISIN-Pfad. Beide Enden sahen richtig aus, die
    Strecke dazwischen war nie gelaufen.

    `tests/test_identity_intake_paths.py` schließt das: die **echte Kette** —
    Router → Cache-Dienst → Quote-Service → Repository auf echter SQLite —,
    ersetzt sind nur die Außengrenzen, an denen sonst das Netz hinge. Zwei
    Mutanten belegen, dass die Tests beißen.

    Der dritte Weg (`get_quote_for_known`, über den der Scheduler läuft) hatte
    dasselbe Loch und trägt jetzt offene Zeilen **nach**. Damit ist die zweite
    Einschränkung unten erledigt, statt eine Fußnote zu bleiben.

    **Ein Unterschied bleibt, und zwar mit Absicht:** Der Symbol-Weg lehnt ein
    unzerlegbares Symbol **nicht** ab. Auf dem ISIN-Weg wählt StockInfo eine
    Notierung aus mehreren aus — eine halb geratene Identität wäre dort eine
    Entscheidung, die niemand getroffen hat. Auf dem Symbol-Weg nennt der
    Aufrufer das Listing selbst; ihm die Auskunft zu verweigern, weil die
    Börsentabelle für suffixlose Symbole nur einen Sammelcode führt, nähme ihm
    eine Abfrage weg, die es heute gibt. Die Zeile entsteht sichtbar offen.

    **Runde 4** hat am Verhalten nichts mehr geändert, aber am Werkzeug: Die
    leeren Außengrenzen der Tests standen viermal nebeneinander und liegen
    jetzt in `tests/boundaries.py`. `tests/test_boundaries.py` vergleicht sie
    über `inspect.signature` gegen `EtfEnricher` und `DailyCloseProvider` —
    eine Grenze mit `*args, **kwargs` nimmt sonst jeden Aufruf an und verdeckt
    einen gebrochenen Vertrag ausgerechnet in dem Test, der die echte Kette
    prüfen soll.

    Was dabei **offen geblieben** ist und nicht zu `#5` gehört:

    * `XNAS`, `XNYS`, `ARCX`, `XASE`, `BATS` stehen nicht in `EXCHANGES`. Aus
      `(AAPL, XNAS)` lässt sich deshalb **kein** Yahoo-Symbol zusammensetzen —
      die Rückrichtung MIC → Suffix fehlt für die US-Plätze. Heute stört das
      nichts (das Symbol ist gespeichert), aber T-23 braucht sie: Dort setzt
      jede Quelle ihr Format selbst zusammen.
    * ~~Der Nachtrag einer offenen Zeile passiert nur über die ISIN.~~
      **Erledigt in Runde 3:** Auch der Weg für bekannte Papiere trägt nach,
      also auch der Scheduler-Refresh. ~~Offen bleibt nur, was sich aus dem
      Symbol nicht zerlegen lässt (`GOLD.SG`, `VTI`) — dafür ist die manuelle
      Zuordnung aus Teil 3 da.~~ **Nachgemessen 2026-08-24, mit einer wichtigen
      Einschränkung:** Auf dem **ISIN-Weg** trägt der Yahoo-Weg nach (`VTI` →
      `ARCX`). Auf dem **Symbolweg** nicht — `get_quote_for_known` löst nicht
      auf, es holt nur Kurse, und `split_symbol('AAPL')` bleibt für immer
      `(None, None)`. Deshalb verlangt Teil 3 dort die Kombination im Vertrag,
      statt hinterher zu reparieren.
    * ~~Eine **von Hand** gesetzte Zuordnung ist von einer maschinellen nicht
      zu unterscheiden — beide tragen `resolved`. Teil 3 braucht dafür einen
      eigenen Status.~~ **Hinfällig seit 2026-08-24:** Mit der gestrichenen
      Handzuordnung gibt es keine manuelle Zuordnung, die ein Auflösungslauf
      überschreiben könnte. `identity_status` bleibt zweiwertig.
    * **Verhaltensänderung, absichtlich:** Ein Yahoo-Treffer an einer Börse,
      die `EXCHANGES` nicht führt (`GOLD.SG`, Stuttgart), wird jetzt
      abgelehnt statt übernommen. Das ist die Regel des Tickets — wer die
      Börse aufnehmen will, trägt sie in die Tabelle ein, dann greift wieder
      der Suffix-Weg.

[^g]: `./_tickets/T-21-smoke.sh --run` gegen eine **Sicherung** von
    `data/stockinfo.db` (sechs gewachsene Papiere, 48 Kurspunkte) — das
    Original wird nur gelesen. Die Sicherung entsteht über die
    SQLite-Backup-API, nicht per `cp`: Die App läuft im WAL-Modus, und eine
    Dateikopie ließe committete Einträge aus — der Lauf liefe dann an genau
    den neuesten Fällen vorbei (Codex, Runde 2). Neun Checks grün: 6 Instrumente vorher und
    nachher, 48 Kurspunkte vorher und nachher, sechs eindeutige `listing_id`,
    vier zerlegt (`VGWL.DE`, `EUNL.DE`, `APC.DE`, `BRYN.DE` → `XETR`), zwei
    offen (`GOLD.SG` — das Suffix `.SG` steht nicht in der Tabelle — und
    `VTI`, suffixlos), Indizes umgezogen **und eindeutig**. Das Script
    migriert **zweimal**; genau dort hat die Alt-Bereinigung in Runde 1
    Listings gelöscht.

    Die Prüfungen rechnen nach statt zu behaupten, und zwar in der
    **Gegenrichtung**: Was dieser Lauf zugeordnet hat, muss sich aus
    `(ticker, mic)` wieder zu `symbol` zusammensetzen; offene Zeilen tragen
    weder Ticker noch MIC; bereits bestehende Zuordnungen bleiben unverändert
    (`#2c`) und dürfen keinen Sammelcode tragen (`#2d`). Ein Lauf, der nichts
    zugeordnet hat, gilt als **nicht geprüft**.

    `#2d` prüft, dass jede Zeile in **genau einem** gültigen Zustand steht:
    `resolved` verlangt Ticker und echten MIC, `legacy_unresolved` verlangt
    beide Felder leer, ein unbekannter Status ist ein Fehler. Nur auf den
    Sammelcode zu sehen genügte nicht — eine Zeile, die `resolved` behauptet
    und nichts trägt, kam sonst durch (Codex, Runde 5).

    **Die Regel gehört in den Produktcode, nicht nur ins Prüf-Script**
    (Codex, Runde 6): Vollständig ist eine Identität erst mit einem
    **echten** MIC — `is_real_mic` in `app/exchanges.py` ist die eine Stelle,
    die das entscheidet, benutzt von Migration und Prüfung. Der Sammelcode
    `US` überlebt die Migration damit nicht mehr; er wird neu bewertet und
    landet bei den offenen Fällen.

    Entschieden wird dabei nach den **Daten**, nicht nach der Beschriftung:
    Eine vollständige Zuordnung mit kaputtem Status behält ihre Identität, nur
    der Status wird korrigiert und protokolliert. Meine erste Fassung hatte
    sie überschrieben — genau der Verlust, den das Ticket verhindern will.

    **Unbekannt heißt nicht gültig** (Codex, Runde 7): `is_real_mic` ließ
    zunächst jeden der Tabelle unbekannten String durch — auch `NOT-A-MIC`,
    `xnAs` oder `XNAS ` mit Leerzeichen. Geprüft wird jetzt zusätzlich die
    Schreibweise nach ISO 10383: genau vier Zeichen, Großbuchstaben oder
    Ziffern. `XNAS` bleibt erlaubt, weil die Tabelle eine Auswahl der
    auflösbaren Börsen ist und kein Verzeichnis aller MICs. Geprüft wird mit
    `fullmatch`: `$` matcht in Python auch **vor** einem abschließenden
    Zeilenumbruch, und `XNAS\n` wäre durchgegangen — ein Wert, den der
    Eindeutigkeits-Index sogar von `XNAS` unterscheidet (Codex, Runde 8).

    `#2d` im Prüf-Script hat dafür ein **eigenes** Urteil, formuliert über die
    Zeichenmenge statt über ein Muster. Ein Orakel darf die Funktion nicht
    befragen, die es prüft — sonst bestätigt es nur, dass sie mit sich selbst
    übereinstimmt. Gegengeprüft mit absichtlich kaputtem Validator
    (`match` statt `fullmatch`): `#2d` schlägt an, Exit 1. Ein leerer Bestand lässt den Lauf **fehlschlagen** —
    vorher hätte er dort grün gemeldet, ohne einen einzigen Fall geprüft zu
    haben (Codex, Runde 2). Gegenproben: leere Datenbank → Exit 1; ein
    committeter Eintrag im WAL → wird mitgesichert und mitgezählt (7 statt 6).

    **Das Oracle rechnet vorwärts** (Codex, Runde 3): Die Migration zerlegt
    `symbol` → `(ticker, mic)`, die Prüfung setzt `(ticker, mic)` → `symbol`
    zusammen. Mit derselben Funktion zu prüfen hieße, sich selbst recht zu
    geben — und es verwarf einen gültigen Zielzustand: Ein von Hand
    zugeordnetes `VTI` → `VTI/XNAS` behält sein suffixloses `symbol`.
    Nachvalidiert wird deshalb nur, was **dieser Lauf** zugeordnet hat; `#2c`
    hält zusätzlich fest, dass bestehende Zuordnungen unverändert bleiben.
    Gegenprobe mit `WALONLY/XNAS` im WAL: angenommen.

---

## Details

### Warum es geht — die Rückrechnung ist eindeutig

Gemessen am 2026-08-19 über die vollständige Börsentabelle:

```
Börsen gesamt: 33
Suffixe doppelt vergeben: keine — Zuordnung ist eindeutig

EUNL.DE  -> ticker=EUNL  suffix=.DE  mic=XETR
XIC.TO   -> ticker=XIC   suffix=.TO  mic=XTSE
VTI      -> ticker=VTI   suffix=''   → Sammelcode US, **kein** MIC
```

Die letzte Zeile zeigt zugleich die Grenze der Messung: Für suffixlose Symbole
liefert die Tabelle nur den Sammelcode `US`. Welcher echte MIC gilt (`XNYS`
gegen `XNAS`), steht dort nicht — das muss aus dem aufgelösten Listing kommen.

Kein Suffix ist doppelt belegt. **Für Symbole, die aus der eigenen Regel
stammen**, ist die Zerlegung damit eindeutig.

Das gilt aber nicht für alle: Was der Yahoo-Fallback geliefert hat, folgt der
Konvention nicht zwingend (siehe unten). Diese Fälle werden **gemeldet**, nicht
geraten — „jedes Symbol lässt sich zerlegen" wäre eine Behauptung, die der
nächste Bestand widerlegt.

### Was `symbol` heute erzwingt

```
app/db.py:21    symbol TEXT NOT NULL
app/db.py:172   CREATE UNIQUE INDEX idx_instruments_symbol
```

Pflichtfeld **und** global eindeutig. Bleibt das so, braucht auch ein Instrument,
das ausschließlich über EODHD oder Twelve Data verwaltet wird, ein gültiges,
eindeutiges **Yahoo**-Symbol. Yahoo wäre dann weiterhin Teil der Identität — das
Ticket verfehlte sein eigenes Ziel.

**Weg (revidiert nach Codex-Runde 3):** `symbol` **bleibt verpflichtend** — die
erste Fassung wollte es `NULL`-fähig machen.

Der Grund ist **nicht** StockPortfolio: Das gehört demselben Autor, ist nicht
öffentlich und wäre in einem Zug mitzuändern. Der Grund ist, dass StockInfo
selbst verteilt wird — GitHub, Docker Hub, Unraid-Template. Wer die API direkt
nutzt, bekäme den Bruch ab, und man erfährt es nicht.

Was an `symbol` hängt, zeigt der Testkonsument stellvertretend:

```text
src/api/types.ts:17        symbol: string                      // nicht nullable
src/types/portfolio.ts:29  symbol: string                      // Pflicht je Position
src/api/mappers.ts:56      return entry.isin ?? entry.symbol   // Cache-Schlüssel
```

Die dritte Stelle bräche **still**: Der Cache-Schlüssel wäre `undefined`.

Stattdessen **additiv**: `ticker` und `mic` kommen dazu und werden die
kanonische Identität; `symbol` bleibt als stabiler Listing-Bezeichner erhalten
und wird nach derselben Regel erzeugt wie bisher. Das ist kein Anbieter-Alias —
das Format gehört der App (`resolver.py:130` bildet es aus der eigenen
`EXCHANGES`-Tabelle), nicht Yahoo.

**Der Eindeutigkeits-Index zieht mit um — aber nicht ersatzlos.** `symbol`
bleibt Pflichtfeld und verliert den globalen Unique-Index; an seine Stelle tritt
`(ticker, mic)` **und** eine `listing_id` als Schlüssel für Maschinen. Den Index
nur zu entfernen wäre ein stiller Bruch: `get_instrument_by_symbol` nimmt per
`ORDER BY id LIMIT 1` die ältere Zeile, und `DELETE /instruments/by-symbol/…`
träfe dann das falsche Instrument. Die Regeln dafür stehen in **T-24**.

Sind später mehrere Anbieter-Aliase nötig, gehören sie in eine eigene Tabelle
statt als Spalten in die Instrumentenzeile.

### Der eine Pfad, der die Migration bricht

`resolver.py:170` übernimmt im Yahoo-Fallback `top["symbol"]` — den String, den
Yahoos Suche liefert. Der folgt der eigenen Konvention **nicht** zwingend
(`BRK-B` mit Bindestrich). Solche Symbole sind später nicht sicher in `ticker` +
`mic` zu zerlegen.

**Entschieden (Codex, 2026-08-20): normalisieren, wenn eindeutig — sonst
ablehnen und sichtbar machen. Niemals raten.**

Der Yahoo-Adapter kennt Yahoos Eigenheiten, also gehört das Wissen dorthin:

1. Yahoos Börsencode über eine **explizite** Tabelle auf einen echten MIC abbilden
2. den Ticker nur für **bekannte, umkehrbare** Fälle in die kanonische Form bringen
3. das ursprüngliche Yahoo-Symbol als Provider-Alias behalten
4. `Resolved` erst liefern, wenn echter MIC **und** kanonischer Ticker feststehen

`BRK-B` darf **nicht** per Bindestrich-zu-Punkt-Regel zu `BRK.B` geraten werden —
diese Zeichensetzung ist anbieterspezifisch und bedeutet bei anderen Tickern
etwas anderes. Bleibt ein Treffer mehrdeutig: mit Grund in `/sources` und Log
sichtbar machen, nicht als `(ticker, mic)` speichern, `Unavailable` zurückgeben
~~und einen Weg zur Zuordnung von Hand anbieten~~ — **seit Runde 16:** mit
**stabilem Reason-Code** ablehnen. Der Rückweg ist die Neuerfassung über den
Aufnahmeweg (ISIN, `TICKER.DE` oder `TICKER.XETR`), nicht eine Handzuordnung.

„Übernehmen und als nicht zerlegbar markieren" wäre die schlechtere Variante:
Sie macht die gerade eingeführte kanonische Identität wieder optional und
belastet jedes spätere Quote- oder Daily-Plugin erneut mit einem Yahoo-Sonderfall.

### `US` ist kein MIC

`EXCHANGES` führt `US` als Sammelcode für NYSE/NASDAQ (OpenFIGI `exchCode=US`).
Das ist **kein** ISO-10383-MIC. Ein Feld, das mal echte MICs und mal diesen
internen Code enthält, wird beim ersten Anbieter, der echte MICs erwartet, zum
Problem.

**Entschieden (Codex, 2026-08-20):** Das kanonische Feld heißt `mic` und enthält
**ausschließlich echte MICs** (`XNYS`, `XNAS`). Der Sammelcode `US` bleibt als
interner OpenFIGI-Suchcode erhalten, taucht aber nie im kanonischen Feld auf.
Niemals raten, und niemals beide Codearten unter einem Namen führen.

Das betrifft auch T-18: Die Kaskade über die Heimatbörse muss auf echte MICs
abbilden, nicht auf den Sammelcode.

### Was sich sonst ändert

* `instruments` bekommt `ticker` und `mic` (nicht `exchange_mic` — der Name trüge sonst wieder zwei Codearten)
* Migration zerlegt bestehende Symbole über die Suffix-Tabelle
* Wer Kurse holt, setzt sein Format selbst zusammen — Yahoo `{ticker}{suffix}`,
  EODHD `{ticker}.{code}`, Twelve Data `symbol` + `mic_code`
* `ExchangeDef` verliert seine OpenFIGI-Spalten (`figi_id_type`, `figi_value`);
  dieses Wissen zieht zum OpenFIGI-Provider

### Warum das die Anbieterfrage löst

Recherchiert am 2026-08-19: **Kein kommerzieller Dienst verlangt ein eigenes
Identitätssystem.** Alle arbeiten mit Ticker plus Börse, nur die Schreibweise
unterscheidet sich — EODHD hängt `.XETRA` an, Twelve Data nimmt den MIC nach
ISO 10383 als eigenen Parameter. Und MIC ist bereits der Schlüssel der
`EXCHANGES`-Tabelle.

Quellen: [EODHD Exchanges API](https://eodhd.com/financial-apis/exchanges-api-list-of-tickers-and-trading-hours),
[Twelve Data Docs](https://twelvedata.com/docs)

### ~~Der Zwischenzustand~~ — aufgehoben, es gibt keine halbe Identität mehr

> **Entscheidung Mike, 2026-08-24 (nach Runde 16).** Der unten beschriebene
> Zwischenzustand ist **aufgehoben**. Eine nicht auflösbare Altzeile darf
> nirgendwo als `NULL`-Identität weiterleben — nicht im aktiven Bestand, nicht
> im REST-Vertrag, nicht im UI.
>
> **Stattdessen:** Was einfach und eindeutig auflösbar ist, wird migriert. Alles
> andere kommt **nicht** in den gültigen Bestand und wird dem Benutzer mit altem
> Symbol, konkretem Grund, verlorenen Kurspunkten und der Aufforderung zur
> Neuerfassung gemeldet. `ticker` und `mic` sind danach Pflicht; als Invariante
> gilt `COUNT(*) WHERE ticker IS NULL OR mic IS NULL = 0`. Eine Quarantäne darf
> die Rohinformation halten, ist aber kein aktiver Instrumentdatensatz.
>
> **Der dritte Ausweg, den der Text unten für ausgeschlossen hielt** — „Daten
> löschen" — ist damit gewählt, aber unter einer Bedingung, die er nicht kannte:
> Es wird nicht stillschweigend gelöscht, sondern **abgelehnt und benannt**.
> Nachgemessen kostet das im echten Bestand ein einziges Papier (`VTI`, null
> Tageskurse), sofern `XSTU` vorher im Katalog steht. Steht es das nicht, kostet
> es `GOLD.SG` mit **257** Kurspunkten — siehe die Reihenfolgewarnung im
> Entwurf.
>
> `identity_status` entfällt damit ersatzlos: Die Spalte hätte nur noch einen
> Wert.

~~Wären `ticker` und `mic` sofort `NOT NULL`, könnte die Migration eine nicht
zerlegbare Zeile weder stehen lassen noch melden: Sie müsste raten, den Start
blockieren oder Daten löschen.~~

~~**Also braucht es einen ausdrücklichen Zwischenzustand:** die neuen Spalten
sind zunächst `NULL`-fähig, eine Kennzeichnung wie
`identity_status = legacy_unresolved` markiert offene Fälle, der Altdatensatz
bleibt lesbar und nutzbar, und erst nach erfolgreicher Zuordnung wird
`(ticker, mic)` zur Pflicht.~~

~~Ohne diesen Zustand ist „später von Hand zuordnen" ein Versprechen, das die
Migration technisch nicht halten kann.~~ **Der Satz stimmt weiter — und ist
genau deshalb hinfällig:** Weil die Migration „später von Hand" nicht halten
kann, wird seit Runde 16 gar nichts mehr versprochen, was sie nicht halten
kann. Sie lehnt ab und meldet.

### Risiko

Die Migration ist die einzige der Serie, die bestehende Daten anfasst. Vor dem
Lauf eine Kopie der Datenbank, und die Zerlegung vorher als Trockenlauf über die
echten Daten prüfen — ein Symbol, das die Tabelle nicht kennt, muss auffallen
statt still `NULL` zu werden.

**Die Eindeutigkeit der Suffixe gilt für den Bestand, nicht für die Zukunft.**
Gemessen wurde die heutige `EXCHANGES`-Tabelle. Nicht abgedeckt sind neue oder
unbekannte Suffixe, suffixlose Nicht-US-Symbole, von Hand eingetragene Symbole
und Ticker, in denen ein Punkt zum Namen gehört (`BRK.A`). Die Migration muss
solche Fälle **melden** statt zu raten — ~~und danach braucht es einen Weg, sie
von Hand zuzuordnen.~~ **Seit Runde 16:** Sie werden abgelehnt und im Bericht
genannt; der Weg zurück ist die Neuerfassung über den Aufnahmeweg, nicht eine
Handzuordnung.

---

## Auflösung

_(offen)_
