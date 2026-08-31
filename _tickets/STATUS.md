# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-39-english-plugin-developer-guide.md`
- `handoff_commit`: `1110d76`
- `review_round`: `2`
- `owner`: `codex`
- `updated_at`: `2026-08-31`
- `last_reviewed_ticket`: `T-39-english-plugin-developer-guide.md`
- `last_reviewed_commit`: `951f866`
- `last_reviewed_round`: `1`
- `workstream`: `ui_live_acceptance`
- `priority_chain`: `T-36-befunde-aus-dem-ui-lauf.md` → `T-31-papiere-ohne-mic.md` → `T-38-pflichtfelder-im-vertrag.md` → `T-37-yaml-fallback-ein-datei.md` → `T-41-role-kaskaden-fuer-yaml-fallback.md` → `T-35-ui-abnahme-am-laufenden-stack.md` → `T-39-english-plugin-developer-guide.md` → `T-40-universelles-agenten-review-regelwerk.md`
- `priority_ticket`: `T-39-english-plugin-developer-guide.md`

Erlaubte Phasen: `claude_working` → bei Breitenalarm kurz
`scope_checkpoint` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `portfolio_review` übergibt nach dem
letzten Kettenglied an Mike, `blocked` nur bei einem echten Hindernis.

## Kontext

> **Portfolio-Rebaseline Mike, 2026-08-27:** T-21 ist nach der freigegebenen
> Übergabe 3 eingefroren. Verbindliche Kette: **T-22 → T-27a → T-27b →
> T-23**. Ziel ist ein nachgewiesener Lauf eines Datei- und eines
> Entry-Point-Plugins über **Registry → Core → REST**.

> **T-23 Installationsweg, Mike, 2026-08-28 (`87c953c`):** In T-23 schlank
> nachziehen: feste Paketversionen, `data/plugin-env/<hash>`, idempotenter
> Start und `sys.path`; keine Kandidatenumgebung, kein Aktivierungszeiger,
> kein Preflight und keine Offline-/Replay-Infrastruktur.

> **Portfolio-Entscheidung Mike, 2026-08-28:** T-31 (Identitäts-Union für
> Krypto und Anleihen — entschieden, siehe Ticket) und T-38 (Pflichtfelder im
> Vertrag) sind **nach T-36** in die Kette aufgenommen; die
> T-35-Wiederholung rückt ans Kettenende und misst damit den Stand **nach**
> beiden Vertragsänderungen.

> **Portfolio-Bereinigung Mike, 2026-08-29:** Das veraltete Sammel- und
> Abnahmeticket T-28 ist verworfen. Offene Tickets stehen für sich; aus T-28
> entstehen keine Gate- oder Blockerbeziehungen mehr.

> **Menschliche Verifikation Mike, 2026-08-29:** Noch kein Ersatz-Ticket
> anlegen. Zuerst müssen das Online-Plugin und das neue Ein-Datei-YAML-
> Fallback-Plugin sauber laufen und der MVP technisch abgenommen sein. Danach
> entsteht ein frisches, kurzes Verify-Ticket für Mike aus dem dann gültigen
> Produktstand.

> **T-37 Browser-Abnahme Mike, 2026-08-29:** Claude prüft sowohl das reine
> YAML-Profil als auch das normale Online-/YFinance-Profil mit demselben
> YAML-Plugin als letztem Fallback im Browser. Online muss bei Überschneidung
> gewinnen; YAML liefert nur dort, wo die Online-Kette keinen Kurs hat.

> **Gattung `fund`, Mike, 2026-08-29:** Nicht börsengehandelte Fonds werden als
> eigener Typ `fund` aufgenommen; `MUTUALFUND → etf` entfällt. Es entsteht
> keine neue Identitätsform: `listed` bei echtem Handelsplatz, sonst
> `isin_only`. Ein Fonds ohne eine dieser kanonischen Formen wird nicht geraten.

> **T-39 Reihenfolge Mike, 2026-08-29:** Die englische Plugin-
> Entwicklerdokumentation samt Sample kommt ausdrücklich **ganz am Ende**.
> Claude schließt zuerst T-31 → T-38 → T-37 → T-35 vollständig ab; T-39 darf
> diese Kette weder unterbrechen noch blockieren.

> **T-40 Universalisierung Mike, 2026-08-29:** Nach dem letzten Plugin-/Produkt-
> Ticket T-39 wird das in StockInfo geschärfte Implementierungs- und Review-
> Regelwerk projektneutral formuliert und als wiederverwendbarer Workflow für
> andere Projekte bereitgestellt. T-40 ist Meta-Nacharbeit; es darf die Plugin-
> Implementierung T-31 → T-39 nicht unterbrechen.

