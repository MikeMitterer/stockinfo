# T-30 · Plugins ergänzen Börsen und deklarieren ihre Unterstützung

Ein Plugin soll **zusätzliche Handelsplätze nutzbar machen**, ohne dass dafür
StockInfo selbst geändert werden muss.

Bisher begrenzt der fest eingebaute
Börsenkatalog diese Erweiterbarkeit.

Beispiel: Ein regionales Plugin unterstützt eine Börse, die StockInfo noch
nicht kennt. Es soll deren Börsenkennung (MIC) und Namen ergänzen können.
Danach lässt sich ein Wertpapier dieses Handelsplatzes regulär aufnehmen.

Für eine bereits bekannte Börse meldet das Plugin nur seine Unterstützung.
**Bestehende Börsendefinitionen bleiben erhalten**; abweichende Schreibweisen
seines Datenanbieters übersetzt das Plugin intern.

Der Core-Teil ist **von Claude in Runde 2 freigegeben**. Bestehende Symbole
werden durch dieses Ticket weder umdefiniert noch migriert.

## Für dich

Aktuell ist **kein Handgriff nötig**.

Codex führt das Ticket als nächstes Element der beauftragten Kette aus.
Claude hat den Umfang vor Produktcode geteilt. Oberfläche, Autor-Harness
und Beispiel stehen in [T-64](T-64-boersen-ui-und-autorennachweise.md).

### Bisherige Antworten und Rückmeldungen

Mike, 2026-09-07: „Ich halte es doch für relevant - ein potentieller Plugin-Author braucht das, oder sehe ich da was falsch?“

Einordnung korrigiert: Die bisherige Beschränkung auf vorhandene Plugins war
zu eng. Ohne T-30 begrenzt der fest eingebaute Katalog die Erweiterbarkeit.

Mike: „Weshalb sollte jemand die Core-Aliases überschreiben?“

Antwort und vereinbarte Eingrenzung: Anbieterübersetzungen gehören ins Plugin.
Für T-30 genügt „bestehende Börsen referenzieren, fehlende Börsen ergänzen,
widersprüchliche Deklarationen ablehnen“. Mike bestätigt: **„Ja, halte das so fest“**.

## Umsetzung und technische Nachweise

### Scope-Vertrag · 2026-09-08

Ergebnis: Ein externes Plugin deklariert einen neuen MIC, ein Nutzer nimmt
darüber ein Asset regulär auf, und REST/Exchanges zeigen Quelle und
Unterstützung je Rolle ohne Änderung bestehender Aliase oder Assets.

1. Optionaler Plugin-Vertrag für Handelsplätze und Rollenabdeckung samt
   gemeinsamer Validierung und Autor-Harness.
2. Deterministischer Core-Katalog aus dem aktiven Profil, Aufnahmeweg und
   REST-Auskunft einschließlich Konflikten und Entfernung.
3. Gezielte Akzeptanz- und Konflikttests über Aufnahmeweg und REST.

Der [Entwurf](../docs/superpowers/specs/2026-09-08-plugin-exchanges-design.md)
legt Vertragsform, Lebenszyklus, Grenzen und Akzeptanzfälle fest. Die
Schätzung von 16–20 Produktdateien, 8–10 Test-/Dokumentationsdateien und
1400–1800 manuellen Diff-Zeilen überschreitet den allgemeinen 800-Zeilen-
Riegel. Claude hat mit `split` entschieden: T-30 behält den Core bis REST.
Einmalig genehmigtes Budget: höchstens 14 Produktdateien, 8–10 Test-/
Dokumentationsdateien und 1100 manuelle Diff-Zeilen. Die UI und der
Autor-Harness samt Beispiel sind nach T-64 abgetrennt.
Keine Migration, keine Alias-Überschreibung, kein ISO-Vollimport und kein
neues Test-Subsystem. Der bestehende UI-Entwurf vom Vortag bleibt unberührt.

### Verbindlicher Umfang

**Aktueller Lieferumfang nach dem Split:** Die UI- und Autor-Harness-Anteile
der folgenden Gesamtanforderungen gehören zu T-64. T-30 liefert den
Plugin-/Core-/REST-Pfad. Die frühere Gesamtbeschreibung bleibt als Bezug
erhalten und ist keine zusätzliche Implementierungszusage dieser Übergabe.

