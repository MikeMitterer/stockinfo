from types import SimpleNamespace

from app.container import _build_resolver
from app.resolver import CompositeResolver, OpenFigiResolver


def _settings(strict: bool) -> SimpleNamespace:
    return SimpleNamespace(openfigi_api_key="", default_exchange="XETR", strict_exchange=strict)


def test_strict_hat_keinen_yahoo_fallback() -> None:
    resolver = _build_resolver(_settings(strict=True))
    assert isinstance(resolver, OpenFigiResolver)  # nur OpenFIGI, kein Fallback


def test_nicht_strict_hat_composite_mit_fallback() -> None:
    resolver = _build_resolver(_settings(strict=False))
    assert isinstance(resolver, CompositeResolver)
