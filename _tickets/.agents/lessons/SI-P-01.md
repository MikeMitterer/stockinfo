---
schema_version: 1
id: SI-P-01
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
  heading: P-01 · Testtiefe wird in der Übergabe überzeichnet
  revision: 5fc549b84ae7d449780b856d3046230da6c5bf2d
  file_sha256: f506fd721ef98bf9c51bff326b06c22a39c24eee57f14daa4e0e93f06bd78dff
  section_sha256: f844fa7dfe12b42bf4a028fae64f9e7185316105e9988841b7b9df6e91017b69
  captured_at: '2026-09-11'
---

# SI-P-01 · Testtiefe wird in der Übergabe überzeichnet

**Implementer-Regel:** Tatsächlich durchlaufene Kette und ersetzte Komponenten benennen.

**Verifier-Prüfung:** Vom Testeinstieg bis zum Ergebnis verfolgen, welche eigenen Komponenten wirklich laufen.

## Originalbelege und Einordnung

**Erkennungsregel:** Die Übergabe behauptet „ganze Kette", „nur externe Grenze
gemockt" oder gleichwertig, während eine eigene Kernkomponente durch Fake,
Stub oder Mock ersetzt ist.

**Prüffrage:** Welche konkrete Objektkette läuft im Test? Jeden Test-Doppel als
externe Grenze oder eigene Komponente klassifizieren und die Behauptung damit
abgleichen.

**Beleg:** T-17 Runde 1, Commit `84c9c2d`: In
`tests/test_resolver.py` ersetzte `CountingResolver` den eigenen
`YFinanceResolver`, obwohl Übergabe und Docstring behaupteten, allein
`httpx.post` sei gemockt und die ganze Kette werde geprüft.

**Beleg:** T-21 Teil 1, Commit `fce1bab`: Verify `#1` markierte die Migration
einer bestehenden Datenbank mit `✅` als live geprüft. Ticketfußnote und
Übergabe hielten zugleich fest, dass nur eine synthetisch nachgestellte
Alt-Datenbank und kein real gewachsener Bestand geprüft worden war.

**Neuer Beleg wegen ausdrücklich falscher Testtiefenbehauptung:** T-21 Teil 3
Übergabe 2A, Runde 30, Commit `d361fbc`: Ticketfußnote und Test-Docstring
erklärten, `test_die_bestaetigung_startet_den_scheduler` prüfe, dass der
Scheduler anlaufe. Der Test ersetzt den registrierten Produkt-Callback jedoch
durch `lambda: gestartet.append("scheduler")`; weder `RefreshScheduler` noch
sein `start()` laufen. Geprüft ist nur, dass irgendein Callback aufgerufen
wird — und auch das vor statt nach der Migration.

**Neuer Beleg:** T-22 Runde 1, Commit `20af8fa`: Smoke und Übergabe erklärten,
über echte Neustarts werde geprüft, „welche Kette entsteht“. Der Smoke las
jedoch ausschließlich `/sources`; die Verdrahtung lief nur in einem getrennten
Unit-Test. Weil der Endpunkt die Datei frisch las, die Services aber eine
gecachete Konfiguration hielten, konnte die laufende Kette `OpenFigiResolver`
sein und `/sources` zugleich `yahoo-search` melden. Beide Tests blieben grün,
weil keiner die beiden Seiten in derselben gestarteten App verglich.

**Neuer Beleg:** T-22 Runde 2, Commit `d5bb327`: Die Übergabe erklärte, die
Korrektur habe für beide Hälften eigene Tests und der HTTP-Test prüfe denselben
Stand wie die laufenden Dienste. Der benannte Test schrieb jedoch nur eine
Konfiguration, leerte den Cache und rief danach `/sources` auf. Er primte keine
Laufzeitkette und änderte die Datei nicht anschließend; eine Rückkehr zum
frischen Dateilesen im Endpunkt wäre deshalb unentdeckt grün geblieben.

**Neuer Beleg:** T-23 Runde 1, Commit `e6ca003`: Die Übergabe erklärte, zwei
Plugins beantworteten dieselbe Rolle und ausschließlich `sources.yaml` wähle
zwischen ihnen. Der benannte Test verlangte jedoch ausdrücklich
`not isinstance(chain[0], YFinancePlugin)` und baute für `yfinance` weiter den
alten nativen `YFinanceProvider`. Das Datei-Plugin wurde nur direkt unterhalb
des Core aufgerufen; Registry → Core → REST blieb ungetestet und laut OUTBOX
noch offen.

