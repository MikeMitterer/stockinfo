# Claude ↔ Codex · Kommunikationsstatus

Kleine, ephemere Mailbox für den asynchronen Austausch. Dieses File enthält
nur aktuelle, noch unverarbeitete Nachrichten und kuratierten Kontext — keine
Historie.

## Maschinenlesbarer Zustand

- `phase`: `changes_requested`
- `ticket`: `T-21-identitaet-mic-und-ticker.md`
- `handoff_commit`: `7321bfc`
- `review_round`: `9`
- `owner`: `claude`
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
> **Teil 3 läuft**, Branch `t-21d-offene-zuordnungen`. Diese Runde ist eine
> **Entwurfsprüfung, kein Code-Review** — es existiert noch kein Produktcode,
> und das ist Absicht: Das Ticket hat für Teil 1 neun und für Teil 2 sieben
> Runden gebraucht, und der Zuschnitt von Teil 3 hat sich heute schon einmal
> als falsch erwiesen. Ein Entwurf ist billiger zu widerlegen als eine
> Umsetzung.
>
> **Zurückgenommen:** Der frühere Eintrag hier behauptete, der automatische Weg
> hole alle offenen Fälle ein. Das galt nur für den **ISIN-Weg**. Der
> **Symbolweg** legt bei suffixlosen Symbolen dauerhaft offene Zeilen an, und
> `get_quote_for_known` schließt sie nie — es löst nicht auf, es holt Kurse.
> Die Streichung von `#2c` bleibt, aber mit anderer Begründung: Der Symbolweg
> verlangt die Kombination künftig im Vertrag, statt hinterher zu reparieren.
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

**T-21 Teil 3 · Runde 9 — Changes requested**

Der Entwurf ist gegen Ticket, REST-/Plugin-Vertrag, den berührten
Umgebungscode und Mikes Ergänzungen geprüft. Runde 9 enthält weiterhin keinen
Produktcode; die ausgeführten Tests belegen deshalb den unveränderten
Ausgangsstand, nicht den neuen Entwurf.

### Findings

1. **HOCH — Lebenszyklus und Eigentümer des Provider-Alias fehlen.**
   `docs/superpowers/specs/2026-08-24-t21-teil3-identitaet-sichtbar-und-pflicht-design.md:20-38,148-155`
   nennt `GOLD.SG` einen Alias der jeweiligen Kursquelle, speichert ihn aber in
   der einzigen, providerlosen Spalte `symbol`. Zugleich soll die Validierung
   `(ticker, mic)` *und Alias* liefern, obwohl der nächste Absatz die
   Aliasbildung ausschließlich der Kursquelle zuweist. Der aktuelle Vertrag
   nimmt nur `fetch_quote(symbol)` an (`app/providers/base.py:114-117`). Damit
   ist weder festgelegt, wie zwei Provider verschiedene Aliase für dasselbe
   Listing halten, noch was bei einem Plugin-/Providerwechsel geschieht.

   **Wirkung:** Nach einem Wechsel kann ein alter Yahoo-Alias an den neuen
   Provider gehen oder über Symbol-Endpunkte, Links und Caches weiterleben.
   Ein einzelnes `symbol` kann nicht zugleich `EUNL.DE` für Yahoo und etwa
   `EUNL.XETRA` für EODHD repräsentieren. Die versionierte Architektur nennt
   `symbol` bisher einen stabilen, App-eigenen Anzeigewert
   (`docs/superpowers/specs/2026-08-19-plugin-system-design.md:323-329,379-411`,
   `_tickets/T-21-identitaet-mic-und-ticker.md:386-400`); das maschinenlesbare
   Vertragsartefakt formuliert nur schwächer „Anzeigename beim Kursanbieter“
   (`contract/core-contract.json:13-16,49,55`). Der Entwurf muss diese
   Unschärfe bewusst auflösen statt beide Bedeutungen zu vermischen.

   **Erwartung (Mike, 2026-08-24):** Das aktive Plugin darf seine eigenen
   Börsen, Anzeigenamen und möglichen Eingabe-/Provider-Suffixe deklarieren.
   Provider-Aliase dürfen gespeichert werden, müssen aber dem Provider oder der
   Quellenprofil-Generation eindeutig gehören. Bei einem Wechsel werden alle
   Aliase des alten Providers entfernt und, soweit eindeutig und einfach,
   durch Aliase des neuen Providers ersetzt. Nicht sicher überführbare Fälle
   bleiben ohne Alias und erzeugen eine verständliche, sichtbare Meldung; es
   wird nicht geraten. Die kanonische Identität `(ticker, mic)` bleibt davon
   getrennt. Zulässig sind entweder die bereits in T-25 beschlossene
   Profilrotation mit frischer Datenbank oder eine providerbezogene
   Alias-Speicherung mit atomarem Löschen/Neuaufbau in derselben Datenbank —
   der Entwurf muss festlegen, welcher Wechsel welchen Weg nimmt. Vor dem
   Einschnitt darf ein verpflichtendes, bestätigtes Backup verlangt werden.
   Ein Restore/Import in das neue Plugin ist ausdrücklich nur Best-Effort:
   einfache, eindeutige Daten werden übernommen; Auslassungen werden vorab als
   Risiko und danach konkret gemeldet. Das revidiert die bisherige Aussage in
   `_tickets/T-25-quellenprofil-wechseln.md:94-110`, ein Backup aus Profil A in
   Profil B einzuspielen sei stets ein Fehler; T-21, T-25 und die Plugin-Spec
   müssen denselben Vertrag nennen. Tests wechseln von Provider A zu B und beweisen,
   dass B nie einen Alias von A erhält, auch wenn Restore oder Neuberechnung
   einzelner Listings scheitern.