- Plugins können neue MICs mit lesbarem Börsennamen deklarieren und ihre
  Unterstützung für bestehende oder neue MICs je Quellenrolle angeben.
- Der Core validiert die Angaben und führt sie mit dem bestehenden Katalog
  zusammen. Eine Unterstützungsangabe für einen vorhandenen MIC ändert
  dessen Definition nicht. Widersprüche werden ausdrücklich gemeldet;
  weder Ladereihenfolge noch Plugin-Vorrang überschreiben einen Core-Eintrag.
- Neue Handelsplätze sind über den regulären Aufnahmeweg mit Ticker und MIC
  verwendbar. Die Deklaration bleibt kein reiner Anzeigeeintrag.
- Herkunft und Unterstützung werden über Core-REST ausgegeben und auf
  „Exchanges“ angezeigt. Das Dashboard spricht niemals direkt mit Plugins.
- Entfernte Plugins hinterlassen keine fälschliche Unterstützungsmarkierung.
  Der Katalog berücksichtigt weiterhin vorhandene Deklarationen. Das
  Entfernen eines Plugins löscht keine gespeicherten Assets.

### Ausdrücklich ausgenommen

Kein Überschreiben bestehender Core-Aliase oder anderer Core-Börsendefinitionen,
keine automatische Umdefinition gespeicherter Symbole und keine daraus
abgeleitete Datenmigration. Insbesondere entfällt der aus T-29 übernommene
Migrationsumfang von #6c. Ein neu ergänzter MIC lässt vorhandene Zeilen unverändert.

Die Schreibweise der externen API ist Sache des jeweiligen Plugins: Aus
`EUNL` / `XETR` bildet es die benötigte Anbieterkennung. Ein providerspezifisches
Suffix ist kein Grund, den Core-Alias zu ändern.

### Akzeptanz und Bezug zur bisherigen Matrix

Die ursprünglichen IDs und leeren Human-Felder bleiben unten als Historie
vollständig erhalten. Aktuell gilt insbesondere:

| Bezug | Geltende Anforderung |
|---|---|
| #1, #2 | Deklaration für neue Börsen und Unterstützung je Rolle; kanonische Validierung im Core. Genaue API-Form und Versionsbehandlung im Entwurf festlegen. |
| #2c–#3 | Eingaben dürfen keine widersprüchliche MIC-/Alias-Auflösung erzeugen. Sammelcodes bleiben von MICs getrennt. |
| #4 | Bestehenden Core-MIC referenzieren ist erlaubt; widersprüchliche Neudefinition wird abgelehnt. Keine überschreibende Vorrangregel. |
| #5 | Herkunft und deklarierte Unterstützung sind über REST nachvollziehbar. |
| #6, #6b | Katalog und Unterstützung spiegeln die geladenen Deklarationen wider; kein veralteter Zustand nach Plugin-Entfernung. |
| #6c | Ersetzt durch Bestandsschutz: Ein Überschreibversuch verändert weder Core-Alias noch gespeicherte Symbole. Keine Symbolmigration. |
| #7 | Neue Handelsplätze im Aufnahmefeld akzeptieren; Katalog und Unterstützung auf „Exchanges“ über REST anzeigen. |
| #8, #9 | Vorhandene REST-Zusagen erhalten und passende Vertrags-, Integrations- und Dashboardtests ausführen. |

Keine neue Live-Verifikation und keine technische Freigabe mit dieser
Scope-Entscheidung. Die frühere Time-box von einem Tag ist vor Umsetzung
gegen den konkretisierten Entwurf zu prüfen.

### Gezielte Vertragsprüfungen · Entscheidung vom 2026-09-07

Mit der Zurückstellung von [T-34](postponed/T-34-zusage-gegen-laufzeit.md)
bleiben die Prüfungen der hier neu eingeführten Zusagen Teil von #8/#9:
Plugin-Vertragsprüfungen im Autor-Harness und Integrationstests über den echten
Plugin-Lader → Core → REST. Sie belegen neue MICs im Aufnahmeweg, Unterstützung
je Rolle, Herkunft sowie die ausdrückliche Ablehnung widersprüchlicher
Deklarationen einschließlich Bestandsschutz für Core-Aliase und Assets.
Plugin-Entfernung und verbleibende Deklarationen werden ebenfalls geprüft.
Die Autor-Dokumentation enthält ein ausführbares Deklarationsbeispiel samt
Prüfbefehl. Ein allgemeines Framework zur Zuordnung sämtlicher Vertragszusagen
zu Tests ist keine Voraussetzung für T-30.

