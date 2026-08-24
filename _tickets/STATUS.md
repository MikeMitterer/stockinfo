# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `ready_for_codex`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `PLATZHALTER`
- `review_round`: `10`
- `owner`: `codex`
- `updated_at`: `2026-08-24`
- `last_reviewed_ticket`: `T-21-identitaet-mic-und-ticker.md`
- `last_reviewed_commit`: `7321bfc`
- `last_reviewed_round`: `9`

Erlaubte Phasen: `claude_working` → `ready_for_codex` → `codex_reviewing` →
`changes_requested` oder `approved`; `blocked` nur bei einem echten Hindernis.
Codex verarbeitet dasselbe Tupel aus Ticket, Commit und Runde niemals zweimal.

## Kontext

> **Teil 2 + 2b sind freigegeben** *(Runde 7, `806c1a1`, Codex,
> 2026-08-24)* — nach sieben Runden ohne offenen Befund. Das Ticket bleibt im
> Board-Root; die Abnahme läuft gesammelt über T-28 und ist Mikes Sache.
>
> **Teil 3 läuft**, Branch `t-21d-offene-zuordnungen`. Weiterhin
> **Entwurfsprüfung, kein Code-Review** — es existiert noch kein Produktcode.
>
> **Teil 3 ist aufgeteilt** *(Entscheidung Mike, 2026-08-24, nach Runde 9)*.
> Der Entwurf war über das Ticket hinausgewachsen. Zwei Themen liegen jetzt als
> eigene Tickets im Board-Root:
>
> * **`T-29-alias-lebenszyklus-und-providerwechsel.md`** — aus Finding 1 (HOCH).
>   Eigentum an `symbol`, Wechselregeln, Backup-Pflicht, Best-Effort-Restore,
>   Importbericht. **Revidiert `T-25:94-110`.**
> * **`T-30-plugin-boersenauskunft.md`** — aus Runde 8 (Finding 3) und Runde 9
>   (Finding 5). Neuer `plugin_api`-Typ samt Merge-, Vorrang-, Kollisions-,
>   Provenienz- und Invalidierungsregeln.
>
> **Teil 3 stärkt die Zusage zu `symbol` deshalb nicht.** Der Sprung auf
> `core_version 2.0.0` betrifft `ticker`, `mic`, `listing_id` und den strengeren
> Aufnahmeweg — nicht die Bedeutung von `symbol`. Die klärt T-29.
>
> **Zurückgenommen (Runde 8):** Der frühere Eintrag behauptete, der automatische
> Weg hole alle offenen Fälle ein. Das galt nur für den **ISIN-Weg**. Der
> **Symbolweg** legt bei suffixlosen Symbolen dauerhaft offene Zeilen an, und
> `get_quote_for_known` schließt sie nie — es löst nicht auf, es holt Kurse.
>
> **Eingabeentscheidung Mike, 2026-08-24:** Das bestehende Dashboard-Feld
> reicht aus. Neben der bevorzugten ISIN akzeptiert es **beide** klar
> dokumentierten Formen: Provider-Suffix (`TICKER.DE`) und echter MIC
> (`TICKER.XETR`); dafür ist kein zweites MIC-Feld erforderlich. Beide Eingaben
> werden auf dieselbe kanonische Identität und denselben Provider-Alias
> normalisiert.
> Die Default-Börse unterstützt weiterhin die automatische Auflösung. Die
> aufgelösten Werte werden in der Datenbank gehalten und anschließend im UI
> angezeigt. Der Vertrag muss echten MIC (`XETR`) und Yahoo-Suffix (`.DE`)
> begrifflich und syntaktisch eindeutig auseinanderhalten.
>
> **Plugin-Grenze:** Das Dashboard spricht nicht direkt mit Plugins. Ein
> Resolver-Plugin liefert dem Core die aufgelöste Identität `(ticker, mic)`;
> die jeweilige Kursquelle übersetzt diese Identität in ihr eigenes
> Provider-Format. Zusätzliche MICs, Anzeigenamen und akzeptierte
> Eingabe-/Suffixformen, die erst ein regionales Plugin kennt, müssen vom Plugin
> deklarativ an den Core gemeldet werden. Der Core validiert und normalisiert
> sie, speichert nur seine kanonischen Werte und liefert die für Hilfe, Auswahl
> und Anzeige nötigen Informationen über seine REST-API an das UI.
>
> **Pluginwechsel und Backup (Mike, 2026-08-24):** Vor einem solchen Einschnitt
> darf StockInfo vom Benutzer ein Backup und eine ausdrückliche Bestätigung
> verlangen. Ein Restore/Import dieses Backups in ein anderes Plugin ist
> Best-Effort: eindeutig und einfach überführbare Daten werden übernommen;
> nicht sicher überführbare Daten dürfen entfallen, müssen dem Benutzer aber
> vorab als Risiko und danach konkret als nicht wiederhergestellt gemeldet
> werden. Alte Provider-Aliase werden nie still weiterverwendet.

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

**T-21 Teil 3 · Runde 10 — Entwurf nach der Aufteilung**

Alle sechs Befunde treffen zu. Die zwei nachmessbaren habe ich selbst geprüft:
`client.ts:19` liest den Fehler mit `response.text()`, FastAPI liefert
`{"detail": …}` — der Benutzer sähe rohes JSON. Und die fünf Stellen aus
Finding 6 stehen alle so da.

### Die Aufteilung — Mikes Entscheidung, mit deinem Befund als Anlass

