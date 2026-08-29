"""Die Doubles selbst — ein Werkzeug, das lügt, ist schlimmer als keines.

Wer eine Kette mit Doubles prüft, verlässt sich darauf, dass sie tun, was
angesagt ist. Ein Double, dessen Aufrufprotokoll einen Aufruf verschluckt,
lässt einen Kettentest grün werden, der einen echten Fehler enthält — und
niemand sucht danach im Werkzeug.
"""

from datetime import datetime, timedelta

import pytest

from stockinfo_plugin import (
    ListedIdentity,
    NotFound,
    NotResponsible,
    Resolved,
    ResolveRequest,
    Unavailable,
)
from stockinfo_plugin.testing import (
    EPOCH,
    CallLog,
    FakeClock,
    FakeDailySource,
    FakeFxSource,
    FakeQuoteSource,
    FakeResolver,
    SourceContract,
)
from stockinfo_plugin.sources import (
    DailyCloseSource,
    FxSource,
    MetadataSource,
    QuoteSource,
    Resolver,
)

REQUEST = ResolveRequest(isin="CA78012H5675")
OTHER = ResolveRequest(isin="IE00B4L5Y983")


# ─── Die Uhr ──────────────────────────────────────────────────────────────────


def test_die_uhr_geht_nur_wenn_man_sie_stellt() -> None:
    """Zwei Abfragen ohne `advance` liefern denselben Augenblick.

    Das ist der ganze Zweck: Eine Erwartung wird dadurch **exakt** statt
    ungefähr. Mit einer echten Uhr müsste jeder Vergleich eine Toleranz
    tragen, und eine Toleranz verdeckt genau die Fehler, die man sucht.
    """
    clock = FakeClock()

    assert clock.now() == clock.now() == EPOCH

    clock.advance(3600)

    assert clock.now() == EPOCH.replace(hour=13)


def test_die_uhr_laesst_sich_zurueckstellen() -> None:
    """Eine zurückgestellte Systemuhr ist ein realer Fall, kein Missbrauch.

    Wer sich auf monoton wachsende Zeit verlässt, hat einen Fehler, den er
    ohne diese Möglichkeit nie zu sehen bekommt — Zeitumstellung, NTP-Sprung,
    ein Container mit falscher Uhr beim Start.
    """
    clock = FakeClock()

    clock.advance(-60)

    assert clock.now() < EPOCH


def test_eine_uhr_ohne_zone_wird_abgelehnt() -> None:
    """Sonst schlüge der Vertrag bei einem Plugin an, dessen Fehler im Test liegt.

    Eine naive Uhr erzeugt naive Zeitstempel; die kommen genau dort an, wo
    `QuoteContract` eine Zone verlangt. Der Autor suchte dann in seinem Plugin
    nach einem Fehler, der im Testaufbau steht.
    """
    with pytest.raises(ValueError, match="Zeitzone"):
        FakeClock(datetime(2026, 1, 2, 12, 0))


# ─── Die Antworten ────────────────────────────────────────────────────────────


def test_antworten_werden_der_reihe_nach_verbraucht() -> None:
    """Erst der Ausfall, dann der Treffer — der übliche Wiederholungsfall."""
    source = FakeResolver([Unavailable("Netz"), Resolved(ListedIdentity(ticker="RY", mic="XTSE"))])

    assert isinstance(source.resolve(REQUEST), Unavailable)
    assert isinstance(source.resolve(REQUEST), Resolved)


def test_die_letzte_antwort_wiederholt_sich() -> None:
    """„Diese Quelle ist ausgefallen" gilt für jeden Aufruf, nicht für den ersten.

    Die Alternative wäre, nach dem Ende der Liste zu werfen. Dann müsste jeder
    Test vorher zählen, wie oft die Kette fragt — und genau diese Zahl ist oft
    das, was der Test herausfinden soll.
    """
    source = FakeResolver([Resolved(ListedIdentity(ticker="RY", mic="XTSE")), Unavailable("weg")])

    source.resolve(REQUEST)
    for _ in range(5):
        assert isinstance(source.resolve(REQUEST), Unavailable)


def test_ohne_vorgabe_kommt_notfound() -> None:
    """Die harmloseste Vorgabe: „nachgesehen, nichts da"."""
    assert isinstance(FakeResolver().resolve(REQUEST), NotFound)


def test_eine_antwort_je_anfrage() -> None:
    """`keyed` für den Fall, dass zwei Papiere verschieden beantwortet werden."""
    source = FakeResolver(
        keyed={REQUEST: Resolved(ListedIdentity(ticker="RY", mic="XTSE")), OTHER: NotResponsible()}
    )

    assert isinstance(source.resolve(REQUEST), Resolved)
    assert isinstance(source.resolve(OTHER), NotResponsible)


def test_eine_ausnahme_wird_geworfen_statt_zurueckgegeben() -> None:
    """Fremder Code wirft, auch wenn der Vertrag es verbietet.

    Ohne diesen Fall ließe sich nicht prüfen, ob die Kette einen Verstoß
    aushält — und die Registry fängt zwar ab, aber nur, wenn jemand das je
    getestet hat.
    """
    source = FakeResolver(TimeoutError("hängt"))

    with pytest.raises(TimeoutError, match="hängt"):
        source.resolve(REQUEST)


def test_eine_ungueltige_antwort_kommt_unveraendert_durch() -> None:
    """Ein Plugin, das den Vertrag missversteht, sieht genau so aus.

    Es gibt ``None`` zurück statt `NotFound`, oder ein Dict statt `Resolved`.
    Der Host muss das überstehen; ein Double, das solche Antworten nicht
    erzeugen kann, lässt diese Lücke ungeprüft.
    """
    assert FakeResolver([None]).resolve(REQUEST) is None
    assert FakeResolver([{"ticker": "RY"}]).resolve(REQUEST) == {"ticker": "RY"}


