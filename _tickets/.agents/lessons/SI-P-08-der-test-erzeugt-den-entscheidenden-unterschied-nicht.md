---
schema_version: 1
id: SI-P-08
project: stockinfo
kind: pattern
discovery_phase: mixed
affected_work:
- implementation
- tests
- handoff
subject_author: claude
discovered_by: unknown
recorded_by: unknown
structured_by: codex
prevention_roles:
- implementer
- reviewer
provenance:
  project: stockinfo
  file: _tickets/.agents/CLAUDE-LESSONS.md
  heading: P-08 · Der Test erzeugt den entscheidenden Unterschied nicht
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: f506fd721ef98bf9c51bff326b06c22a39c24eee57f14daa4e0e93f06bd78dff
  section_sha256: 34bc4fa45bea388ccfd0cfc765ca708bab2f30cef07c7d0e4a1d5c432a320602
  captured_at: '2026-09-11'
---

# SI-P-08 · Der Test erzeugt den entscheidenden Unterschied nicht

**Implementer-Regel:** Eingaben wählen, die die vermutete Fehlervariante sichtbar unterscheiden.

**Verifier-Prüfung:** Erwartung unabhängig bestimmen und den entscheidenden Unterschied nachweisen.

## Originalbelege und Einordnung

**Erkennungsregel:** Der Test soll zwei Implementierungen oder Zustände
unterscheiden, baut aber Eingaben auf, bei denen beide dieselbe Antwort geben.
Typische Formen sind eine Einerliste für eine Sortierregel, ein Aufruf unterhalb
der zu prüfenden Verdrahtung oder nur ein Zustand bei einem Cache-/Reload-Fehler.
Die Assertion kann dabei vollkommen richtig sein; wertlos ist der Aufbau.

**Prüffrage:** Welche zwei Zustände oder Implementierungen soll der Test
unterscheiden? Erzeugt sein Arrange-Schritt einen Fall, in dem deren Antworten
wirklich verschieden sind? Bei Zweifel denselben Test gegen einen minimalen
Mutanten der alten oder falschen Implementierung laufen lassen.

**Beleg 1:** T-22, erste Umsetzung von Verify #1: Der Reihenfolgetest verwendete
nur eine Quelle. Eine umgedrehte Einerliste ist dieselbe Liste; der Test konnte
eine ignorierte Reihenfolge nicht erkennen.

**Beleg 2:** T-22, nachgeschärfter Verdrahtungstest: Die erste Fassung rief
`_chain()` statt `_build_resolver()` auf. Sie prüfte damit eine Ebene unter der
Composition-Root und konnte eine dort verbliebene Verdrahtungsentscheidung
nicht erkennen.

**Beleg 3:** T-22 Runde 2, Commit `d5bb327`: Der HTTP-Test schrieb nur einen
Konfigurationsstand und rief danach `/sources` auf. Frisches Dateilesen und
gecacheter Laufzeitstand lieferten in diesem Aufbau dasselbe. Runde 3,
Commit `490314a`, erzeugt zuerst Laufzeit A, ändert danach die Datei auf B und
weist mit einem Frischlese-Mutanten nach, dass der Test nun unterscheidet.

**Beleg 4:** T-27a Runde 1, Commit `6121a94`: `DailyContract` prüfte
Sortierung, Schlusskurse und Zeitraum ausschließlich in Schleifen über
`answer.bars`; eine leere `DailySeries` bestand deshalb die vollständige Suite.
`MetadataContract` verwendete parallel `fetch(...) or []`, sodass selbst
`None` beim als bekannt deklarierten verantwortlichen Fall alle Feld-, Typ-,
Einheiten-, Plausibilitäts- und Herkunftsprüfungen übersprang. Die Testdaten
erzeugten keinen einzigen Wert, an dem die zugesagten Regeln hätten
unterscheiden können.

**Beleg 5:** T-27a Runde 2, Commit `db53189`: `ROLE_RESULTS` und seine Tests
erzeugten ausschließlich den Unterschied „bekannter Request, falscher
Treffertyp“. Für Miss-Erwartungen kehrte `_check_role_match()` vor der
Request-Prüfung zurück. Ein völlig unbekannter `object()`-Request mit
`expect=Unavailable` bestand deshalb Validierung und vollständigen Lauf: Der
`DirectRunner` erzeugte für den unbekannten Request genau das erwartete
`Unavailable`. Der neue Test unterschied die konkret besprochene Hit-Kombination,
nicht die behauptete allgemeine Rollenpassung.

