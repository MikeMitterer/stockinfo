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

Der Umfang ist **entschieden, der Entwurf wird vorbereitet**. Bestehende Symbole
werden durch dieses Ticket weder umdefiniert noch migriert.

## Für dich

Aktuell ist **kein Handgriff nötig**.

Codex führt das Ticket als nächstes Element der beauftragten Kette aus.
Der Entwurf geht wegen der erwarteten Breite vor Produktcode an Claude.

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
3. Exchanges-UI und ausführbares Autorenbeispiel samt gezielten Tests.

Der [Entwurf](../docs/superpowers/specs/2026-09-08-plugin-exchanges-design.md)
legt Vertragsform, Lebenszyklus, Grenzen und Akzeptanzfälle fest. Die
Schätzung von 16–20 Produktdateien, 8–10 Test-/Dokumentationsdateien und
1400–1800 manuellen Diff-Zeilen überschreitet den allgemeinen 800-Zeilen-
Riegel. Deshalb zunächst Scope-Checkpoint, keine Produktimplementierung.
Keine Migration, keine Alias-Überschreibung, kein ISO-Vollimport und kein
neues Test-Subsystem. Der bestehende UI-Entwurf vom Vortag bleibt unberührt.

### Verbindlicher Umfang

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

Heute nur Ticketänderung. Offen für Entwurf und Implementierung im oben
vereinbarten Umfang. Keine Änderung an Rollen oder Prioritätskette.

## Frühere Fassung · Historie

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