### Auflösung

Der Core-Teil ist implementiert und am 2026-09-08 von Claude in Runde 2
für `441b4b0` freigegeben. Mikes Abschlussbestätigung ist noch offen.
Die Kette bleibt unverändert, T-64 ist noch nicht eingeordnet.

### Implementierung und Nachweise · Codex, 2026-09-08

`ExchangeSpec` und `MicCoverage` sind optionale öffentliche Deklarationen.
Der Core prüft das vollständige Profil vor dem Quellenbau. Widersprüche
verwerfen alle beteiligten Quellen, ohne Ladegewinner; Referenzen auf
entfallene Definitionen werden ebenfalls abgewiesen. Neue App-Suffixe sind
die MICs selbst, bestehende Core-Aliase bleiben erhalten. REST ergänzt
`declared_by`, `support` und `unspecified_support`; der vorhandene
Core-Katalog und die Herkunftsform bleiben kompatibel.

Der erste Akzeptanzlauf war rot (neue Deklaration noch nicht importierbar),
der Fall ohne Deklaration grün. Danach zeigte der echte Aufnahmeweg eine
vorhandene Lücke: Neuaufnahme verwendete den Abruf für bekannte Assets und
hatte deshalb bei vertragskonformen Kursplugins keinen Namen/keine Gattung.
`get_quote_by_identity` beschafft die Beschreibung, hält aber den genannten
MIC fest. Refresh vorhandener Assets bleibt beim bekannten Datensatz.
Der alte No-Resolver-Testdouble erhält die vorhandene `resolve_symbol`-
Schnittstelle; sein Ergebnis bleibt `NotFound`.

| Bezug | Konkretes Orakel | AI |
|---|---|:--:|
| #1–3 | Struktur-/Wertprüfung, unbekannte Referenzen und Rollen in `test_exchange_declarations.py`; ungültige Quellen erhalten Diagnosen. | ✅ |
| #4, #6c | Core-Überschreibversuch bleibt unwirksam; widersprüchliche neue Definitionen werden in beiden Ladereihenfolgen abgewiesen. | ✅ |
| #5 | Echter Start → `POST /instruments/intake` → `GET /exchanges`: Quelle, Rolle, Bestandsumfang, Einsatzbereitschaft. | ✅ |
| #6, #6b | Identische Deklarationen behalten verbleibende Quellen; Entfernung beseitigt Katalog-/Supporteinträge und lässt gespeicherte Assets stehen. | ✅ |
| #7 Core | Neues `DEMO.XBUD` ergibt HTTP 201 und persistiertes `(DEMO, XBUD)`; ohne Deklaration HTTP 400. | ✅ |
| #7 UI, #8/#9 Autor-Harness | Nach T-64 abgetrennt, hier nicht als umgesetzt gewertet. | ➖ |
| #8/#9 Core | Gesamtlauf: 1129 Backend bestanden, 29 übersprungen, 8 Onlinefälle abgewählt; Plugin-API 309/1 übersprungen, Beispiel 47, Dashboard 339 samt ESLint. | ⚠️ |

```bash
.venv/bin/pytest -q tests/test_exchange_declarations.py tests/test_plugin_exchanges.py tests/test_symbol_ambiguity.py
make test ARGS="-m 'not integration'"
```

Gezielt zuletzt **26 bestanden**. Gesamtlauf ohne vorbereitete Datenbank
oder manuellen Datenpfad: `/tmp/stockinfo-t30-suite.log`. Beide Plugin-Ladewege
verwenden echte Modulimporte; beim Entry-Point-Fall wird nur die Discovery
durch ein echtes `importlib.metadata.EntryPoint`-Objekt ersetzt. Keine
Paketinstallation behauptet. Onlinefälle bleiben ausdrücklich ungeprüft.

Mutanten jeweils rot, anschließend zurückgenommen: Validierung entfernt
7/15 rot, Konfliktsperre entfernt 3/15 rot, unbekannte Referenzen erlaubt
1/15 rot, Betriebsfähigkeit immer wahr 1/15 rot; Katalogveröffentlichung
entfernt und Entfernung nicht invalidiert jeweils 2/4 vertikale Fälle rot.
Logs: `/tmp/stockinfo-t30-mutant-*.log`. Alle Datendateien liegen in pytest-
Tempverzeichnissen. Ruff über alle geänderten Python-Dateien grün;
vollständiges AST-Bezeichnerinventar ohne deutschen Bezeichner.

