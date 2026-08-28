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
from stockinfo_plugin import NotFound, Resolved, ResolveRequest, Resolver


class MeinResolver(Resolver):
    name = "meine-quelle"

    def handles(self, request: ResolveRequest) -> bool:
        return bool(request.isin and request.isin.startswith("CA"))

    def resolve(self, request: ResolveRequest):
        return Resolved(ticker="RY", mic="XTSE", isin=request.isin)


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

Installiert wird es **wie jedes andere Python-Paket** in die Umgebung, in der
StockInfo läuft:

```
pip install stockinfo-plugin-meinemarkt
```

Mehr ist es nicht. Die App sucht beim Start mit `importlib.metadata` nach der
Gruppe `stockinfo.sources` und findet, was installiert ist.

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
