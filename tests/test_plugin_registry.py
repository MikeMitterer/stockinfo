"""Zwei Ladewege, eine Registry — und was passiert, wenn ein Plugin kaputt ist.

Die Leitregel dieses Moduls steht in jedem zweiten Test: **Ein Fehler in einem
Plugin darf die App nicht am Starten hindern.** Wer eine Quelle kaputt macht,
verliert diese Quelle, nicht seine Installation. Deshalb prüfen die Tests unten
nicht nur, dass etwas fehlschlägt, sondern dass die **übrigen** Quellen
trotzdem ankommen.
"""

import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from stockinfo_plugin import (
    ListedIdentity,
    NotFound,
    Resolution,
    Resolved,
    ResolveRequest,
    Unavailable,
)
from stockinfo_plugin.sources import FxSource, QuoteSource, Resolver

from app.plugin_guard import CircuitBreaker, GuardedSource
from app.plugin_loader import (
    ENTRY_POINT_GROUP,
    load_all,
    load_directory_sources,
    load_entry_point_sources,
    roles_of,
    spec_from_class,
)
from app.sources_registry import BUILTIN_SOURCES, register_loaded, specs_by_name


class DemoResolver(Resolver):
    """Eine minimale Quelle, wie ein Beiträger sie schriebe."""
    api_version = 2

    name = "demo"

    def handles(self, request: ResolveRequest) -> bool:
        return bool(request.isin)

    def resolve(self, request: ResolveRequest) -> Resolution:
        return Resolved(
            ListedIdentity(ticker="DEMO", mic="XTSE", isin=request.isin),
            name="Demo",
            instrument_type="stock",
        )


class TwoRoleSource(Resolver, QuoteSource):
    """Eine Quelle, die zwei Fragen beantwortet."""
    api_version = 2

    name = "zweirollig"


class WrongVersion(Resolver):
    """Gegen einen anderen Vertrag gebaut."""

    name = "veraltet"
    api_version = 99


class Nameless(Resolver):
    """Ohne Namen — unter welchem Schlüssel sollte sie in `sources.yaml` stehen?"""
    api_version = 2


class NoRole(Resolver):
    """Erbt zwar `Resolver`, aber der Test unten prüft die Ableitung selbst."""
    api_version = 2

    name = "rollenlos"


@pytest.fixture(autouse=True)
def _empty_registry():
    """Jeder Test beginnt ohne geladene Plugins — und hinterlässt keine.

    Ohne diese Fixture beeinflussten sich die Tests über den Modulzustand der
    Registry, und die Reihenfolge entschiede mit. Das ist genau die Klasse von
    Fehler, die man erst bemerkt, wenn jemand einen einzelnen Test laufen lässt.
    """
    register_loaded(())
    yield
    register_loaded(())


# ─── Rollen ───────────────────────────────────────────────────────────────────


def test_die_rollen_kommen_aus_den_protokollen() -> None:
    """Abgeleitet, nicht deklariert.

    Eine Quelle, die `QuoteSource` erbt, kann Kurse. Das noch einmal
    hinzuschreiben wäre eine zweite Wahrheit, die beim ersten Umbau
    auseinanderläuft.
    """
    assert roles_of(DemoResolver) == frozenset({"resolvers"})
    assert roles_of(TwoRoleSource) == frozenset({"resolvers", "quotes"})


def test_ein_bauplan_sieht_aus_wie_ein_eingebauter() -> None:
    """Genau das ist der Punkt: In der Registry ist ein Plugin nichts Besonderes."""
    spec = spec_from_class(DemoResolver)

    assert spec.name == "demo"
    assert spec.roles == frozenset({"resolvers"})
    assert spec.loaded is True

    built = spec.build("resolvers", {"a": 1}, object())
    assert isinstance(built, DemoResolver)


# ─── Verzeichnisweg ───────────────────────────────────────────────────────────


def _write_plugin(directory: Path, name: str, body: str) -> Path:
    """Legt eine Plugin-Datei an, wie ein Betreiber sie in `data/plugins/` legt."""
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{name}.py"
    path.write_text(body, encoding="utf-8")
    return path


