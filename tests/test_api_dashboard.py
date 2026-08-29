from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from app.config import Settings, get_settings
from app.container import get_cached_quote_service, get_quote_analyzer
from app.main import app
from app.models import (
    AnalyzeResult,
    AnalyzeStage,
    ListedIdentityOut,
    QuoteResponse,
    with_identity,
)
from app.services.quote_cache import IsinConflictError
from app.services.quote_service import InstrumentNotFoundError


class FakeService:
    def list_instruments(self) -> list[dict]:
        # **Über `with_identity`, nicht mit einem handgeschriebenen
        # `identity`-Block.** Der echte Dienst faltet die flachen Spalten der
        # gespeicherten Zeile genau so; eine zweite Fassung hier liefe beim
        # ersten Zusatzfeld auseinander, und der Test prüfte dann eine Form,
        # die es im Betrieb nicht gibt.
        return [
            with_identity(
                {
                    "symbol": "VGWL.DE",
                    "isin": "IE00B3RBWM25",
                    "history_count": 2,
                    "kind": "listed",
                    "ticker": "VGWL",
                    "mic": "XETR",
                    "listing_id": "018f3a2c-7b41-7c9e-a3d2-5f1b9c4e2a10",
                    "latest_price": 161.0,
                    "source": "yfinance+justetf",
                }
            )
        ]

    def count_instruments(self) -> int:
        return 1

    def refresh_all(self) -> int:
        return 3

    def refresh_one(self, isin: str) -> QuoteResponse:
        if isin.startswith("XX"):
            raise InstrumentNotFoundError(isin)
        return QuoteResponse(
            identity=ListedIdentityOut(ticker="VGWL", mic="XETR", isin=isin),
            symbol="VGWL.DE",
            currency="EUR",
            price=161.0,
            quote_time="t",
            fetched_at="t",
            type="etf",
        )

    def refresh_one_by_symbol(self, symbol: str) -> QuoteResponse:
        return QuoteResponse(
            identity=ListedIdentityOut(ticker="MC", mic="XPAR", isin=None),
            symbol=symbol,
            currency="EUR",
            price=430.0,
            quote_time="t",
            fetched_at="t",
            type="stock",
        )

    def delete_instrument(self, isin: str) -> bool:
        return not isin.startswith("XX")

    def delete_by_symbol(self, symbol: str) -> bool:
        return not symbol.startswith("XX")

    def set_isin(self, symbol: str, isin: str) -> None:
        if symbol.startswith("XX"):
            raise InstrumentNotFoundError(symbol)
        if isin == "IE00B4L5Y983":
            raise IsinConflictError(isin)


@pytest.fixture
def client() -> Iterator[TestClient]:
    app.dependency_overrides[get_cached_quote_service] = FakeService
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_instruments(client: TestClient) -> None:
    response = client.get("/instruments")
    assert response.status_code == 200
    assert response.json()[0]["symbol"] == "VGWL.DE"
    # Fehlt `source` auf `InstrumentSummary`, filtert FastAPI es stillschweigend
    # aus der Antwort — die Repository-Tests merkten davon nichts.
    assert response.json()[0]["source"] == "yfinance+justetf"


def test_env(client: TestClient) -> None:
    response = client.get("/env")
    assert response.status_code == 200
    body = response.json()
    assert body["default_exchange"] == "XETR"
    assert "openfigi_key_set" in body and "version" in body


def test_env_zeigt_strict_exchange(client: TestClient) -> None:
    body = client.get("/env").json()
    assert "strict_exchange" in body
    assert body["strict_exchange"] is False  # Default


def test_refresh_global(client: TestClient) -> None:
    response = client.post("/refresh")
    assert response.status_code == 200
    assert response.json()["refreshed"] == 3


def test_refresh_one_und_404(client: TestClient) -> None:
    assert client.post("/refresh/IE00B3RBWM25").status_code == 200
    assert client.post("/refresh/XX0000000000").status_code == 404


def test_delete(client: TestClient) -> None:
    assert client.delete("/instruments/IE00B3RBWM25").status_code == 204
    assert client.delete("/instruments/XX0000000000").status_code == 404


def test_refresh_by_symbol(client: TestClient) -> None:
    response = client.post("/refresh/by-symbol/BRYN.DE")
    assert response.status_code == 200
    assert response.json()["symbol"] == "BRYN.DE"


def test_delete_by_symbol(client: TestClient) -> None:
    assert client.delete("/instruments/by-symbol/BRYN.DE").status_code == 204
    assert client.delete("/instruments/by-symbol/XXNOPE").status_code == 404


def test_set_isin_ok(client: TestClient) -> None:
    response = client.put(
        "/instruments/by-symbol/BRYN.DE/isin", json={"isin": "US0846707026"}
    )
    assert response.status_code == 200
    assert response.json()["isin"] == "US0846707026"