**Beleg 6:** T-23 Runde 3, Commit `4e23cde`: Der Test „jede Rolle liefert dem
Core was er ruft“ prüfte nur `hasattr` auf fünf gebauten Objekten. Er erzeugte
weder einen aliaslosen US-Daily-Request noch eine Metadatenantwort mit einer
vom Core-Zielformat abweichenden Einheit. Beide Adapterfehler bestanden den
Test, weil der entscheidende Unterschied erst beim Methodenaufruf entsteht.

**Beleg 7:** T-23 Runde 4, Commit `adcb505`: Der Test „beide Namen erscheinen
in `/sources`“ konfigurierte nur `local-file`. Die zweite Assertion durfte
`canada-file` statt in der HTTP-Antwort alternativ in der internen Registry
finden. Der Arrange-Schritt erzeugte nie den behaupteten Zustand „beide Namen
im Endpunkt“, und die Assertion wechselte für den zweiten Namen die
Systemgrenze.

**Beleg 8:** T-46 Runde 1 (vor der Übergabe selbst gefunden): Das Pflichtorakel
„im Dateiprofil geht nichts ins Netz" hielt `socket.socket.connect` und
`socket.getaddrinfo` zu und prüfte zusätzlich die Quellennamen der Antwort.
Beide Hälften waren blind. `yfinance` 1.5.1 telefoniert über `curl_cffi`, also
über libcurl — die Python-`socket`-Sperre bewacht eine Leitung, die die Quelle
gar nicht benutzt. Und die Stufenliste entsteht aus der **konfigurierten**
Kette, ein Aufruf daneben bekommt keine Zeile. Ein Mutant mit
`yf.Ticker(...).history()` mitten in der Diagnose ließ das Orakel grün. Die
Lehre über den Einzelfall hinaus: **Eine Sperre prüft den Kanal, den sie
kennt.** Wo die Abstinenz von einer fremden Bibliothek abhängt, ist die
Abhängigkeit selbst das belastbarere Orakel — hier ein `ast`-Inventar aller
Importe des Moduls gegen eine aufgezählte Liste konkreter Quellen.

**Beleg 9:** T-46 Runde 1, Codex: Die Ersatzprüfung inventarisierte bei
`from … import …` nur den **Modulnamen**. Der Mutant
`from app.resolver import CompositeResolver, YahooSearchResolver` änderte die
gemessene Menge daher nicht: `app.resolver` war vorher schon erlaubt. Das
Mischmodul enthält aber neben dem Composite konkrete Online-Resolver und
importiert yfinance. Der zweite Versuch prüfte die richtige Idee eine Ebene zu
grob — ein Orakel über Importe muss bei Mischmodulen auch die importierten
Symbole unterscheiden.

**Beleg 10:** T-46 Runde 1, Codex: Der neue Test
`test_ein_quellenausfall_ist_kein_leeres_ergebnis` sagte in Name und Docstring,
`Unavailable` müsse von „leer" unterschieden werden, behauptete aber nur noch
`detail == "Unavailable"`. Der Produktcode klassifizierte denselben Wert als
`empty`; der Test blieb grün. Die alte Fassung hatte genau den entscheidenden
Unterschied (`status == "error"`) geprüft — bei der Neufassung wurde nicht nur
Code ersetzt, sondern unbemerkt das Orakel abgeschwächt.

**Beleg 11:** T-47 Runde 1a, Commit `c56c7b6`: Der Test
`test_zwei_sicherungen_kurz_nacheinander_kollidieren_nicht` rief `create()`
dreimal **nacheinander** auf und meldete damit die Abwesenheit von
Dateinamenskollisionen. FastAPI führt die synchronen POST-Handler jedoch
parallel aus. Ein Gegenlauf mit 20 gleichzeitigen `POST /backups` erhielt nur
siebenmal `201`; 13 Aufrufe wählten zwischen Existenzprüfung und
`VACUUM INTO` denselben Zielpfad und warfen einen SQLite-Fehler. „Kurz
nacheinander" erzeugte nicht den Zustand „gleichzeitig", den die
Kollisionsregel beherrschen muss.