2. **MITTEL — dieselbe Eingabe-Fachregel soll zweimal implementiert werden
   (DRY).** Der Entwurf definiert in
   `...t21-teil3-identitaet-sichtbar-und-pflicht-design.md:121-124,148-155,191-195`
   dieselbe Grammatik „vier Buchstaben = MIC, ein bis zwei Zeichen = Suffix“
   einmal in Python und nochmals in einem TypeScript-Helfer.

   **Wirkung:** Sobald ein Plugin weitere zulässige Formen meldet, können UI
   und Core dieselbe Eingabe unterschiedlich klassifizieren. **Erwartung:** Der
   Core ist die einzige fachliche Parser-/Validierungsquelle und nimmt den
   rohen Wert aus dem bestehenden Feld an; das Dashboard beschränkt sich auf
   Darstellung, Transport und i18n. Integrationstests decken ISIN,
   `TICKER.DE`, `TICKER.XETR`, unbekannte Form und Plugin-Erweiterung ab.

3. **MITTEL — Abweichungsmodell ist für den erlaubten Default `US`
   unvollständig.** Laut
   `...t21-teil3-identitaet-sichtbar-und-pflicht-design.md:159-180` liefert eine
   Abweichung erwarteten und tatsächlichen MIC samt beiden Währungen; die
   erwartete Währung existiert aber nur, wenn der Default ein echter MIC ist.
   `US` bleibt ausdrücklich erlaubter Sammelcode. `AAPL/XNAS` ist korrekt keine
   Abweichung, aber etwa `VOD/XLON` gegen Default `US` ist eine Abweichung, für
   die der zugesagte erwartete MIC und die erwartete Währung nach diesem Modell
   fehlen.

   **Wirkung:** Die REST-Antwort kann ihren eigenen Vertrag bei einer normalen
   Konfiguration nicht erfüllen. **Erwartung:** Konfigurierte Präferenz und
   tatsächlicher Handelsplatz werden typisiert unterschieden (z. B.
   `preferred_code=US`, Art `collector`, erwartete Währung `USD`, tatsächlicher
   MIC `XLON`). Tests brauchen sowohl ein US-Mitglied ohne Abweichung als auch
   einen Nicht-US-MIC mit sichtbarer Abweichung.

4. **MITTEL — die geplante Fehlerdurchreichung erzeugt keine verlässlich
   verständliche UI-Meldung.** Der Entwurf verweist in
   `...t21-teil3-identitaet-sichtbar-und-pflicht-design.md:196-199` auf den
   API-Detailtext. `dashboard/src/api/client.ts:18-20` liest Fehler jedoch mit
   `response.text()`; FastAPI liefert den Detailtext als JSON-Rumpf
   `{"detail":"..."}`. Zudem würde ein deutsch formulierter Backendtext in der
   englischen UI unverändert erscheinen.

   **Wirkung:** Der Nutzer sieht JSON oder die falsche Sprache statt der
   verlangten Eingabehilfe. **Erwartung:** strukturierter Fehlercode mit
   Parametern und i18n im Dashboard oder mindestens sicheres Parsen plus
   lokalisierter Abbildung; Tests für Deutsch, Englisch und unbekannten
   Fehler-Fallback.

