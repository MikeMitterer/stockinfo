# T-34 · Zusage gegen Laufzeit — Wächter statt Review

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Tests + Vertragsartefakt) | offen | 1 Tag [^box] | drei Wächter zwischen Vertrag, Fixtures und laufendem Dienst | — |

- **Angelegt:** 2026-08-27, aus T-21 Übergabe 3 und 4 (Runden 39–49)
- **Hängt ab von:** nichts. Übergabe 4B baut den dritten der drei Wächter
  ohnehin; die anderen beiden sind unabhängig
- **Einordnung:** eigenständiges, von Mike beauftragtes Ticket
- **Entscheidung Mike, 2026-08-27:** ausdrücklich beauftragt, nachdem die
  Runden 39–49 dreimal denselben Befundtyp gebracht haben

[^box]: **Die Schätzung ist mit Vorsicht zu lesen.** T-21 stand mit „1 Tag" im
    Kopf und hat vier Tage und 42 Runden gebraucht. Der Unterschied hier: Der
    Umfang ist geschlossen — drei Wächter über bestehende Artefakte, kein
    neuer Vertrag, kein Schema, keine Oberfläche. Wächst er, ist das der
    Hinweis, dass ein vierter Wächter gefunden wurde, und der gehört in eine
    eigene Zeile statt in dieselbe Übergabe.

## Worum es geht

Der Core hat einen geschriebenen Vertrag (`contract/core-contract.json`),
zwölf Fixtures für fremde Konsumenten und einen laufenden Dienst. **Zwischen
den dreien prüft heute nur ein Mensch.**

Das ist gemessen, nicht vermutet: Die Runden 39 bis 49 haben **dreimal**
denselben Befundtyp gebracht, und jedes Mal hat Codex ihn gefunden, nicht ein
Test.

| Runde | Zusage | Laufzeit | Gefunden von |
|---|---|---|---|
| 39 | Artefakt: `quote.ticker`/`mic` sind Pflicht | OpenAPI führte beide als optional **und** nullable | Codex |
| 44/45 | Artefakt: `identity.ambiguous_symbol_status: 409`, seit T-24 abgenommen | An **keinem** Endpunkt umgesetzt; der Lookup traf still die ältere Zeile | Codex |
| 45 | Fixture `quote-409-ambiguous-symbol.json` | Zeigte zwei Kandidaten mit **derselben** ISIN — ein Zustand, den `isin UNIQUE` verbietet | Claude, beim Nachstellen |

Der zweite Fall ist der teuerste: Die Zusage stand seit T-24 im abgenommenen
Vertrag. Zwischen Abnahme und Fund lagen mehr als zwanzig Runden, in denen
jeder Beteiligte davon ausging, sie sei eingelöst — und in Runde 44 habe ich
sie sogar still nach „noch nicht umgesetzt" zurückgestuft, statt sie zu bauen.

**Der gemeinsame Nenner:** Eine Zusage ist ein Satz in einer JSON-Datei. Ob
ihr etwas entspricht, weiß nur, wer beides nebeneinanderlegt. Das ist
Reviewarbeit, die ein Test übernehmen kann.

## Verify-Matrix

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `contract/core-contract.json`, jede Verhaltenszusage | jede trägt **entweder** einen Test, der sie am laufenden Dienst ausführt, **oder** einen Eintrag unter `planned`. Ein dritter Zustand — zugesagt, ungeprüft, nicht als geplant markiert — ist rot | | |
| 1b | derselbe Wächter, Mutationsprobe | eine Zusage aus `planned` entfernen, ohne sie umzusetzen → **rot**. Ohne diese Probe prüft der Test nur, dass die Datei lesbar ist | | |
| 2 | `contract/fixtures/`, **alle zwölf** | jede Fixture wird gegen den **laufenden Dienst** gehalten, nicht nur gegen das Artefakt. Heute prüft `test_contract.py` Endpunkt, Modellschema und Header — aber nie, ob der Dienst diesen Rumpf tatsächlich liefert | | |
| 2b | dieselbe Prüfung, Mutationsprobe | ein Feld in einer Fixture ändern → rot; und eine Fixture, deren Zustand das Schema **verbietet** (zwei Zeilen mit derselben ISIN), fällt beim Aufbau auf statt beim Lesen | | |
| 2c | vertragswidrige Fixtures | die Negativfälle bleiben ausgenommen und sind ausdrücklich als solche erkannt — sie beschreiben, was der Dienst **nicht** tut | | |
| 3 | Fehlerkennungen gegen die Sprachkataloge | jede im Backend erzeugte Kennung hat DE **und** EN, kein leerer Text, keine Karteileiche im Katalog | ➖ [^a] | |
| 4 | `make test` | die drei Wächter laufen im normalen Lauf mit, nicht in einem eigenen Ziel, das niemand aufruft | | |