**Neuer Beleg:** T-23 Runde 3, Commit `4e23cde`: Der neue Rollentest wurde als
Nachweis beschrieben, dass alle fünf Rollen dem Core nun das von ihm
aufgerufene Objekt liefern. Er prüfte jedoch ausschließlich `hasattr` auf dem
Ergebnis von `build_chain`. Der echte Daily-Aufruf mit `AAPL/XNAS` endete vor
dem Provider mit `None`, und der Metadatenaufruf übernahm eine Ratio-TER ohne
Umrechnung und verlor ihre Herkunft. Vorhandensein einer Methode war keine
Ausführung der behaupteten Core-Grenze.

**Neuer Beleg:** T-23 Runde 4, Commit `adcb505`: OUTBOX und Test-Docstring
erklärten, beide Loader-Namen würden in `GET /sources` geprüft. Der Test
konfigurierte dort jedoch nur `local-file`; für `canada-file` akzeptierte die
Assertion alternativ dessen bloßes Vorkommen in `specs_by_name()`. Damit war
der Test grün, obwohl der zweite Name in der HTTP-Antwort fehlen durfte.

**Neuer Beleg:** T-23 Runde 5, Commit `d4f9036`: OUTBOX erklärte, beide
Metadatenfälle liefen durch `CompositeEtfEnricher → Adapter → Plugin` und
`close()` werde je Objekt genau einmal gerufen. Im Produktcommit wurde jedoch
kein Test für einen dieser Wege ergänzt; der Test-Diff betraf Installer,
Parser, einen Diagnosefall nach vorherigem Bau und die zwei Namen in
`/sources`. Claudes eigene Fehleranalyse („kein Test lief durch
`CompositeEtfEnricher`“) blieb damit auch nach der Reparatur ohne dauerhafte
Gegenprobe.

**Neuer Beleg:** T-37, Commit `d313318`: Ticket und OUTBOX meldeten dieselbe
Prüfstrecke für ein CSV-Profil mit Quellen in allen fünf Rollen. Der Smoke
prüfte die fünf Namen jedoch nur über `/sources`; seine 17 fachlichen Checks
riefen Resolver, Quote und Metadaten auf, aber weder `/quote/{isin}/daily`
noch `/fx`. Konfiguration war damit für Ausführung eingetreten, obwohl die
beiden Rollen den Core in diesem Lauf nie berührten.

**Neuer Beleg:** T-31 Runde 5, Commit `1133dd9`: Übergabe und Test-Docstring
meldeten für `BTC-EUR` die „echte Kette; nur Außengrenzen ersetzt". Der Test
injizierte mit `_TypingResolver` jedoch direkt einen eigenen Kern-Resolver und
umging damit Registry, `ResolverAdapter` und `YahooSearchResolverPlugin`. Die
reale Online-Quelle akzeptierte weder Symbol-Requests noch `crypto`; der
behauptete Produktweg blieb trotz grünem Orakel unberührt.

**Neuer Beleg:** T-47 Teilstrecke 1b, Commit `0e6ca65`: Die Übergabe erklärte
Restore und Sicherheitskopie über zwei echte Prozesse für bestätigt. Der
Aufbau besaß nur eine Sicherung und berührte damit die gekoppelte
Zehnerrotation nicht. Mit zehn Sicherungen löschte das Sicherheitsbackup die
ausgewählte älteste Restore-Datei vor dem Einspielen; alle 37 Backup-Tests
blieben grün.

**Neuer Beleg:** T-47 Teilstrecke 1b Runde 2, Commit `a904d42`: Der Test
`test_ein_erzwungener_fremder_restore_ist_in_sources_sichtbar` trug den
gesamten Nutzerweg im Namen, schrieb den fremden Fingerprint aber direkt per
SQL und rief danach nur `/sources` auf. Request mit `force`, Pending-Datei und
Starttausch durften vollständig fehlen, ohne dass das Orakel rot wurde.

**Neuer Beleg:** T-51 Runde 1, Commit `7b8d3bc`: Komponenten- und Browsertest
belegten den Backup-Klick, aber kein dauerhafter Test verband das sichtbare
`MigrationGate` mit `AppGate` und dessen Backup-Composable. Nach Entfernen von
`@backup="backup"` blieb die gesamte Suite mit 318 Dashboardtests grün. Erst
der vertikale AppGate-Test in `5c4afc8` ließ genau diesen Mutanten rot werden.
