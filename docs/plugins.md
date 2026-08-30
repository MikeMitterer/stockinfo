# Eigene Datenquellen — zwei Wege hinein

StockInfo lässt sich weltweit betreiben, aber hier nur für wenige Märkte
prüfen. Wer vor Ort sitzt, findet ein Problem mit seinem Markt in Minuten —
deshalb muss die Lösung von außen kommen können, ohne dass jemand dieses
Repository anfasst.

Es gibt zwei Wege, und beide landen in derselben Registry.

## 1. Eine Datei im Datenvolume — zum Ausprobieren

Lege eine `*.py` in `data/plugins/` und exportiere `SOURCES`:

```python
# data/plugins/meine_quelle.py
from stockinfo_plugin import (
    ListedIdentity,
    NotFound,
    Resolved,
    ResolveRequest,
    Resolver,
)


class MeinResolver(Resolver):
    name = "meine-quelle"
    # Jede Quelle nennt die Vertragsversion **selbst**. Erben genügt nicht:
    # Der Loader weist eine Quelle ohne eigene Deklaration ab.
    api_version = 2
    # Was die Quelle bedient. Eine **leere** Menge heißt „nichts zugesagt",
    # nicht „alles" — der Host überspringt sie dann für jede bekannte Gattung.
    SUPPORTED_KINDS = frozenset({"listed"})
    SUPPORTED_TYPES = frozenset({"stock"})

    def handles(self, request: ResolveRequest) -> bool:
        return bool(request.isin and request.isin.startswith("CA"))

    def resolve(self, request: ResolveRequest):
        return Resolved(
            identity=ListedIdentity(ticker="RY", mic="XTSE", isin=request.isin),
            name="Royal Bank of Canada",
            instrument_type="stock",
        )


SOURCES = [MeinResolver]
```

Nach einem Neustart steht `meine-quelle` in `GET /sources` und lässt sich in
`sources.yaml` in eine Kette eintragen.

Dateien mit führendem `_` werden übersprungen — so bleiben Hilfsmodule und
Editor-Reste außen vor.

## 2. Ein installiertes Paket — zum Weitergeben

Ein Paket meldet seine Quellen als Entry-Point an:

```toml
# pyproject.toml des Plugin-Pakets
[project.entry-points."stockinfo.sources"]
meine-quelle = "meinpaket.quellen:MeinResolver"
```

Eingetragen wird es in `data/sources.yaml`, mit **fester Version**:

```yaml
plugins:
  packages:
    - stockinfo-plugin-meinemarkt==1.2.3
```

Beim Start installiert die App die Liste nach `data/plugin-env/<hash>` und hängt
das Verzeichnis in den Suchpfad; danach findet `importlib.metadata` die Gruppe
`stockinfo.sources`.

**Warum nicht einfach `pip install`?** Beim offiziellen Container liegt
`site-packages` im **Image** und ist nach dem nächsten `docker pull` wieder
weg. `/data` ist das Volume und überlebt das Update.

Drei Regeln gelten dabei:

* **Feste Version.** Der Ordnername ist eine Prüfsumme über die Liste — ohne
  `==` zeigte derselbe Hash morgen auf ein anderes Paket. Alles andere
  (`>=`, ein nackter Name, eine Git-URL, eine pip-Option) wird abgewiesen und
  benannt.
* **Nur Wheels.** Sonst müssten Build-Werkzeuge ins Image, und ein `setup.py`
  liefe beim Start als Code.
* **Der Vertrag bleibt der der App.** Eine Constraint verhindert, dass ein
  Plugin eine andere Fassung von `stockinfo-plugin-api` in den Ordner zieht —
  sie stünde vorn im Suchpfad und gewänne.

Dieselbe Liste ⇒ derselbe Ordner ⇒ **keine Installation** beim nächsten Start.
Eine geänderte Liste ergibt einen neuen Ordner; der alte bleibt liegen, und ein
Zurückrollen ist damit ein Zeileneditat.

> **Es gibt bewusst keine Automatik, die etwas nachlädt.** Ein Plugin läuft mit
> den Rechten der App; was installiert wird, entscheidet der Betreiber
> ausdrücklich und nicht eine Konfigurationsdatei im Hintergrund. Wer selbst
> hostet, hat ohnehin ein Container-Image installiert, dem er vertraut — diese
> Entscheidung soll bewusst bleiben und nicht beiläufig passieren.

## Auswählen: `sources.yaml`

Geladen heißt **nicht** benutzt. Welche Quelle in welcher Rolle und in welcher
Rangfolge gefragt wird, sagt allein `data/sources.yaml`:

