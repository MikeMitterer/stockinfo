"""Tests der Börsentabelle und der Symbol-Rückrechnung (T-21)."""

import pytest

from app.exchanges import EXCHANGES, split_symbol


@pytest.mark.parametrize(
    ("symbol", "erwartet"),
    [
        ("EUNL.DE", ("EUNL", "XETR")),
        ("XIC.TO", ("XIC", "XTSE")),
        ("EQQQ.MI", ("EQQQ", "XMIL")),
        ("7203.T", ("7203", "XTKS")),
    ],
)
def test_bekannte_suffixe_sind_eindeutig_umkehrbar(
    symbol: str, erwartet: tuple[str, str]
) -> None:
    """Die Rückrechnung funktioniert, weil kein Suffix doppelt vergeben ist."""
    assert split_symbol(symbol) == erwartet


@pytest.mark.parametrize(
    "symbol",
    [
        "AAPL",       # suffixlos → Sammelcode US, kein echter MIC
        "BRK-B",      # fremde Schreibweise aus der Yahoo-Suche
        "EUNL.XYZ",   # Suffix, das die Tabelle nicht kennt
        ".DE",        # kein Ticker vor dem Punkt
        "",           # leer
    ],
)
def test_unklare_symbole_werden_nicht_geraten(symbol: str) -> None:
    """Im Zweifel ``(None, None)`` — die Zeile bleibt offen und sichtbar.

    Jede dieser Vermutungen wäre plausibel und keine davon belegt: `AAPL`
    könnte an der NYSE oder der NASDAQ liegen, `BRK-B` könnte `BRK.B` meinen.
    Geraten wird nichts.
    """
    assert split_symbol(symbol) == (None, None)


def test_kein_suffix_ist_doppelt_vergeben() -> None:
    """Die Voraussetzung der ganzen Rückrechnung — hier festgehalten.

    Käme eine Börse mit einem schon belegten Suffix dazu, wäre `split_symbol`
    stillschweigend mehrdeutig. Dieser Test schlägt dann an, statt dass die
    Migration ein falsches Listing zuordnet.
    """
    suffixe = [d.suffix for d in EXCHANGES.values() if d.suffix]

    assert len(suffixe) == len(set(suffixe))


def test_die_schema_schicht_zieht_kein_yfinance_mit() -> None:
    """`app/db.py` darf für die Migration nicht den halben Netzstack laden.

    Die Zerlegung sitzt deshalb in `app/exchanges.py` und nicht im Resolver:
    Dort steht `import yfinance`, und die Schema-Schicht hat damit nichts zu
    tun. Ohne diesen Test rutscht die Abhängigkeit beim nächsten Import
    unbemerkt zurück.
    """
    import ast

    quelle = ast.parse((__import__("pathlib").Path("app/db.py")).read_text(encoding="utf-8"))
    module = {
        knoten.module
        for knoten in ast.walk(quelle)
        if isinstance(knoten, ast.ImportFrom) and knoten.module
    }

    assert "app.resolver" not in module
    assert "app.exchanges" in module