DRY: bestehende MIC-/Währungsvalidierung wiederverwendet; ein zentraler
Profilkatalog, ein Pfad zur Beschreibung neuer Listings. Keine parallele
REST-Tabelle, kein erfundener Handles-Aufruf, kein Test-Subsystem. Die
Paketveröffentlichung ist nicht Bestandteil dieses Entwicklungsauftrags;
API_VERSION bleibt wegen der optionalen Erweiterung 2, data_version bleibt
unverändert. UI, Autor-Harness und Beispiel folgen erst mit T-64.

## Frühere Fassung · Historie

### Review Runde 1 und Korrektur · 2026-09-08

Claude prüfte `0336d10` gegen `5b1d748`: Implementierung, 26 gezielte Tests,
1129 Backendtests, Ruff, Bezeichnerinventar und Split bestätigt. Ein Finding:
Für identische Core-Referenzen fehlte der negative Mutant der Schranke
`if mic not in _CORE`. Mit `if True` blieb die gesamte Suite grün, obwohl
eine identische Xetra-Deklaration den Alias DE durch XETR ersetzen konnte.
Ergebnis: `changes_requested`, nur dieser zusätzliche Test erforderlich.

Codex ergänzt `test_identische_referenz_ersetzt_den_core_eintrag_nicht`:
identische Referenz akzeptiert, Quelle einsatzbereit, Core-Definition und
Alias DE unverändert, EUNL.DE weiterhin auflösbar. Derselbe Mutant wird jetzt
rot: **alias XETR != DE**, 1 fehlgeschlagen/15 abgewählt. Nach Rücknahme
**27 gezielte Tests bestanden**, Ruff grün. Keine Produktänderung. Log:
`/tmp/stockinfo-t30-mutant-core-reference.log`. Die bereits unabhängig
bestätigte Gesamtsuite wurde für diese reine Testergänzung nicht wiederholt.

Die folgende Fassung dokumentiert die Herkunft und bisherigen Prüfkennungen.
Ihre überschreibenden Vorrangregeln und der Alias-Migrationsauftrag sind durch
Mikes Entscheidung oben abgelöst und keine aktuellen Anforderungen.

<details>
<summary>Vor der Eingrenzung vom 2026-09-07</summary>

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
* **Bestandsschutz für veröffentlichte Aliase** — siehe unten. Aus T-29
  übernommen, als dieses am 2026-09-07 verworfen wurde.

Dazu der neue Typ in `plugin_api` samt `API_VERSION`-Sprung (additiv).

## Ein veröffentlichter Alias ist eine Zusage

*(Aus T-29 übernommen; dort war es die letzte offene Frage, nachdem T-21, T-23
und T-31 den Alias als Abrufschlüssel abgelöst hatten. Gemessen 2026-09-07.)*

`symbol` entsteht bei der Anlage eines Instruments **einmal** aus der
kanonischen Identität — `provider_alias(ticker, mic)` macht aus
`('EUNL', 'XETR')` den Wert `EUNL.DE`. Danach schreibt ihn nichts mehr: Er
steht nicht in `_META_FIELDS` und überlebt deshalb jede Aktualisierung
unverändert. Die Ableitungsvorschrift steht dagegen in genau der Tabelle, die
dieses Ticket für Plugins öffnet: `EXCHANGES[mic].alias`.

Daraus folgt eine Regel, die der Entwurf mitnehmen muss:

> **Ein einmal ausgelieferter Alias wird nicht umdefiniert.** Geschieht es doch
> — durch Korrektur im Core oder durch ein Plugin, das einen MIC neu belegt —,
> müssen die bereits gespeicherten `symbol`-Werte mitgezogen werden.

Ohne sie tragen alte Zeilen die alte und neue Zeilen die neue Konvention,
nebeneinander in derselben Tabelle, ohne Fehler und ohne Meldung. **Neue MICs
hinzuzufügen ist davon nicht betroffen** — nur das Ändern eines bestehenden
Alias erzeugt den Bruch. Der Vorrangfall aus dem Merge oben ist genau ein
solcher Fall, sobald ein Plugin einen MIC des Core-Katalogs überschreibt.