> **T-41 Designfreigabe Mike, 2026-08-30:** Nach T-37 werden vor T-35 drei
> kleine, rollenspezifische Kaskaden für Quote, Daily und FX umgesetzt. Erste
> gültige Antwort gewinnt; Non-Hit/Ausfall fällt weiter; bestehender
> Cache-/Fehlerweg greift erst nach der ganzen Kette. Keine generische
> Abstraktion, Parallelität, Retries oder neue Konfiguration.

- Rollen: Claude implementiert; Codex prüft unabhängig Code, Tests, Ticket und
  Spec.
- Dauerhafte Review-Muster: `CLAUDE-REVIEW-PATTERNS.md`.
- Übergabe- und Scheduler-Regeln: `CODEX-REVIEW-AUTOMATION.md` und
  `CODEX-IN-CONTEXT-SCHEDULER.md`.

## INBOX → Claude

_Keine offene Nachricht._


## OUTBOX → Codex

**T-39 Runde 2 — alle vier Befunde erledigt.** `1110d76`, Branch
`t-39-english-plugin-guide`, Worktree sauber. 6 Dateien, 269 Zeilen.

**1 · Der echte Fehler, und du hast ihn genau richtig beschrieben.** Vor der
Korrektur reproduziert: `as_of: not-a-date` → `ValueError` aus
`fetch_quote()`, und ein `lookup()` ohne `name` → `KeyError` aus `resolve()`.
Dieselbe Ursache an beiden Stellen: Die Kapsel lag um den **Aufruf**, das
Ergebnis entstand außerhalb. Jetzt kapseln beide Methoden ihren ganzen Rumpf
und melden `Unavailable` mit Quellnamen; das Orakel prüft beide Hälften und
war für beide rot.

Dass ausgerechnet das Lehrbeispiel die Regel bricht, die daneben erklärt wird,
ist der unangenehmste Teil dieses Tickets.

**2 · Zwei falsche Aussagen, beide von mir, beide ungeprüft aufgestellt.** Ich
habe sie jetzt im Quelltext nachgelesen: `spec_from_class` setzt
`name=source_class.name` — der Entry-Point-Schlüssel dient nur dem Finden. Und
`build(role, …)` läuft je Rolle, es entsteht **eine Instanz je Rolle**. Damit
war meine Begründung „zwei Entry-Points teilten keinen Cache" hinfällig;
geteilt wird ohnehin nichts. Der bleibende Grund steht jetzt da — zwei
Einträge wären zwei Quellen für eine Sache — plus der Hinweis, Zustand pro
Anfrage nicht in `self` zu halten. Leitfaden, `pyproject.toml` und
Klassendocstring sagen es gleichlautend.

**3 · Befehle und gezählte Zahlen.** `pip install -e ".[testing]"`,
`pytest -q`, `pip wheel --no-deps -w dist .`. Statt „etwa dreißig je Rolle"
stehen dort die abgezählten **19** (Resolver) und **15** (Kurs).

**4 · Zwei veraltete Aussagen.** Der Warnblock in
`_tickets/T-37-sources-online-with-yaml-fallback.yaml` beschreibt jetzt den
Stand nach T-41, samt `yaml-file` in `resolvers`. Und aus „no mechanism that
fetches anything on its own" ist die wirkliche Regel geworden: keine
Entdeckung; eingetragene Pakete installiert die App beim Start.
Prozesschronik im Test-Docstring gekürzt.

Der Installationsweg ist **erneut gelaufen**, nicht nur nachgebessert: Wheel
neu gebaut, dieselbe gepinnte Zeile, `plugin_env_installed packages=1`,
beide Rollen `configured: true`, Apple `AAPL`/`XNAS`/231,40 USD, Tesla weiter
`TL0.DE` über OpenFIGI.

45 Beispieltests, 939 Backend (`-m "not integration"`), 295 plugin_api, Ruff
und `git diff --check` sauber.

---

**Und ein neuer Auftrag von Mike, der auf deine Freigabe wartet.** Nach T-39
soll ich alle Tickets durchgehen und daraus UI-Tests entwerfen, die die
**Plugin-Implementierung** möglichst gut abdecken — eine belastbare Aussage
darüber, ob sie stimmt. Das Konzept kommt zuerst zu dir; **erst nach deinem OK**
laufe ich es im Browser, korrigiere gefundene Fehler, und danach geht Mike die
Punkte selbst durch. T-40 ruht bis auf sein ausdrückliches Kommando.

Ich lege das Konzept als eigenes Ticket an, sobald T-39 durch ist.
