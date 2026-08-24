# T-30 · Plugin-deklarierte Börsenauskunft

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Plugin-API + Backend + Dashboard) | offen | 1 Tag | Deklarationstyp, Merge- und Vorrangregeln, REST-Ausgabe | — |

**Löst:** Der Börsenkatalog `EXCHANGES` in `app/exchanges.py` ist heute
Core-Wissen und fest verdrahtet. Regionale Plugins bringen aber weitere MICs,
Anzeigenamen und Symbolkonventionen mit — der Plugin-Entwurf sagt das
ausdrücklich und nimmt „derzeit" wörtlich
(`2026-08-19-plugin-system-design.md:365-373`). Für diese Deklaration hat der
heutige Plugin-Vertrag **keinen Typ**.

Ohne sie kann das Dashboard weder vollständige Hilfetexte noch lesbare
Börsennamen für plugin-eigene Handelsplätze zeigen — und ohne einen Weg über
den Core müsste es direkt mit Plugins sprechen, was ausgeschlossen ist.

**Herkunft:** Codex-Review zu T-21 Teil 3, Runde 8 (Finding 3) und Runde 9
(Finding 5). Aus T-21 herausgeschnitten — Entscheidung Mike, 2026-08-24.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)
· Entwurf für dieses Ticket steht aus.

**Hängt an:** T-21 Teil 3 (legt den Core-Katalog und die REST-Form fest, an die
sich Plugin-Einträge anfügen), T-23 (Registry).

---

## Die feste Grenze

**Das Dashboard spricht nie direkt mit einem Plugin.** Ein Plugin deklariert
gegenüber dem Core; der Core validiert, normalisiert, speichert nur seine
kanonischen Werte und liefert dem UI über seine REST-API, was es für Hilfe,
Auswahl und Anzeige braucht.

## Was der Entwurf festlegen muss

Codex hat in Runde 9 fünf Regelbereiche benannt, die alle offen sind:

* **Merge** — wie Plugin-Einträge und Core-Katalog zusammenkommen.
* **Vorrang** — wer gewinnt, wenn beide denselben MIC führen.
* **Kollision** — was passiert, wenn zwei Plugins dasselbe Suffix beanspruchen.
  Der Plugin-Entwurf hat dafür bereits eine `409`-Regel, die **allgemein** gilt
  und kein US-Sonderfall ist.
* **Provenienz** — woher ein Eintrag stammt, muss am Eintrag ablesbar sein.
* **Invalidierung** — was mit deklarierten Einträgen geschieht, wenn das Plugin
  verschwindet oder sich ändert.

Dazu der neue Typ in `plugin_api` samt `API_VERSION`-Sprung (additiv).

## Vorbedingung aus T-21 Teil 3

Teil 3 entwirft die REST-Form der Börsenauskunft **so, dass ein Plugin später
Einträge beisteuern kann, ohne dass sich der Antworttyp ändert**. Wenn dieses
Ticket feststellt, dass das nicht eingehalten ist, ist das ein Befund gegen
Teil 3 und nicht hier zu reparieren.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `plugin_api` | ein deklarativer Typ für Börsen (MIC, Anzeigename, Suffixformen); `API_VERSION` additiv erhöht | | |
| 2 | Core | validiert und normalisiert die Deklaration; speichert nur kanonische Werte | | |
| 3 | zwei Plugins, dasselbe Suffix | Kollision wird erkannt und gemeldet, nicht stillschweigend aufgelöst | | |
| 4 | Plugin und Core führen denselben MIC | die Vorrangregel greift nachvollziehbar | | |
| 5 | Eintrag im REST | Provenienz ist ablesbar (Core oder welches Plugin) | | |
| 6 | Plugin entfernt | deklarierte Einträge verschwinden; kein verwaister MIC bleibt stehen | | |
| 7 | Dashboard | zeigt plugin-gelieferte Börsen in Hilfe und Anzeige — ausschließlich über Core-REST | | |
| 8 | Antworttyp aus T-21 Teil 3 | musste **nicht** geändert werden, um Plugin-Einträge aufzunehmen | | |
| 9 | `make test` | Backend, Plugin-API und Dashboard grün | | |
