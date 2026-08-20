# T-23 · Registry: Quellen werden geladen statt einkompiliert

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend) | offen | 1 Tag | Registry, zwei Ladewege, Isolation | — |

**Löst:** Der Schlussstein. Die App soll weltweit funktionieren, lässt sich hier
aber nur für wenige Märkte prüfen — allein die Auflösung eines kanadischen
Papiers hat am 2026-08-19 drei Anläufe gebraucht. Wer vor Ort sitzt, findet das
Problem in Minuten. Also muss die Lösung von außen kommen können.

**Hängt an:** T-20, T-21, T-22. Ohne sie wäre das Plugin-System eine Hülle: Ein
Plugin müsste Yahoo-Symbole verstehen, Yahoos Gattungsnamen kennen und mit `None`
drei Zustände ausdrücken.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | `examples/canada_file.py` nach `data/plugins/`, Neustart | erscheint in `GET /sources`, löst `CA…` auf | | |
| 2 | dasselbe als installiertes Paket (Entry-Point) | erscheint gleichwertig, ohne Datei im Volume | | |
| 3 | Plugin mit falscher `api_version` | wird abgelehnt, mit Meldung — App startet trotzdem | | |
| 4 | Plugin, das bei jedem Aufruf wirft | wird nach wiederholtem Fehler stillgelegt; App bleibt bedienbar | | |
| 5 | Plugin, das 60 s hängt | Schutzschalter verhindert **weitere** Aufrufe; der laufende wird **nicht** abgebrochen — Verhalten ist dokumentiert, nicht behauptet | | |
| 6 | `yfinance` und `justetf` in `GET /sources` | erscheinen als **normale Quellen**, nicht als Sonderfall | | |
| 7 | `make test` | Backend grün | | |

---

## Details

### Zwei Ladewege, eine Registry

**Entry-Points** (`importlib.metadata`) für Beigesteuertes — versioniert und
teilbar. Der Python-Standard; pytest und Airflow machen es so.

Installiert wird **nicht** über ein selbstgebautes Image, sondern über eine
Paketliste mit fester Version in `sources.yaml`; ein Launcher legt die Pakete
vor dem App-Start in eine hash-benannte Umgebung unter `/data` und hängt sie in
den Suchpfad. Das überlebt Image-Updates, weil nur `/data` beschrieben wird.
Einzelheiten und Sicherheitsregeln stehen im Design.

**Verzeichnis** (`data/plugins/*.py`) zum Ausprobieren und für lokale Anpassungen.
Ein Modul exportiert `SOURCES = [MeineQuelle]`.

Beide landen in derselben Registry; `sources.yaml` (T-22) bestimmt Auswahl und
Reihenfolge. Geladen wird **beim Start** — das genügt und ist auch, was Home
Assistant für Custom Components tut. Nachladen ohne Neustart kostet
Zustandsverwaltung für einen Gewinn, den man selten spürt.

### Isolation — die eine Stelle, an der fremdem Code misstraut wird

Jeder Aufruf gekapselt: Zeitgrenze, `except Exception` → als `Unavailable`
behandeln, nach wiederholtem Fehlschlag die Quelle stilllegen statt bei jedem
Abruf erneut zu hängen. Dafür gibt es genau **einen** Ort.

### Der erste Plugin-Autor ist die App selbst

`YFinanceResolver` und `JustEtfProvider` werden über denselben Weg geladen wie
ein fremdes Plugin — nicht als verdrahteter Sonderfall daneben. Nur so fällt auf,
wo der Vertrag zwickt, bevor es jemand anderes merkt.

### Sicherheit: bewusst, nicht beiläufig

Ein Python-Plugin läuft mit den Rechten der App. Das lässt sich nicht
wegargumentieren — wer selbst hostet, hat aber ohnehin ein Container-Image
installiert, dem er vertraut. Was die App schuldet: eine klare Ansage in der
Dokumentation und **keine Automatik, die von selbst etwas nachlädt**.

Einen risikoärmeren Nebenweg gibt es nicht: Der deklarative Ansatz wurde
gestrichen (siehe Design). Damit gilt diese Ansage für **jedes** Plugin.

---

## Auflösung

_(offen)_
