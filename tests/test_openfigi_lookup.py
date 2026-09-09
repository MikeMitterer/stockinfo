"""Konkrete Handelsplätze und MIC-Formregel ohne Sammelcodes."""

import pytest

from app.exchanges import EXCHANGES, ExchangeDef, home_exchange, is_real_mic


@pytest.mark.parametrize("mic", ["XETR", "XNAS", "ARCX"])
def test_eine_konkrete_boerse_hat_einen_gueltigen_mic(mic: str) -> None:
    """US-Plätze bleiben einzeln adressierbar."""
    assert is_real_mic(mic)
    assert mic in EXCHANGES


def test_die_boersentabelle_traegt_kein_anbieterwissen() -> None:
    """Anfragefelder gehören zum Provider, nicht in den Börsenkatalog."""
    assert set(ExchangeDef.__dataclass_fields__) == {"alias", "name", "region", "currency"}


def test_ein_land_ist_keine_boerse() -> None:
    """Eine US-ISIN darf weder einen Sammelcode noch eine geratene Börse erhalten."""
    assert not is_real_mic("US")
    assert home_exchange("US0378331005") is None
    assert home_exchange("CA7800871021") == "XTSE"