Zwei Dinge, die hier ausdrücklich **kein** Problem sind:

* **Mehrdeutigkeit.** Einen `UNIQUE`-Index auf `symbol` gibt es nicht; eindeutig
  sind `isin`, `listing_id`, `(ticker, mic)` und `(base, quote_currency)`. Zwei
  gleichnamige Listings sind vorgesehen, die `by-symbol`-Wege antworten mit
  `409`.
* **Der Abruf.** Seit `API_VERSION 2` trägt `QuoteRequest` nur die Identität;
  jede Quelle bildet ihr Anbietersymbol selbst. Ein geänderter Alias kann
  deshalb keinen Abruf brechen, nur Anzeige und `by-symbol`-URLs verschieben.

Nachrangig, aber beim Entwurf mitzudenken: Das Alphabet der Aliase ist Yahoos
(`XETR → DE`, `XSTU → SG`, `XLON → L`, `XTSE → TO`, US-Plätze ohne Suffix,
Krypto als `BTC-EUR`). Der Wert ist App-eigen und abgeleitet, sein Vokabular
stammt aus einer Quelle. Solange Yahoo in der Kette steht, fällt das nicht auf.

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
| 1 | `plugin_api` | ein deklarativer Typ für Börsen (MIC, Anzeigename, **ein** optionaler Alias) und getrennt davon für Sammelcodes; `API_VERSION` additiv erhöht | | |
| 2 | Core | validiert und normalisiert die Deklaration; speichert nur kanonische Werte | | |
| 2c | ein **vierstelliger** Alias | wird als Alias erkannt, nicht wegen seiner Länge für einen MIC gehalten | | |
| 2d | ein Token trifft als MIC **und** als Alias verschiedene Börsen | benannter Konflikt mit eigener Fehlerkennung, kein stiller Vorrang | | |
| 2e | ein Plugin meldet einen Sammelcode | er landet als `kind: collector`, **nie** in einem `mic`-Feld | | |
| 3 | zwei Plugins, dasselbe Suffix | Kollision wird erkannt und gemeldet, nicht stillschweigend aufgelöst | | |
| 4 | Plugin und Core führen denselben MIC | die Vorrangregel greift nachvollziehbar | | |
| 5 | Eintrag im REST | Provenienz ist ablesbar (Core oder welches Plugin) | | |
| 6 | Plugin entfernt | deklarierte Einträge verschwinden; kein verwaister MIC bleibt stehen | | |
| 6b | `COLLECTOR_CODES` bei dynamischen Plugins | **keine** beim Import eingefrorene Menge dient als Wahrheit; gefragt wird der zusammengeführte Katalog, oder die Ableitung wird bei Invalidierung erneuert (Auflage aus T-21 Runde 13) | | |
| 6c | ein bestehender Alias wird geändert (Core-Korrektur oder Plugin-Vorrang) | gespeicherte `symbol`-Werte ziehen mit; keine zwei Konventionen in einer Tabelle. Ein **neu hinzugefügter** MIC lässt vorhandene Zeilen unberührt | | |
| 7 | Dashboard | zeigt plugin-gelieferte Börsen in Hilfe und Anzeige — ausschließlich über Core-REST | | |
| 8 | Antworttyp aus T-21 Teil 3 | musste **nicht** geändert werden, um Plugin-Einträge aufzunehmen | | |
| 9 | `make test` | Backend, Plugin-API und Dashboard grün | | |

</details>

## Review-Historie · Scope-Checkpoint: split, 2026-09-08

Geprüft hat **Claude** als zugeordneter Verifier, Prüfstand `d0e6ad0`.
Nach Vertrag nur Ziel, Diff-Statistik und neu berührte Flächen — **kein
Code-Review**, keine zusätzlichen Qualitätsanforderungen. Der Checkpoint kam
vor dem ersten Produktedit; genau so ist der Riegel gedacht.

### Warum nicht `continue`

Die Schätzung von 1400–1800 manuellen Zeilen ist mehr als das **Doppelte** des
800-Zeilen-Riegels, und es existiert noch keine Zeile Code. Ich darf das Budget
einmal erweitern — eine Verdopplung auf Verdacht wäre aber keine Erweiterung
mehr, sondern das Abschalten der Grenze. Landet der Diff dann bei 2200, ist der
Hebel schon verbraucht.