def test_set_isin_normalisiert_und_validiert(client: TestClient) -> None:
    # klein + Leerzeichen → wird normalisiert
    response = client.put(
        "/instruments/by-symbol/BRYN.DE/isin", json={"isin": " us0846707026 "}
    )
    assert response.status_code == 200 and response.json()["isin"] == "US0846707026"
    # ungültiges Format → 422
    assert (
        client.put(
            "/instruments/by-symbol/BRYN.DE/isin", json={"isin": "nope"}
        ).status_code
        == 422
    )


def test_set_isin_unbekannt_404(client: TestClient) -> None:
    response = client.put(
        "/instruments/by-symbol/XXNOPE/isin", json={"isin": "US0846707026"}
    )
    assert response.status_code == 404


def test_set_isin_konflikt_409(client: TestClient) -> None:
    response = client.put(
        "/instruments/by-symbol/BRYN.DE/isin", json={"isin": "IE00B4L5Y983"}
    )
    assert response.status_code == 409


def test_analyze_verlangt_genau_eine_kennung(client: TestClient) -> None:
    assert client.get("/analyze").status_code == 422
    assert client.get("/analyze?isin=IE00B4L5Y983&symbol=EUNL.DE").status_code == 422


def test_exchanges_liefert_den_katalog_und_die_vorgabe(client: TestClient) -> None:
    """Der Katalog trägt seit T-21 Teil 3 zwei Eintragsarten.

    Die Liste heißt deshalb `catalog` und nicht mehr `exchanges` — sonst hieße
    eine Liste mit Sammelcodes darin weiterhin „Börsen".
    """
    body = client.get("/exchanges").json()

    assert body["default_exchange"] == "XETR"
    assert body["default_exchange_kind"] == "exchange"

    exchanges = {
        entry["mic"]: entry for entry in body["catalog"] if entry["kind"] == "exchange"
    }
    assert exchanges["XTSE"]["alias"] == "TO"
    assert exchanges["XSTU"]["alias"] == "SG"
    assert exchanges["XETR"]["currency"] == "EUR"
    assert exchanges["XNAS"]["alias"] is None


def test_kein_katalogeintrag_serialisiert_einen_sammelcode_als_mic(
    client: TestClient,
) -> None:
    """Der Vertragstest zur Trennung — hier wäre der alte Fehler sichtbar.

    Bis Teil 3 lieferte dieser Endpunkt ``mic="US"`` aus: einen Wert, den
    `is_real_mic` im selben Backend ablehnt. Ein Konsument, der ihn übernahm,
    erzeugte genau die halbe Identität, die T-21 austreibt.
    """
    body = client.get("/exchanges").json()

    collectors = [entry for entry in body["catalog"] if entry["kind"] == "collector"]
    assert [entry["code"] for entry in collectors] == ["US"]
    assert set(collectors[0]["members"]) == {"XNAS", "XNYS", "ARCX", "XASE", "BATS"}
    assert all("mic" not in entry for entry in collectors)
    assert all(
        entry["mic"] != "US" for entry in body["catalog"] if entry["kind"] == "exchange"
    )


def test_der_alias_ist_im_openapi_vertrag_optional(client: TestClient) -> None:
    """Der Vertrag muss die Abwesenheit selbst benennen, nicht nur zulassen.

    Bis zu dieser Korrektur stand `alias` in `required` und die fünf US-Plätze
    kamen als `""` herein. Ein Client-Generator hätte daraus ein Pflichtfeld
    gebaut, und T-30 müsste seinen deklarativ gemeldeten Alias an eine Form
    anfügen, die „keiner" nicht ausdrücken kann.
    """
    schema = client.get("/openapi.json").json()["components"]["schemas"][
        "ExchangeEntry"
    ]

    assert "alias" not in schema.get("required", [])
    assert {"type": "null"} in schema["properties"]["alias"]["anyOf"]


def test_der_sammelcode_bleibt_eine_zulaessige_vorgabe(client: TestClient) -> None:
    """`US` hat die Börsentabelle verlassen, nicht die Konfiguration.

    Ohne diese Zeile wäre die Trennung ein Rückschritt: Der Vorgabewert `US`
    ist dokumentiert und muss weiterhin gelten — er heißt jetzt nur
    ausdrücklich `collector` statt heimlich `mic`.
    """
    app.dependency_overrides[get_settings] = lambda: Settings(default_exchange="US")
    try:
        body = client.get("/exchanges").json()
    finally:
        app.dependency_overrides.pop(get_settings, None)

    assert body["default_exchange"] == "US"
    assert body["default_exchange_kind"] == "collector"


def test_analyze_liefert_stages(client: TestClient) -> None:
    class _StubAnalyzer:
        def analyze(self, *, isin=None, symbol=None) -> AnalyzeResult:
            return AnalyzeResult(
                symbol="EUNL.DE",
                isin=isin,
                total=1.23,
                stages=[AnalyzeStage(stage="openfigi", seconds=0.5, status="ok")],
            )

    app.dependency_overrides[get_quote_analyzer] = lambda: _StubAnalyzer()
    try:
        response = client.get("/analyze?isin=IE00B4L5Y983")
    finally:
        app.dependency_overrides.pop(get_quote_analyzer, None)

    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1.23
    assert body["stages"][0]["stage"] == "openfigi"