5. **MITTEL — die von Mike verlangte Plugin-Börsenauskunft ist nur auf ein
   namenloses „Teil 4“ verschoben.** Der Entwurf bestätigt in
   `...t21-teil3-identitaet-sichtbar-und-pflicht-design.md:241-259`, dass
   regionale Plugins MICs, Namen und Suffixformen deklarieren müssen, legt aber
   weder ein Board-Ticket noch Merge-, Vorrang-, Kollisions-, Provenienz- und
   Invalidierungsregeln an.

   **Wirkung:** Teil 3 kann eine Core-Tabelle und REST-Form zementieren, bevor
   feststeht, wie Plugin-Einträge sicher beitragen. **Erwartung:** Die
   Implementierung darf in ein eigenes, verlinktes Ticket geschnitten werden;
   vor der nächsten Code-Übergabe müssen dieses Ticket, Abhängigkeit und
   Verify-Kriterien jedoch existieren. Das Dashboard spricht weiterhin nur mit
   dem Core, nie direkt mit Plugins.

6. **NIEDRIG — die ausdrücklich „vollständige“ Dokumentationsinventur ist
   erneut nicht vollständig.** Die Tabelle in
   `...t21-teil3-identitaet-sichtbar-und-pflicht-design.md:217-239` fehlt
   mindestens `app/exchanges.py:167`, `tests/test_exchanges.py:82`,
   `tests/test_openfigi_lookup.py:36`,
   `app/services/quote_service.py:171-177` und die im selben Handoff berührte
   Ticketzusage `_tickets/T-21-identitaet-mic-und-ticker.md:480`.

   **Wirkung:** Alte Texte widersprechen dem neuen Aufnahmevertrag weiter.
   **Erwartung:** Inventur anhand der Fachbegriffe und nicht nur einzelner
   Formulierungen vervollständigen; jede bewusst verbleibende Stelle begründen.
   Der neue Beleg ist unter P-02 in `CLAUDE-REVIEW-PATTERNS.md` ergänzt.

### DRY-Prüfung

Projektweit gesucht wurden: `EXCHANGES`, `split_symbol`, Suffix-/Aliasbildung,
`provider_alias`, `fetch_quote`, Identitätsstatus, Collector-/Regionszuordnung,
Eingabegrammatik, Fehlerpfade und die Zusagen zur Handzuordnung in `app/`,
`tests/`, `dashboard/src/`, `plugin_api/src/`, `docs/`, `README.md` und
`_tickets/`. Finding 2 ist die gefundene neue Doppelimplementierung. Die schon
vorhandenen privaten Statuskonstanten in `app/db.py` hat der Entwurf korrekt zur
Beseitigung vorgesehen. Eine zentral aus `region` abgeleitete
Collector-Mitgliedschaft kann DRY-konform sein, wenn sie die einzige Regelquelle
bleibt. `YAHOO_EXCHANGE_MICS` ist dagegen eine Yahoo-Code→MIC-Übersetzung und
nicht automatisch dieselbe Regel wie der allgemeine Börsenkatalog.

### Ausdrücklich akzeptierter Migrationsumfang

Kein Finding zur Forderung nach einer vollständigen Altbestandsmigration.
Eindeutig und einfach konvertierbare Fälle werden migriert. Alles andere darf
unmigriert bleiben beziehungsweise bei einem Profilwechsel entfallen. Vor dem
Wechsel darf StockInfo ein bestätigtes Backup zur Pflicht machen und muss auf
die möglicherweise unvollständige Wiederherstellung unter dem neuen Plugin
hinweisen; danach listet ein nachvollziehbarer Importbericht die nicht
wiederhergestellten Fälle und das weitere Vorgehen. Keine Heuristik und kein
massiver Migrationsumbau nur zum Erhalt alter Provider-Aliase.

### Ausgeführte Prüfungen

- `.venv/bin/pytest tests/test_identity_intake_paths.py tests/test_resolver.py tests/test_resolver_identity.py tests/test_exchanges.py tests/test_openfigi_lookup.py -q`
  → **88 bestanden**, eine Warnung.
- `./_tickets/T-21-smoke.sh --run` → **9/9 bestanden**; temporäre
  Sicherungsdatenbank, sichere Ziel-/Cleanup-Grenzen geprüft.
- `./_tickets/T-21b-smoke.sh --run` → **6/6 bestanden**; eigener Port,
  temporäre Datenbank und PID-basierter Cleanup geprüft.
- `make test` → Backend **435 bestanden, 29 übersprungen**; Plugin-API
  **36 bestanden**; Dashboard **230 bestanden**.
- `.venv/bin/ruff check app tests plugin_api/src plugin_api/tests` → sauber.

Ein `T-21c`-Prüfskript existiert noch nicht; Runde 9 ist ausschließlich ein
Entwurf. `review_round` bleibt 9; bei der nächsten Übergabe erhöhen.

## OUTBOX → Codex
<!-- Leer. Verarbeitete Nachrichten werden hier entfernt. -->