def test_eine_datei_wird_geladen(tmp_path: Path) -> None:
    """Der Weg zum Ausprobieren: eine Datei, ein `SOURCES`."""
    _write_plugin(
        tmp_path,
        "meins",
        "from stockinfo_plugin.sources import Resolver\n"
        "class MineFromFile(Resolver):\n"
        "    name = 'meins'\n"
        "    api_version = 2\n"
        "SOURCES = [MineFromFile]\n",
    )

    result = load_directory_sources(tmp_path)

    assert [spec.name for spec in result.specs] == ["meins"]
    assert result.problems == ()


def test_ein_fehlendes_verzeichnis_ist_kein_fehler(tmp_path: Path) -> None:
    """Die meisten Installationen haben keine eigenen Plugins.

    Eine Warnung bei jedem Start wäre nach dem dritten Mal Rauschen — und
    Rauschen verdeckt die Meldung, auf die es ankommt.
    """
    result = load_directory_sources(tmp_path / "gibt-es-nicht")

    assert result.specs == ()
    assert result.problems == ()


def test_eine_datei_die_beim_import_wirft_reisst_die_anderen_nicht_mit(
    tmp_path: Path,
) -> None:
    """**Die Leitregel dieses Moduls, als Test.**

    Die zweite Hälfte ist die wichtigere: Dass die kaputte Datei gemeldet wird,
    ist die halbe Aussage — dass die **gesunde daneben trotzdem ankommt**, ist
    die andere.
    """
    _write_plugin(tmp_path, "kaputt", "raise RuntimeError('ich bin kaputt')\n")
    _write_plugin(
        tmp_path,
        "heil",
        "from stockinfo_plugin.sources import Resolver\n"
        "class Intact(Resolver):\n"
        "    name = 'heil'\n"
        "    api_version = 2\n"
        "SOURCES = [Intact]\n",
    )

    result = load_directory_sources(tmp_path)

    assert [spec.name for spec in result.specs] == ["heil"]
    assert any("ich bin kaputt" in problem.reason for problem in result.problems)


def test_eine_datei_ohne_sources_wird_benannt(tmp_path: Path) -> None:
    """Der häufigste Anfängerfehler — und die Meldung nennt ihn beim Namen."""
    _write_plugin(tmp_path, "leer", "GIBT_ES_NICHT = 1\n")

    result = load_directory_sources(tmp_path)

    assert result.specs == ()
    assert any("kein SOURCES" in problem.reason for problem in result.problems)


def test_hilfsmodule_gelten_nicht_als_plugin(tmp_path: Path) -> None:
    """Ein führender Unterstrich hält Hilfsmodule und Editor-Reste heraus."""
    _write_plugin(tmp_path, "_helfer", "raise RuntimeError('darf nie laufen')\n")

    result = load_directory_sources(tmp_path)

    assert result.specs == ()
    assert result.problems == ()


def test_eine_plugin_datei_verdraengt_kein_standardmodul(tmp_path: Path) -> None:
    """`json.py` im Plugin-Verzeichnis darf nicht das Standardmodul ersetzen.

    Ohne den Namensraum vor dem Modulnamen wäre der Fehler an einer ganz
    anderen Stelle aufgetaucht — irgendwo, wo jemand `json.loads` ruft.
    """
    import json as standard_json

    _write_plugin(
        tmp_path,
        "json",
        "from stockinfo_plugin.sources import Resolver\n"
        "class Foreign(Resolver):\n"
        "    name = 'fremd'\n"
        "    api_version = 2\n"
        "SOURCES = [Foreign]\n",
    )

    result = load_directory_sources(tmp_path)

    assert [spec.name for spec in result.specs] == ["fremd"]
    assert standard_json.loads("{}") == {}, "das echte json ist unangetastet"


