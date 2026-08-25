"""Tests der Börsentabelle und der Symbol-Rückrechnung (T-21)."""

import pytest

from app.exchanges import EXCHANGES, is_real_mic, split_symbol


@pytest.mark.parametrize(
    ("symbol", "expected"),
    [
        ("EUNL.DE", ("EUNL", "XETR")),
        ("XIC.TO", ("XIC", "XTSE")),
        ("EQQQ.MI", ("EQQQ", "XMIL")),
        ("7203.T", ("7203", "XTKS")),
    ],
)
def test_bekannte_suffixe_sind_eindeutig_umkehrbar(
    symbol: str, expected: tuple[str, str]
) -> None:
    """Die Rückrechnung funktioniert, weil kein Suffix doppelt vergeben ist."""
    assert split_symbol(symbol) == expected


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

    Käme eine Börse mit einem schon belegten Alias dazu, wäre `split_symbol`
    stillschweigend mehrdeutig. Dieser Test schlägt dann an, statt dass die
    Migration ein falsches Listing zuordnet.

    Leere Aliase sind ausgenommen: Die fünf US-Plätze teilen sich den leeren,
    und genau deshalb ist `AAPL` nicht rückrechenbar.
    """
    aliases = [
        definition.alias for definition in EXCHANGES.values() if definition.alias
    ]

    assert len(aliases) == len(set(aliases))


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


@pytest.mark.parametrize("mic", ["XETR", "XTSE", "XNAS", "XNYS", "X0AT"])
def test_echte_mics_werden_angenommen(mic: str) -> None:
    """Vier Großbuchstaben oder Ziffern — auch wenn die Tabelle sie nicht kennt.

    `XNAS` steht nicht in der eigenen Börsentabelle und ist trotzdem der Wert,
    den eine manuelle Zuordnung setzen soll. Die Tabelle ist eine Auswahl, kein
    Verzeichnis aller MICs.
    """
    assert is_real_mic(mic) is True


@pytest.mark.parametrize(
    ("mic", "reason"),
    [
        ("US", "Sammelcode der eigenen Tabelle, kein ISO-MIC"),
        (None, "gar kein Wert"),
        ("", "leer"),
        ("NOT-A-MIC", "zu lang"),
        ("XNA", "zu kurz"),
        ("xnAs", "Kleinbuchstaben"),
        ("XN@S", "Sonderzeichen"),
        ("XNAS ", "Leerzeichen am Ende"),
        (" US", "Leerzeichen am Anfang"),
        ("XNAS\n", "Zeilenumbruch am Ende — `$` würde ihn durchlassen"),
        ("XNAS\t", "Tabulator am Ende"),
    ],
)
def test_ungueltige_mics_werden_abgelehnt(mic: str | None, reason: str) -> None:
    """Unbekannt heißt nicht gültig.

    Meine erste Fassung ließ jeden nichtleeren String durch, den die Tabelle
    nicht kannte — damit konnte im kanonischen Feld alles stehen, auch
    `NOT-A-MIC`. Ein MIC nach ISO 10383 hat genau vier Zeichen, Großbuchstaben
    oder Ziffern.

    Der Zeilenumbruch am Ende ist der tückischste Fall: In Python matcht `$`
    auch **vor** einem abschließenden `\n`. Der Ausdruck sah richtig aus und
    ließ `XNAS\n` durch — ein Wert, den der Eindeutigkeits-Index sogar von
    `XNAS` unterscheidet.
    """
    assert is_real_mic(mic) is False, reason
