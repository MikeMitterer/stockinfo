"""Die Test-Außengrenzen müssen den echten Verträgen entsprechen.

Ein Ersatz mit `*args, **kwargs` nimmt **jeden** Aufruf an. Ändert sich der
Provider-Vertrag, merkt das ein Test, der ihn benutzt, deshalb nicht — er läuft
weiter grün und behauptet dabei, die echte Kette geprüft zu haben. Das ist die
schlechteste Sorte grüner Test: einer, der einen Bruch verdeckt.

Python prüft strukturelle Protokolle zur Laufzeit nicht (`Protocol` ohne
`@runtime_checkable`, und selbst damit sähe `isinstance` nur die Namen, nicht
die Signaturen). Also wird hier ausdrücklich verglichen.
"""

import inspect

import pytest

from app.providers.base import EtfEnricher
from app.services.daily_sync import DailyCloseProvider
from tests.boundaries import EmptyDailyCloseProvider, EmptyEtfEnricher


@pytest.mark.parametrize(
    ("protocol", "boundary"),
    [
        (DailyCloseProvider, EmptyDailyCloseProvider),
        (EtfEnricher, EmptyEtfEnricher),
    ],
    ids=["daily", "etf"],
)
def test_die_grenze_traegt_die_signatur_ihres_vertrags(protocol, boundary) -> None:
    """Jede Methode des Protokolls, mit genau ihren Parametern.

    Verglichen werden Namen, Reihenfolge, Vorgabewerte und die Trennung
    zwischen Positions- und Schlüsselwort-Parametern — `inspect.Signature`
    bildet das alles ab. Ein zusätzlicher Parameter auf der Test-Seite fällt
    damit ebenso auf wie ein fehlender.
    """
    methods = [
        name
        for name, member in vars(protocol).items()
        if callable(member) and not name.startswith("_")
    ]
    assert methods, "das Protokoll nennt keine Methoden — dann prüft dieser Test nichts"

    for name in methods:
        expected = inspect.signature(getattr(protocol, name))
        actual = inspect.signature(getattr(boundary, name))

        assert actual == expected, f"{boundary.__name__}.{name} weicht vom Vertrag ab"


def test_die_leere_daily_grenze_meldet_keinen_fehler() -> None:
    """Leere Liste heißt „nichts da", ``None`` hieße „nicht erreichbar".

    Der Unterschied ist im Produktcode entscheidend, und eine Grenze, die ihn
    verwechselt, prüft in jedem Test das falsche Verhalten.
    """
    assert EmptyDailyCloseProvider().fetch_daily_closes("VGWL.DE") == []


def test_die_leere_etf_grenze_ist_nicht_zustaendig() -> None:
    """Beide Fragen verneint — und zwar mit den richtigen zwei Antworten."""
    boundary = EmptyEtfEnricher()

    assert boundary.is_responsible("IE00B3RBWM25") is False
    assert boundary.fetch_etf("IE00B3RBWM25") is None