```yaml
resolvers: [meine-quelle, openfigi, yahoo-search]
quotes:    [yfinance]

providers:
  meine-quelle:
    path: data/meine-tabelle.csv
```

Die Reihenfolge ist die Aussage und wird nicht umsortiert. `GET /sources` zeigt
danach, was tatsächlich gilt — einschließlich der Quellen, die **nicht**
arbeiten können und warum.

## Was die App mit einem fremden Plugin macht

| Lage | Verhalten |
|---|---|
| Import wirft | gemeldet, übersprungen — die App startet |
| falsche `api_version` | gemeldet, übersprungen |
| Konstruktor wirft | gemeldet, die Quelle fällt aus der Kette |
| `configuration_problem()` spricht | die Quelle fällt aus der Kette, `GET /sources` nennt sie als nicht einsatzbereit |
| eine Methode wirft | wird zu `Unavailable`; nach drei Fehlschlägen in Folge wird die Quelle fünf Minuten stillgelegt |
| Name kollidiert mit einer eingebauten Quelle | abgelehnt — sonst ließen sich die Kurse der App still umleiten |

**Eine Grenze, die es nicht gibt:** einen hängenden Aufruf abbrechen. Für
synchronen Python-Code im selben Prozess gibt es keine harte Zeitgrenze; ein
Timeout ließe den Aufrufer zurückkehren, der Thread liefe weiter. Zeitgrenzen
setzt deshalb das Plugin bei seinen eigenen I/O-Aufrufen — der Vertrag verlangt
es, erzwingen kann er es nicht.

## Was eine Auflösung tragen muss

Drei Felder, alle Pflicht — und keines hat einen Vorgabewert:

| Feld | Bedeutung |
|---|---|
| `identity` | Die Identität in ihrer Form: `ListedIdentity` (Ticker + MIC), `PairIdentity` (Basiswert + Quote-Währung, für natives Krypto) oder `IsinOnlyIdentity` (die ISIN selbst, für OTC-Anleihen). |
| `name` | Der Anzeigename des Papiers. |
| `instrument_type` | Die Gattung: `stock`, `etf`, `etc`, `fund`, `crypto`, `bond`. Die Aufzählung ist **offen** — ein neuer Wert ist ein Nachtrag und kein Bruch. |

**Wer eines davon nicht kennt, antwortet `NotFound`.** Das ist keine Härte,
sondern die einzige ehrliche Antwort: „Ich habe einen Ticker, weiß aber nicht,
was das Papier ist" ist keine brauchbare Auflösung. Eine spätere Quelle in der
Kette darf es besser wissen — eine halbe Antwort nimmt ihr diese Gelegenheit,
weil die Kette beim ersten Treffer aufhört.

Der Anlass ist gemessen und nicht theoretisch: Bis August 2026 waren `name` und
`instrument_type` optional. Quellen ließen sie leer, die App nahm es an,
speicherte es und zeigte leere Felder — und weil die Gattung fehlte, wurde die
Metadatenquelle **gar nicht erst** befragt. Ohne Meldung, ohne
Protokolleintrag, monatelang.

Ein leerer String zählt dabei nicht als Wert. Der Host prüft nicht nur, ob das
Feld da ist, sondern ob etwas darin steht; `stockinfo_plugin.invariants.
resolution_problem` ist dieselbe Funktion, die auch das Testkit benutzt — wer
mag, ruft sie vor dem Antworten selbst.

Für die anderen Rollen gilt dasselbe Prinzip an anderen Feldern: Ein `Quote`
trägt Preis, Währung und Zeitpunkt mit Zone, alle drei ohne Vorgabewert. Was
eine Rolle verlangt, steht maschinenlesbar unter `GET /fields` im Abschnitt
`plugin_contract`.

## Den Vertrag selbst

`stockinfo-plugin-api` ist ein eigenständiges Paket mit fünf Rollen
(`Resolver`, `MetadataSource`, `QuoteSource`, `DailyCloseSource`, `FxSource`),
fachlichen Invarianten und einem Testkit. Ein Plugin erbt die Vertragssuite
seiner Rolle, statt eigene Prüfungen zu schreiben:

```python
from stockinfo_plugin.testing import ResolverContract


class TestMeinResolver(ResolverContract):
    responsible = ResolveRequest(isin="CA78012H5675")
    not_responsible = ResolveRequest(symbol="AAPL")
    unknown = ResolveRequest(isin="CA0679011084")

    def make_source(self):
        return MeinResolver()
```

Beispiele liegen in `plugin_api/examples/` — sie werden als
`stockinfo_plugin_examples` mitinstalliert und lassen sich direkt importieren.
