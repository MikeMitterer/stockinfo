# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dauerhafte
Entscheidungen stehen in den Tickets und in der Plugin-System-Spec.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-39-english-plugin-developer-guide.md`
- `handoff_commit`: `951f866`
- `review_round`: `1`
- `owner`: `codex`
- `updated_at`: `2026-08-31`
- `last_reviewed_ticket`: `T-35-ui-abnahme-am-laufenden-stack.md`
- `last_reviewed_commit`: `49e4354`
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

**T-39 Runde 1 — Leitfaden und lauffähiges Beispielpaket.** `951f866`, Branch
`t-39-english-plugin-guide`, Worktree sauber.

Alle acht Verify-Zeilen gemessen; Werte und Belege stehen im Ticket.

- `docs/plugin-authors.md` (386 Zeilen) ist die **kanonische** Anleitung.
  Vertragsfelder sind verlinkt statt abgeschrieben. `docs/plugins.md` bleibt
  die deutsche Betreibersicht und verweist für den Autorenteil dorthin.
- `plugin_api/examples/us-example/` ist ein eigenes Paket: eigene
  `pyproject.toml`, eine Quelle in zwei Rollen, `api_version = 2` im eigenen
  Klassenkörper, Anbieter als hereingereichtes Protokoll. 43 Tests ohne Netz
  und ohne Schlüssel, davon rund 36 geerbt.
- Der Installationsweg ist **gelaufen**, nicht beschrieben: Wheel gebaut,
  gepinnt in `plugins.packages`, `plugin_env_installed packages=1`,
  `plugins_loaded names=['us-example', 'yaml-file']`, danach in `/sources` in
  beiden Rollen `configured: true`. End-to-End: Apple über das Beispiel
  (231,40 USD), Tesla fällt von dort an OpenFIGI durch (`TL0.DE`), SAP wird
  gar nicht erst beansprucht.

**Ein Befund am eigenen Beispiel.** Der erste Entwurf las `preferred_mic` als
Filter — die Quelle antwortete auf alles `NotResponsible`, und der Code sah
vernünftig aus. Das Feld ist ein Wunsch und nie leer; der Host füllt es mit
`XETR` vor. Gefunden hat es die geerbte Vertragssuite beim ersten Lauf
(7 rot), nicht das Lesen. Steht jetzt als Test, im Beispielcode und im
Abschnitt „When it does not work".

**Drei Dinge zum Nachprüfen, weil ich sie selbst entschieden habe:**

1. **Zwei Dateien außerhalb des Scope-Vertrags.** Der `Makefile` nimmt die
   Beispieltests in `make test` auf — ein Beispiel, das niemand ausführt,
   stimmt genau bis zur nächsten Vertragsänderung. Und `.gitignore` ignoriert
   jetzt `build/`, `dist/`, `*.egg-info/`: Hier verdeckt sie eine globale
   Datei, auf jeder anderen Maschine landete ein gebautes Wheel im
   Repository.
2. **`PIP_FIND_LINKS` im Abnahmelauf.** Das Wheel liegt auf keinem Index, also
   zeigte der Lauf pip auf ein lokales Verzeichnis. Das ist Betreiber-
   Konfiguration, nicht Plugin-Sache; `app/plugin_env.py` blieb unberührt.
   Mit zusätzlichem `PIP_NO_INDEX=1` scheitert es an der transitiven
   Abhängigkeit `PyYAML` — auch das steht im Ticket.
3. **Ein Beleg eines fremden Tickets wandert.** T-38 Zeile 10 verweist auf
   `docs/plugins.md` für die Pflichtfelder; der Inhalt steht jetzt im
   englischen Leitfaden, erreichbar über einen Klick. Ein Duplikat wäre genau
   das, was T-39 abschaffen soll — aber es ist deine Zeile, nicht meine.

Umfang: 9 Dateien, 1.045 Zeilen — im Budget (10 neu / 1.600). Kein
Produktcode, kein REST-Vertrag, kein Schema.

`ruff` sauber, Backend 939 (`-m "not integration"`), plugin_api 295, Beispiel
43, beide Smokes 20/20, `git diff --check` sauber.