**Beleg 12:** T-48 Runde 2, Commit `4186cc8`: Übergabe und Ticket erklärten,
eine fehlgeschlagene Dateisignatur blockiere die Erholung nicht. Der
Erholungstest schrieb aber eine Datei mit anderer Größe und Mtime. Der
entscheidende Zustand — gültige Wiederherstellung mit derselben
`(st_mtime_ns, size)`-Signatur — fehlte. Ein Gegenlauf stellte genau diesen
Stand her; `_reload()` kehrte vor dem Parser zurück und ließ die Quelle
dauerhaft gestört.

**Beleg 13:** T-48 Runde 3, Commit `08214cf`: Der neue Test unterschied die
abgelehnte Signatur vom geladenen Stand, der zweite Test stellte jedoch nur
den **identischen** geladenen Inhalt wieder her. Die Implementierung durfte
deshalb bei dessen Signatur `_problem` ungeprüft löschen. Eine gleich große
Preiskorrektur mit derselben Signatur meldete die Quelle ebenfalls gesund,
lieferte aber weiter den alten Katalogwert. Das Orakel musste Inhalt und
Erwartungswert ändern, nicht nur den Fehlerzustand zurücknehmen.

**Beleg 14 · Reviewerfehler:** T-50 Konzept Runde 2: Codex korrigierte den
vermuteten Aufnahmeweg auf die existierende Route `POST /instruments/intake`,
ohne die sichtbare Handlung bis zum Client zu verfolgen. Das UI-Feld benutzt
tatsächlich `useInstrumentActions.add` → `GET /quote…`; `intake` kommt im
Dashboard nicht vor. Die Route war real, aber der Browserfall hätte einen
anderen Weg vorbereitet als den geprüften. Bei UI-Abnahmen muss die Kette
**Interaktion → Composable → Request** inventarisiert werden, nicht nur ein
passender Backend-Endpunkt.

**Beleg 15:** T-50 Phase B, Commit `475e72a`: Der zweite UI-Test baute mit
`symbol: null as never` ein Instrument, das weder Pydantic- noch TypeScript-
Vertrag zulassen; eine ISIN-only-Anleihe trägt ihre ISIN im Stringfeld. Nur
dieser erfundene Zustand machte die neue Wächterzeile notwendig und rötete
ihren Mutanten. Gleichzeitig erklärte die Isolation sich für ✅, obwohl der
Vorher-/Nachher-Check nur `stockinfo.db`, nicht deren WAL/SHM erfasste; beide
Hilfsdateien trugen danach einen Zeitstempel aus dem Browserlauf. Ein Orakel
darf weder den Produktvertrag per `as never` umgehen noch Teile eines
mehrdateiligen Zustands auslassen.

**Beleg 16:** T-55 Runde 1, Commit `0bebb89`: Das nachgeschärfte
Isolationsskript erkannte korrekt, dass transiente WAL/SHM-Dateien über die
Verzeichnis-mtime sichtbar werden, maß diese mit `stat -f%m` aber nur in ganzen
Sekunden. Eine Datei anzulegen und sofort zu löschen ließ den Sekundenwert
gleich, während `st_mtime_ns` sich änderte. Genau der schnelle
Anlegen-/Löschen-Zyklus, den das Orakel unterscheiden soll, konnte daher weiter
grün bleiben. Die richtige Zustandsgröße allein genügt nicht; ihre Auflösung
muss den erzeugten Unterschied ebenfalls tragen.

**Beleg 17:** T-54 Runde 1, Commit `a2e65ad`: Der Test sollte beweisen, dass
die vom Benutzer genannte Börse die Resolverbörse überschreibt, und erzeugte
dafür absichtlich `XETR` gegen `XFRA`. Er prüfte aber nur
`identity.mic == "XETR"`; das parallele Antwortfeld `exchange` blieb
`"Frankfurt"`. Der entscheidende Unterschied war erzeugt, aber nur an einer
von zwei gemeinsam ausgegebenen Zustandsgrößen gemessen. Bei einer
Identitätsübernahme müssen kanonische Identität und die davon abgeleitete
Anzeige gemeinsam im Orakel stehen.

**Unmittelbare Wiederholung in T-54 Runde 2, Commit `ede5c3a`:** Die
Implementierung korrigierte beide Felder. Als Beleg wurde aber ein anderer
Test auf `Toronto` gezogen, bei dem Symbol und Resolver ohnehin dieselbe Börse
nannten. Der kontrastierende Fall `XETR` gegen `XFRA` prüfte weiter nur
`identity.mic`; `exchange` blieb ohne Assertion. Ein grüner Gleichheitsfall
ersetzt nicht den absichtlich erzeugten Unterschied des Orakels.