Dazu die Breite: berührt werden Plugin-API, Registry/Loader, Core-Katalog,
REST und Dashboard — **fünf Produktschichten**. Der Vertical-Acceptance-Riegel
will zuerst einen dünnen vertikalen Pfad grün sehen und erst danach die
horizontale Verbreiterung.

### Warum `split` und nicht `reduce`

Nichts an dem Umfang ist überflüssig — es ist nur zweierlei. Die Trennlinie
zieht dein eigener Entwurf in „Umsetzung in prüfbaren Schritten": Schritte 1
und 2 sind der vertikale Pfad samt Schutzregeln, Schritt 3 ist die Oberfläche
und das Autorenbeispiel. Auch dein erster Akzeptanzfall endet bei
`GET /exchanges` und braucht keine UI.

Entscheidend ist, dass die Abhängigkeit **einseitig** ist: Die feste Grenze im
Ticket sagt, das Dashboard spricht ausschließlich über Core-REST. Die UI kann
also erst entstehen, wenn REST steht, und ist danach reiner Konsument. Das ist
ein natürlicher Schnitt entlang einer bestehenden Grenze, kein künstlicher.

### Der Schnitt

**T-30 behält** — unabhängig lieferbar und über den bereits entworfenen
Akzeptanzfall prüfbar:

- optionaler Plugin-Vertrag für Handelsplätze und Rollenabdeckung samt
  gemeinsamer Validierung
- deterministischer Core-Katalog aus dem aktiven Profil, Konflikte,
  Plugin-Entfernung
- regulärer Aufnahmeweg mit neuem MIC bis in die Persistenz
- `GET /exchanges` mit Herkunft und Unterstützung je Rolle

Beobachtbares Ergebnis: frischer Start, `DEMO.XBUD` aufnehmen, Wert
gespeichert, Deklaration und Herkunft über REST lesbar — ohne Deklaration
bleibt derselbe Eingang abgewiesen.

**Neues Ticket bekommt** Schritt 3: Exchanges-Oberfläche, Browserlauf für
DE/EN und schmales Fenster, Autor-Harness und ausführbares Beispiel.

### Budget für das verkleinerte T-30

Damit du nicht in einen zweiten Checkpoint für eine absehbare Überschreitung
läufst, erweitere ich hiermit **einmalig** auf **höchstens 14 Produktdateien
und 1100 manuelle Diff-Zeilen**, Test-/Dokumentationsdateien wie geplant.
Damit ist die eine erlaubte Erweiterung dieses Tickets verbraucht.

Die Zahl ist aus deiner Gesamtschätzung abgeleitet, nicht selbst gemessen.
Ergibt deine Neuschätzung ohne UI und Beispiel etwas deutlich anderes, sag es
**vor** dem ersten Produktedit — dann ist es dieselbe Entscheidung, nur mit
besseren Zahlen. Danach führt eine zweite Überschreitung nach Vertrag zu
`reduce` oder `split`.

### Was ich nicht entschieden habe

Wo das neue UI-Ticket in der Prioritätskette landet, ist eine
Portfolio-Entscheidung und gehört Mike. Ein Split erzeugt keine neue Priorität:
T-30 bleibt an seiner Stelle in der Kette, das abgetrennte Ticket kommt ins
Board und wartet dort auf eine ausdrückliche Einordnung. Bitte lege es an und
verweise von T-30 darauf, ohne die Kette selbst zu ändern.

`review_round` bleibt 0 — es lag keine inhaltliche Review-Runde vor.
Der Entwurf selbst ist damit nicht abgenommen; ich habe ihn nur so weit
gelesen, wie es für Ziel, Breite und Schnittlinie nötig war.

### Review Runde 2 · Claude, 2026-09-08

`441b4b0` freigegeben. Negativer Alias-Mutant: 1 fehlgeschlagen/1129
bestanden; sauberer Backendlauf 1130 bestanden. Delta nur 17 Test- und
17 Ticketzeilen, Ruff und Bezeichnerinventar bestätigt. Der Gesamtbericht
steht im Git-Verlauf der STATUS-Mailbox. Mikes anschließender Auftrag zieht
die dynamische Exchanges-UI in T-64 vor T-21 #2g.