# ─── Prüfungen an der Klasse ──────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("source_class", "expected"),
    [
        (WrongVersion, "api_version"),
        (Nameless, "hat keinen name"),
        (object, "keine Source-Unterklasse"),
    ],
)
def test_was_nicht_als_quelle_taugt_wird_abgelehnt(
    tmp_path: Path, source_class: type, expected: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Drei Ablehnungsgründe, jeder mit einer Meldung, die ihn nennt.

    Die App startet in allen drei Fällen — geprüft wird hier die **Meldung**,
    denn eine Ablehnung ohne Grund schickt den Autor auf die Suche.
    """

    class FakePoint:
        name = "kandidat"

        def load(self):
            return source_class

    monkeypatch.setattr(
        "app.plugin_loader.entry_points", lambda group=None: [FakePoint()]
    )

    result = load_entry_point_sources()

    assert result.specs == ()
    assert any(expected in problem.reason for problem in result.problems)


def test_ein_entry_point_der_beim_import_wirft(monkeypatch: pytest.MonkeyPatch) -> None:
    """Ein kaputtes Paket darf die übrigen Entry-Points nicht mitreißen."""

    class Broken:
        name = "kaputt"

        def load(self):
            raise ImportError("Abhängigkeit fehlt")

    class Good:
        name = "gut"

        def load(self):
            return DemoResolver

    monkeypatch.setattr(
        "app.plugin_loader.entry_points", lambda group=None: [Broken(), Good()]
    )

    result = load_entry_point_sources()

    assert [spec.name for spec in result.specs] == ["demo"]
    assert any("Abhängigkeit fehlt" in problem.reason for problem in result.problems)


def test_die_entry_point_gruppe_heisst_wie_dokumentiert() -> None:
    """Der Name ist eine öffentliche Schnittstelle — Plugin-Autoren tippen ihn ab."""
    assert ENTRY_POINT_GROUP == "stockinfo.sources"


# ─── Beide Wege zusammen ──────────────────────────────────────────────────────


def test_eine_datei_schlaegt_einen_gleichnamigen_entry_point(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Wer eine Datei hinlegt, hat es getan, um genau das zu erreichen.

    Gemeldet wird es trotzdem: Ein stiller Vorrang wäre der Fall, in dem jemand
    stundenlang das installierte Paket debuggt, das gar nicht läuft.
    """

    class Point:
        name = "demo"

        def load(self):
            return DemoResolver

    monkeypatch.setattr("app.plugin_loader.entry_points", lambda group=None: [Point()])
    _write_plugin(
        tmp_path / "plugins",
        "demo",
        "from stockinfo_plugin.sources import Resolver\n"
        "class FromFile(Resolver):\n"
        "    name = 'demo'\n"
        "    api_version = 2\n"
        "SOURCES = [FromFile]\n",
    )

    result = load_all(tmp_path)

    assert [spec.name for spec in result.specs] == ["demo"]
    assert result.specs[0].build("resolvers", {}, object()).__class__.__name__ == (
        "FromFile"
    )
    assert any("mehrfach geladen" in problem.reason for problem in result.problems)


def test_ein_plugin_kann_keine_eingebaute_quelle_verdraengen() -> None:
    """Sonst ließen sich die Kurse der App still umleiten.

    Der Betreiber sähe in `/sources` weiterhin `yfinance` und bekäme die Daten
    von woanders. Das ist kein Randfall, sondern der Grund für die Regel.
    """

    class Attacker(Resolver):
        api_version = 2
        name = "yfinance"

    register_loaded((spec_from_class(Attacker),))

    known = specs_by_name()

    assert known["yfinance"] in BUILTIN_SOURCES


def test_geladene_quellen_stehen_neben_den_eingebauten() -> None:
    """Gleichwertig in derselben Tabelle — das ist die Zusage von T-23."""
    register_loaded((spec_from_class(DemoResolver),))

    known = specs_by_name()

    assert "demo" in known
    assert {spec.name for spec in BUILTIN_SOURCES} <= set(known)


# ─── Isolation ────────────────────────────────────────────────────────────────


class Thrower(Resolver):
    """Eine Quelle, die den Vertrag bricht und wirft."""
    api_version = 2

    name = "werfer"

    def resolve(self, request: ResolveRequest) -> Resolution:
        raise RuntimeError("boom")


class Failing(Resolver):
    """Eine Quelle, die sich korrekt verhält und trotzdem nicht arbeiten kann."""
    api_version = 2

    name = "ausfaller"

    def resolve(self, request: ResolveRequest) -> Resolution:
        return Unavailable(error="Anbieter weg")


def test_eine_werfende_quelle_wird_zur_antwort() -> None:
    """Ein Vertragsbruch wird zu `Unavailable` — nicht zu einem Absturz der App."""
    guarded = GuardedSource(Thrower())

    answer = guarded.resolve(ResolveRequest(isin="US0378331005"))

    assert isinstance(answer, Unavailable)
    assert "RuntimeError" in answer.error and "boom" in answer.error


def test_angaben_ueber_die_quelle_werden_durchgereicht() -> None:
    """`name` und `cost` sind Auskünfte, keine Aufrufe — sie gehen unverändert durch."""
    guarded = GuardedSource(DemoResolver())

    assert guarded.name == "demo"
    assert guarded.cost == "free"


def test_der_schalter_oeffnet_erst_nach_wiederholtem_fehlschlag() -> None:
    """Drei und nicht einer.

    Ein einzelner Ausfall ist Alltag — ein Zeitfehler, ein 502, ein
    Ratenlimit. Wer danach sofort stilllegt, schaltet eine gesunde Quelle wegen
    eines Schluckaufs ab.
    """
    guarded = GuardedSource(Failing())
    request = ResolveRequest(isin="US0378331005")

    for _ in range(2):
        guarded.resolve(request)
    assert guarded.breaker.is_open is False, "zwei Fehlschläge sind noch ein Muster"

    guarded.resolve(request)
    assert guarded.breaker.is_open is True


def test_ein_erfolg_setzt_den_zaehler_zurueck() -> None:
    """Sonst summierten sich Fehlschläge über Stunden zu einer Stilllegung."""

    class Flaky(Resolver):
        api_version = 2
        name = "wackelig"

        def __init__(self):
            super().__init__()
            self.calls = 0

        def resolve(self, request: ResolveRequest) -> Resolution:
            self.calls += 1
            if self.calls == 3:
                return Resolved(ListedIdentity(ticker="OK", mic="XTSE"), "Okay", "stock")
            return Unavailable(error="später nochmal")

    guarded = GuardedSource(Flaky())
    request = ResolveRequest(isin="US0378331005")

    for _ in range(4):
        guarded.resolve(request)

    assert guarded.breaker.failures == 1, "nach dem Erfolg wurde neu gezählt"
    assert guarded.breaker.is_open is False


def test_halb_offen_und_reset_ohne_echte_wartezeit() -> None:
    """**Verify `#5` — und der Grund für die eingespeiste Uhr.**

    Ohne sie dauerte dieser Test fünf Minuten und liefe deshalb nie. Die Uhr
    wird hereingereicht, nicht gestellt: Ein Test, der `time.sleep` benutzt,
    prüft die Geduld der Testsuite.
    """
    now = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    breaker = CircuitBreaker(clock=lambda: now)
    source = Failing()
    guarded = GuardedSource(source, breaker)
    request = ResolveRequest(isin="US0378331005")

    for _ in range(3):
        guarded.resolve(request)
    assert breaker.is_open is True

    # Solange der Schalter offen ist, wird die Quelle **gar nicht** gefragt.
    class Forbidden(Failing):
        def resolve(self, request: ResolveRequest) -> Resolution:
            raise AssertionError("die Quelle wurde trotz offenem Schalter gefragt")

    suppressed = GuardedSource(Forbidden(), breaker).resolve(request)
    assert isinstance(suppressed, Unavailable)
    assert "stillgelegt" in suppressed.error

    # Die Uhr weiterdrehen — jetzt darf **ein** Versuch durch.
    now += timedelta(minutes=6)
    assert breaker.is_open is False, "halb offen, ohne dass jemand gewartet hätte"

    class Recovered(Resolver):
        api_version = 2
        name = "geheilt"

        def resolve(self, request: ResolveRequest) -> Resolution:
            return Resolved(ListedIdentity(ticker="OK", mic="XTSE"), "Okay", "stock")

    answer = GuardedSource(Recovered(), breaker).resolve(request)

    assert isinstance(answer, Resolved)
    assert breaker.failures == 0 and breaker.opened_at is None, "vollständig geschlossen"


def test_ein_fehlschlag_im_halb_offenen_zustand_oeffnet_wieder() -> None:
    """Sonst liefe die App nach jeder Frist erneut in denselben Fehler."""
    now = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    breaker = CircuitBreaker(threshold=1, clock=lambda: now)
    guarded = GuardedSource(Failing(), breaker)
    request = ResolveRequest(isin="US0378331005")

    guarded.resolve(request)
    assert breaker.is_open is True

    now += timedelta(minutes=6)
    assert breaker.is_open is False

    guarded.resolve(request)
    assert breaker.is_open is True, "der Versuch ist gescheitert — wieder zu"


def test_ein_nicht_gefundenes_papier_ist_kein_fehlschlag() -> None:
    """`NotFound` heißt „gibt es hier nicht" — die Quelle hat gearbeitet.

    Würde der Schalter das mitzählen, legte er eine gesunde Quelle still, nur
    weil jemand dreimal nach einem unbekannten Papier gefragt hat.
    """

    class Unknown(Resolver):
        api_version = 2
        name = "unbekannt"

        def resolve(self, request: ResolveRequest) -> Resolution:
            return NotFound()

    guarded = GuardedSource(Unknown())
    request = ResolveRequest(isin="US0378331005")

    for _ in range(5):
        guarded.resolve(request)

    assert guarded.breaker.is_open is False
    assert guarded.breaker.failures == 0


def test_jede_quelle_hat_ihren_eigenen_schalter() -> None:
    """Ein geteilter legte eine gesunde Quelle still, weil eine andere ausfiel."""
    broken = GuardedSource(Failing())
    healthy = GuardedSource(DemoResolver())
    request = ResolveRequest(isin="US0378331005")

    for _ in range(3):
        broken.resolve(request)

    assert broken.breaker.is_open is True
    assert healthy.breaker.is_open is False


def test_im_halb_offenen_zustand_kommt_genau_einer_durch() -> None:
    """**Befund aus Runde 1: „genau ein Versuch" stand nur in der Prosa.**

    Nach Ablauf der Frist meldete `is_open` schlicht ``False``. Zwei
    gleichzeitige Aufrufer fragten daraufhin **beide** die Quelle — also genau
    der Sturm, vor dem der halb offene Zustand schützen soll.

    Die Barriere ist der Kern des Tests: Ohne sie starteten die Threads
    nacheinander, der erste wäre fertig, bevor der zweite beginnt, und das
    Rennen fände gar nicht statt. Der Test wäre grün gewesen, ohne etwas zu
    prüfen.
    """
    now = datetime(2026, 1, 2, 12, 0, tzinfo=timezone.utc)
    breaker = CircuitBreaker(threshold=1, clock=lambda: now)
    attempts: list[int] = []
    guard = threading.Barrier(2)
    counter_lock = threading.Lock()

    class Slow(Resolver):
        api_version = 2
        name = "langsam"

        def resolve(self, request: ResolveRequest) -> Resolution:
            with counter_lock:
                attempts.append(1)
            return Unavailable(error="immer noch weg")

    guarded = GuardedSource(Slow(), breaker)
    request = ResolveRequest(isin="US0378331005")

    guarded.resolve(request)  # öffnet den Schalter
    assert breaker.is_open is True
    attempts.clear()

    now += timedelta(minutes=6)  # halb offen

    def concurrently() -> None:
        guard.wait()
        guarded.resolve(request)

    threads = [threading.Thread(target=concurrently) for _ in range(2)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    assert len(attempts) == 1, (
        f"{len(attempts)} Aufrufe kamen durch — der halb offene Zustand "
        "reserviert genau einen"
    )
    assert breaker.is_open is True, "der Probeversuch scheiterte — wieder zu"


@pytest.mark.parametrize(
    ("role", "source", "method"),
    [
        ("resolvers", "openfigi", "resolve_isin"),
        ("quotes", "yfinance", "fetch_quote"),
        ("daily", "yfinance", "fetch_daily_closes"),
        ("fx", "yfinance", "fetch_fx_rate"),
        ("etf_meta", "justetf", "fetch_etf"),
    ],
)
def test_jede_rolle_liefert_dem_core_was_er_ruft(
    role: str, source: str, method: str
) -> None:
    """**Der Befund aus Runde 2, und der Grund für diesen Test.**

    Dort war `contract` an der Quelle gesetzt, aber die Adaptertabelle hatte
    nur zwei Einträge. Für `daily` und `fx` bekam der Core damit das nackte
    Plugin und rief darauf Methoden, die es nicht hat — ein `AttributeError`
    im Betrieb.

    **Kein einziger Test hat das gesehen**, weil keiner diese Rollen durch den
    Container geführt hat. Dieser hier tut es, für alle fünf: Er fragt nicht,
    was gebaut wurde, sondern ob das Gebaute die Methode **hat**, die der Core
    aufruft.
    """
    from app.config import Settings
    from app.sources_config import SourcesConfig
    from app.sources_registry import build_chain

    chain = build_chain(role, SourcesConfig(chains={role: (source,)}), Settings())

    assert chain, f"{source} ist für {role} nicht einsatzbereit"
    assert hasattr(chain[0], method), (
        f"{type(chain[0]).__name__} hat kein {method} — der Core ruft es"
    )


def test_eine_auskunft_bewegt_den_schutzschalter_nicht() -> None:
    """**Befund aus Runde 2 — und er machte den Schalter wirkungslos.**

    `CompositeResolver` ruft vor jedem `resolve` erst `handles`. Solange auch
    diese Auskunft als Erfolg zählte, setzte sie den Zähler **vor jedem**
    Fehlschlag zurück: Eine Quelle, die dauerhaft ausfällt, aber brav ihre
    Zuständigkeit meldet, erreichte die Schwelle nie.

    Der Test ruft `handles` deshalb genau so, wie die Kette es tut.
    """

    class Failing(Resolver):
        api_version = 2
        name = "ausfaller"

        def handles(self, request: ResolveRequest) -> bool:
            return True

        def resolve(self, request: ResolveRequest) -> Resolution:
            return Unavailable(error="weg")

    guarded = GuardedSource(Failing())
    request = ResolveRequest(isin="US0378331005")

    for _ in range(3):
        guarded.handles(request)
        guarded.resolve(request)

    assert guarded.breaker.failures == 3, "die Auskunft hat nichts zurückgesetzt"
    assert guarded.breaker.is_open is True


def test_eine_verworfene_quelle_erscheint_nicht_als_brauchbar() -> None:
    """**Befund aus Runde 2:** `/sources` und der Bauweg widersprachen sich.

    Eine Quelle, deren `configuration_problem()` spricht, wird beim Bauen
    verworfen — der Leseweg meldete sie trotzdem als `configured: true` und
    `usable: true`. Zwei getrennte Auswertungen unterscheiden sich beim ersten
    Sonderfall, und ausgerechnet die Diagnose meldet dann das Falsche.
    """
    from app.config import Settings
    from app.sources_config import SourcesConfig
    from app.sources_registry import (
        SourceSpec,
        build_chain,
        describe_chain,
        register_loaded,
    )

    class WithoutFile(Resolver):
        api_version = 2
        name = "ohne-datei"

        def configuration_problem(self) -> str:
            return "Datei fehlt"

    register_loaded(
        (
            SourceSpec(
                "ohne-datei",
                frozenset({"resolvers"}),
                lambda role, config, settings: WithoutFile(config),
                loaded=True,
            ),
        )
    )
    config = SourcesConfig(chains={"resolvers": ("ohne-datei",)})

    # **Erst bauen, dann lesen** — wie beim Start. Seit Runde 4 konstruiert ein
    # reiner Lesezugriff nichts mehr: `/sources` zeigt die laufende Kette,
    # nicht eine frisch erzeugte. Eine Selbstauskunft, die erst beim Bauen
    # entsteht, kann er deshalb auch erst danach kennen.
    assert build_chain("resolvers", config, Settings()) == []

    entry = describe_chain("resolvers", config, Settings())[0]

    assert entry.configured is False
    assert entry.usable is False
    assert "Datei fehlt" in entry.reason


def test_eine_fx_quelle_wird_ebenso_gekapselt() -> None:
    """Die Kapsel hängt an der Methode, nicht an der Rolle.

    Ohne diesen Test bewiese die Suite nur, dass Resolver gekapselt sind — und
    genau die anderen vier Rollen wären die Lücke.
    """

    class BrokenFx(FxSource):
        api_version = 2
        name = "fx-kaputt"

        def fetch_rate(self, request: object) -> object:
            raise ValueError("keine Kurse")

    guarded = GuardedSource(BrokenFx())

    answer = guarded.fetch_rate(object())

    assert isinstance(answer, Unavailable)
    assert "ValueError" in answer.error