[^a]: **Wird in T-21 Übergabe 4B gebaut**, samt Inventar per `ast` und
    dreifacher Mutationsprobe. Steht hier nur, damit die Sammlung
    vollständig ist — nicht, um ihn ein zweites Mal zu bauen. Ist 4B
    freigegeben, wird die Zeile von dort übernommen.

## Die drei Wächter

### 1 · Jede Zusage hat einen Beleg oder ein `planned`

Das Artefakt trennt heute schon zwischen zugesagt und geplant: `planned`
enthält `details_container` (T-26) und `generation_runtime` (T-25), jeweils mit
Ticket und Wirkung. Das ist der richtige Mechanismus — er wird nur nicht
erzwungen.

`identity.ambiguous_symbol_status: 409` stand **ohne** `planned`-Eintrag im
Vertrag und war trotzdem nirgends gebaut. Genau diese Lücke schließt der
Wächter: Für jede Verhaltenszusage muss es einen Test geben, der sie ausführt,
oder einen Eintrag, der sagt „kommt noch, mit diesem Ticket".

**Die Zuordnung Zusage → Test darf keine Handliste werden.** Der Weg dahin ist
Teil dieses Tickets und nicht vorentschieden; die naheliegende Form ist eine
Markierung am Test selbst (etwa ein `pytest`-Marker mit dem Vertragsschlüssel),
sodass das Artefakt die Wahrheit bleibt und der Test sich zu ihr bekennt.

### 2 · Jede Fixture ist das, was der Dienst wirklich sagt

`contract/README.md` sagt Konsumenten zu, dass sie die Fixtures benutzen
können, **ohne StockInfo zu starten**. Genau deshalb muss jemand sie starten
und vergleichen — sonst beschreiben sie irgendwann einen Dienst, den es nicht
gibt.

Für `quote-409-ambiguous-symbol.json` steht dieser Test seit Runde 45
(`test_die_fixture_zeigt_was_der_dienst_wirklich_antwortet`). Er ist die
Vorlage; hier wird er auf die übrigen elf ausgedehnt.

**Der Aufbau ist der schwierige Teil, nicht der Vergleich.** Jede Fixture
braucht einen Bestand, aus dem ihr Rumpf entsteht. Wo der über die echte Kette
nicht herstellbar ist, ist das ein Befund über die Fixture — so wie die
zwei Kandidaten mit derselben ISIN, die es nach `one_active_listing_per_isin`
gar nicht geben kann.

### 3 · Jede Kennung hat zwei Übersetzungen

Baut Übergabe 4B. Hier nur als Teil der Sammlung geführt.

## Was bewusst nicht gebaut wird

* **Ein Wächter über die Prosa.** `docs/rest-core-contract.md` erklärt, das
  Artefakt sagt zu. Sätze gegen Code zu prüfen führt zu einem Test, der
  Formulierungen einfriert.
* **Ein Generator, der den Vertrag aus dem Code ableitet.** Dann wäre der
  Vertrag keine Zusage mehr, sondern eine Beschreibung — und jede
  Vertragsverletzung würde per Definition wegdefiniert.
* **Rückwirkende Prüfung abgenommener Tickets.** Der Wächter greift ab jetzt.
  Was er beim ersten Lauf an Altlast findet, wird gesichtet und einzeln
  entschieden, nicht als Sammelbefund abgearbeitet.

## Warum das ein eigenes Ticket ist

Es ist kein Teil von T-21. T-21 zieht eine Identitätsgrenze; diese Wächter
sind Werkzeug für **jedes** Ticket, das eine Zusage macht — T-25 mit
`/generation`, T-26 mit dem `details`-Container, T-30 mit den
Plugin-Deklarationen. Sie in T-21 zu bauen hieße, sie dort zu verstecken, wo
das nächste Ticket sie nicht sucht.

Der erwartete Nutzen ist der Grund für den Auftrag: Der Befundtyp, den die
drei Wächter abfangen, hat in T-21 allein geschätzt ein halbes Dutzend Runden
gekostet — bei mindestens fünf Tickets, die noch Zusagen machen werden.