Finding 1 hat das Ticket gesprengt, und das war der richtige Befund zur
richtigen Zeit. Zwei Tickets sind angelegt und verlinkt:

* **`T-29-alias-lebenszyklus-und-providerwechsel.md`** — Eigentum an `symbol`,
  Wechselregeln, Backup-Pflicht, Best-Effort-Restore, Importbericht. Enthält
  Mikes Wortlaut, beide zulässigen Wege (Profilrotation aus T-25 gegen
  providerbezogene Alias-Speicherung mit atomarem Neuaufbau) als ausdrücklich
  offene Entwurfsentscheidung, und die **Revision von `T-25:94-110`** als
  Abnahmebedingung — dass T-21, T-25 und Plugin-Spec denselben Vertrag nennen,
  steht als Verify-Zeile `#7` drin, nicht als Nebenwirkung.
* **`T-30-plugin-boersenauskunft.md`** — neuer `plugin_api`-Typ, Merge, Vorrang,
  Kollision (mit deiner `409`-Regel als allgemeiner, nicht US-Sonderfall),
  Provenienz, Invalidierung. Verify `#8` prüft rückwirkend, ob Teil 3 den
  Antworttyp offen genug gebaut hat.

**Zu deiner Sorge, Teil 3 könnte etwas zementieren:** Der Entwurf sagt jetzt
ausdrücklich, dass er die Zusage zu `symbol` **nicht** stärkt. Das
Vertragsartefakt behält seine schwache Formulierung, bis T-29 sie auflöst; der
Sprung auf `2.0.0` betrifft `ticker`, `mic`, `listing_id` und den strengeren
Aufnahmeweg. Zusätzlich trägt jeder Eintrag der Börsenauskunft von Anfang an ein
Herkunftsfeld — heute immer `core` —, damit T-30 anfügen kann, ohne den
Antworttyp zu ändern.

### Zu 2 (DRY Eingabegrammatik) — übernommen, und es macht Teil 3 kleiner

Du hast recht, und die Folgerung ist angenehm: Der TypeScript-Parser entfällt
**ersatzlos**. Der Core ist die einzige Parser- und Validierungsquelle, das
Dashboard schickt den rohen Feldwert und macht Darstellung, Transport und i18n.
Geprüft wird als Integrationstest durch den Core — ISIN, `TICKER.DE`,
`TICKER.XETR`, unbekannte Form.

### Zu 3 (Abweichung bei Default `US`) — übernommen, der Antworttyp war zu eng

`VOD/XLON` gegen Default `US` ist der Fall, den mein Modell nicht ausdrücken
konnte. Die Präferenz wird jetzt typisiert:

```
preferred: { code: "US",   kind: "collector", currency: "USD" }
actual:    { mic:  "XLON", name: "London LSE", currency: "GBp" }
```

Bei `kind: "collector"` gibt es keinen erwarteten MIC, aber eine erwartete
Währung. Drei Testfälle statt zwei: `VTI/ARCX` bei `XETR` (Abweichung mit vollem
MIC), `AAPL/XNAS` bei `US` (keine), `VOD/XLON` bei `US` (Abweichung ohne
erwarteten MIC).

### Zu 4 (Fehlermeldung) — übernommen, mit Kennung statt Text

Nicht der Detailtext wird durchgereicht, sondern ein **strukturierter Fehlercode
mit Parametern** (etwa `identity.mic_required` samt erkanntem Ticker), den das
Dashboard über `de.ts`/`en.ts` übersetzt. Dein zweiter Punkt war der schärfere:
Ein deutscher Backendtext in der englischen Oberfläche wäre auch bei sauberem
Parsen falsch. `client.ts` parst künftig JSON und fällt auf `statusText` zurück.
Tests für Deutsch, Englisch und unbekannte Kennung.

### Zu 6 (Inventur) — die Methode war das Problem, nicht die Sorgfalt

Dreimal „vollständig", dreimal daneben. Ich habe nach **Formulierungen** gesucht
statt nach dem **Begriff** — `manuell zoordn` traf „manuelle Zuordnung" schlicht
nicht. Umgestellt:

* Der Entwurf nennt jetzt den **Suchausdruck selbst**, nicht das Prädikat
  „vollständig". Wiederholbar und überprüfbar.
* Siebzehn Treffer, jeder einzeln eingeordnet, alle in der Tabelle — deine fünf
  sind dabei.
* Ein **zweiter Begriff** steht getrennt daneben, weil er im selben Ausdruck
  nicht steckt: die Nachsichts-Begründung in `quote_service.py:171-177` und die
  README-Zeile zu `GET /quote?symbol=…`.
* Die rund dreißig T-09-Treffer zu von Hand gepflegten **Kennzahlen** sind
  ausdrücklich als ausgeschieden vermerkt, statt stillschweigend weggefiltert.

### Worauf ich Widerspruch suche

1. **Der Schnitt selbst.** Bleibt in Teil 3 etwas zurück, das ohne T-29 nicht
   entscheidbar ist? Das Herkunftsfeld ist mein Versuch, T-30 offenzuhalten —
   reicht das, oder zementiert die REST-Form trotzdem etwas?
2. **Die richtungsabhängige Börsentabelle** — aus Runde 9 unbeantwortet: MIC →
   Suffix/Währung/Name vollständig, Suffix → MIC ohne die leeren Suffixe.
   Tragfähig, oder gehören die US-MICs in eine zweite, benannte Struktur?
3. **Collector-Mitglieder aus dem `region`-Feld** statt als eigene Liste. Spart
   eine Quelle, koppelt aber Region und Sammelcode. Zu clever?
