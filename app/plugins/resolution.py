"""Antworten der Core-Resolver als Auflösung des Plugin-Vertrags, für die eigenen Resolver."""

from stockinfo_plugin import ListedIdentity, Resolved

from app.providers.base import ResolvedInstrument


def listed_resolution(answer: ResolvedInstrument, requested_isin: str | None) -> Resolved:
    """Ein gefundenes Listing als `Resolved` — für OpenFIGI und die Yahoo-Suche.

    Die ISIN der Antwort geht vor; fehlt sie, gilt die angefragte, denn danach
    wurde gesucht.

    Args:
        answer: Die Antwort des Core-Resolvers mit Ticker und MIC.
        requested_isin: Die ISIN aus der Anfrage, falls es eine gab.
    """
    return Resolved(
        identity=ListedIdentity(
            ticker=answer.ticker,
            mic=answer.mic,
            isin=answer.isin or requested_isin,
        ),
        name=answer.name,
        instrument_type=answer.type,
    )
