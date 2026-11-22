"""Eine abgelehnte Anfrage als **Kennung mit Werten** — für jeden Router.

Die Router werfen `ApiError` statt `HTTPException(detail="…")`. Der zentrale
Handler in `app.main` macht daraus `ErrorDetail`, also `{code, params}` auf
oberster Ebene. Eine `HTTPException` verpackte den Rumpf unter `detail`, und
ein deutscher Satz dort wäre in jeder anderen Sprache falsch: Den Satz bildet
der Konsument aus seinem Katalog (Dashboard: `errors.reason`).

Geworfen statt zurückgegeben, weil auch Abhängigkeiten wie die
Symbolprüfung ablehnen: Sie können keine Antwort zurückgeben, nur werfen.

Jede Kennung steht als Konstante `REASON_*` im Modul, das sie wirft. Daraus
liest `tests/test_error_reason_catalogue.py` den Bestand und hält ihn gegen
den Katalog des Dashboards.
"""


class ApiError(Exception):
    """Eine Ablehnung mit Status, Kennung und Werten für den übersetzten Satz.

    Args:
        status_code: HTTP-Status der Antwort.
        code: Stabile Kennung, etwa ``instrument_not_stored``.
        params: Werte, die der übersetzte Satz einsetzt. Nur Zeichenketten,
            wie `ErrorDetail` sie zusagt.
    """

    def __init__(self, status_code: int, code: str, params: dict[str, str] | None = None) -> None:
        super().__init__(code)
        self.status_code = status_code
        self.code = code
        self.params = params or {}
