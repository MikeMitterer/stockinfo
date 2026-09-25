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
    path: data/meine-tabelle.yaml
```

Die Reihenfolge ist die Aussage und wird nicht umsortiert. `GET /sources` zeigt
danach, was tatsächlich gilt — einschließlich der Quellen, die **nicht**
arbeiten können und warum.

Zwei fertige Paare liegen unter [`examples/`](../examples/): je ein
Quellenprofil und die Fachdatei, auf die es zeigt —
`sources-fallback.yaml` mit `assets-fallback.yaml` für Online-Betrieb mit
Rückfall, `sources-standalone.yaml` mit `assets-standalone.yaml` für eine
Instanz ohne Netz.

Für den Wechsel zwischen diesen beiden Profilen im Docker-Container siehe
[Docker](../README.md#docker) und [Unraid](../README.md#unraid). Der Pfad für
`make up` ist ein benanntes Volume; Unraid verwendet ein Host-Verzeichnis.

**Eine Quelle darf in mehreren Rollen stehen.** Das mitgelieferte `yaml-file`
tut genau das: Es liest eine Datei und bedient daraus Auflösung, Kurs,
Historie, Metadaten und Devisen.

**Jede Rolle hat eine Rangfolge.** Alle fünf fragen die Kette der Reihe nach,
und die erste belastbare Antwort gilt. Wer keine hat, reicht weiter:

```yaml
quotes: [yfinance, yaml-file]
```

Das ist ein Rückfall und liest sich auch so: Online gewinnt, wo es einen Kurs
gibt; die gepflegte Datei springt nur dort ein, wo keiner kommt — bei einer
Anleihe etwa, die online kein Papier mit Kurs ist.

Drei Feinheiten, die man beim Eintragen kennen sollte:

- **Die Datei gehört auch in `resolvers`**, sonst hilft sie beim Kurs nicht.
  Ein Papier, das keine Online-Quelle kennt, lässt sich ohne sie gar nicht
  erst aufnehmen — die Aufnahme scheitert an der Auflösung, lange bevor
  jemand nach einem Kurs fragt. Für eine Anleihe, die nur in der eigenen
  Datei steht, lautet die Kette also `resolvers: [openfigi, yahoo-search,
  yaml-file]`.
- Bei `daily` ist eine **leere** Tagesreihe eine Antwort — „nachgesehen, in
  diesem Zeitraum nichts" — und beendet die Kette. Nur „konnte nicht
  nachsehen" fällt weiter.
- `GET /fx` nennt die Quelle, die den Kurs **geliefert** hat, nicht die, die
  vorne steht.

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

## Datenversion und Migration beim Start

Ein Paketupdate allein verändert den Datenbestand nicht. Erhöht ein aktives
Plugin seine `data_version`, sichert StockInfo den alten Bestand und ruft die
Migrationsfunktion des Autors auf. Datenänderungen und neue Version werden je
Plugin gemeinsam gespeichert. Nach einem Fehler oder Prozessabbruch bleibt die
fehlgeschlagene Umwandlung ungespeichert; erfolgreiche frühere Schritte werden
beim nächsten Start nicht wiederholt. Neue Datenbanken übernehmen die aktuelle
Version ohne Migration, fehlende Einträge im Altbestand gelten als Version 1.

Fehlt eine Funktion, scheitert die Sicherung/Umwandlung oder liegt ein Downgrade
vor, bleiben Fachrequests und Hintergrundaktualisierung gesperrt. `/ready` und
`/operational` melden `degraded`; das Serverlog nennt Plugin, Ausgangs- und
Zielversion sowie den Fehler. Während des Anlaufs melden Fachrequests dagegen
`503` mit `startup_running`; erst ein gescheiterter Start liefert
`startup_failed`. Der Link auf `/migration` gehört nur zur noch ausstehenden
Identitätsbestätigung. Prüfe den Fehlerhinweis und korrigiere das Plugin,
bevor du neu startest. Eine offene Bestätigung der Identitätsmigration hat
Vorrang. Es gibt keinen zusätzlichen Migrationsdialog.

Der [Autorenvertrag](plugin-authors.md#plugin-data-migrations) beschreibt den
Kontext und ein ausführbares Beispiel. Die vorhandene Sicherungsfunktion wird
wiederverwendet; StockInfo führt keine automatische Datenbankrotation aus.

## Wer selbst eine Quelle schreibt

Ab hier ist die Anleitung **englisch** und steht in
[`docs/plugin-authors.md`](plugin-authors.md): Identitätsformen,
Pflichtfelder, die vier Arten „nein" zu sagen, das kleinste installierbare
Paket, das geerbte Testkit und die Stolperstellen.

Sie ist englisch, weil ihre Leser es sind — ein Plugin für den brasilianischen
oder japanischen Markt schreibt niemand, der dieses Repository auf Deutsch
liest. Und sie steht **einmal**: Zwei Anleitungen zu derselben Sache laufen
beim ersten Nachtrag auseinander, und dann ist die falsche die, die jemand
zufällig zuerst findet.

Ein vollständiges, baubares Beispielpaket liegt daneben in
[`plugin_api/examples/us-example/`](../plugin_api/examples/us-example/); das
mitgelieferte `yaml-file` in
[`plugin_api/examples/yaml_file.py`](../plugin_api/examples/yaml_file.py)
zeigt eine Quelle in allen fünf Rollen.