# ─── Das Protokoll ────────────────────────────────────────────────────────────


def test_das_protokoll_haelt_reihenfolge_und_anzahl() -> None:
    source = FakeResolver()

    source.resolve(REQUEST)
    source.resolve(OTHER)

    assert [call.request for call in source.calls] == [REQUEST, OTHER]


def test_handles_zaehlt_nicht_als_aufruf() -> None:
    """Sonst ließe sich „übersprungen" nicht von „gefragt" unterscheiden.

    Der Vertrag verspricht, dass eine unzuständige Quelle nichts kostet.
    Stünde `handles` im Protokoll, sähe ein übersprungener Aufruf genauso aus
    wie ein durchgeführter — und die Zusage wäre nicht mehr prüfbar.
    """
    source = FakeResolver(responsible=False)

    source.handles(REQUEST)

    assert source.calls == []


def test_zwei_doubles_teilen_sich_ein_protokoll() -> None:
    """Die Frage eines Kettentests ist die Reihenfolge **zwischen** den Quellen.

    Aus zwei getrennten Listen ist sie nicht zu beantworten: Die Zeitstempel
    stehen still, solange niemand die Uhr stellt, also tragen alle Aufrufe
    dieselbe Zeit. Ein gemeinsames Protokoll beantwortet die Frage direkt.
    """
    log = CallLog()
    first = FakeResolver(NotResponsible(), name="erste-quelle", log=log)
    second = FakeResolver(Resolved(ListedIdentity(ticker="RY", mic="XTSE")), name="zweite-quelle", log=log)

    first.resolve(REQUEST)
    second.resolve(REQUEST)

    assert log.order == ["erste-quelle", "zweite-quelle"]


def test_die_verzoegerung_stellt_die_uhr_statt_zu_warten() -> None:
    """Ein Double, das wirklich hängt, prüft die Geduld des Testlaufs.

    Der Zeitstempel im Protokoll steht dabei auf dem Stand **beim Eintritt**:
    Sonst ließe sich nicht mehr sagen, wann gefragt wurde, sondern nur, wann
    geantwortet wurde — und ein Zeitlimit misst die erste Zahl.
    """
    clock = FakeClock()
    source = FakeResolver(clock=clock, delay_seconds=30)

    source.resolve(REQUEST)
    source.resolve(OTHER)

    assert [call.at for call in source.calls] == [
        EPOCH,
        EPOCH + timedelta(seconds=30),
    ]
    assert clock.now() == EPOCH + timedelta(seconds=60)


def test_ein_ttl_laeuft_ohne_eine_sekunde_wartezeit_ab() -> None:
    """Die Zusage aus Verify `#9`, vorgeführt statt behauptet.

    Der Cache hier ist **Testcode und bleibt es** — dieses Paket hat keinen
    TTL, und einen zu bauen, damit die Zeile grün wird, wäre die Umkehrung der
    Beweisführung. Gezeigt wird, dass die Uhr für einen fremden TTL taugt: Ein
    Ablauf von einer Stunde wird in null Sekunden Laufzeit geprüft, und die
    Grenze ist **exakt** — nicht „ungefähr eine Stunde".

    Was hier bewusst nicht steht: Half-open und Reset eines Schutzschalters.
    Deren Bedeutung legt T-23 fest; sie hier vorwegzunehmen hieße, einen
    Entwurf zu erfinden, um ihn dann zu prüfen.
    """
    clock = FakeClock()
    stored_at = clock.now()
    ttl_seconds = 3600

    def is_fresh() -> bool:
        return (clock.now() - stored_at).total_seconds() < ttl_seconds

    assert is_fresh()

    clock.advance(ttl_seconds - 1)
    assert is_fresh(), "eine Sekunde vor Ablauf ist der Stand noch gültig"

    clock.advance(1)
    assert not is_fresh(), "genau bei Ablauf ist er es nicht mehr"


# ─── Die Rollen ───────────────────────────────────────────────────────────────


def test_jedes_double_erfuellt_genau_seine_rolle() -> None:
    """Ein Double, das alle fünf Rollen erfüllt, käme durch jede Rollenprüfung.

    Und genau die soll T-23 haben: Eine Quelle in der falschen Rolle gehört
    nicht in die Kette. Ein allwissendes Double würde diesen Fehler decken —
    deshalb fünf schmale Klassen, obwohl das Verhalten nur einmal dasteht.
    """
    assert isinstance(FakeResolver(), Resolver)
    assert not isinstance(FakeResolver(), QuoteSource)

    assert isinstance(FakeQuoteSource(), QuoteSource)
    assert not isinstance(FakeQuoteSource(), Resolver)

    assert isinstance(FakeDailySource(), DailyCloseSource)
    assert isinstance(FakeFxSource(), FxSource)
    assert not isinstance(FakeFxSource(), MetadataSource)


class TestDasDoubleHaeltDenEigenenVertrag(SourceContract):
    """Das Werkzeug wird mit demselben Maß gemessen wie die geprüften Quellen.

    Vor allem wegen `test_kein_veraenderlicher_zustand_an_der_klasse`: Das
    Aufrufprotokoll ist eine Liste, und läge sie an der Klasse statt in
    ``__init__``, zählte der zweite Testfall die Aufrufe des ersten mit. Das
    Double wäre dann selbst der Fehler, vor dem es warnt.
    """

    def make_source(self) -> FakeResolver:
        return FakeResolver()
