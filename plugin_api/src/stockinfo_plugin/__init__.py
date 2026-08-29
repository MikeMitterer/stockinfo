"""Der Plugin-Vertrag von StockInfo.

Dieses Paket enthält **nur** Verträge, Datentypen und Testwerkzeuge — keine
Anwendungslogik. Ein Plugin-Autor installiert es und hängt damit an ein paar
hundert Zeilen, nicht an der ganzen App. Was unter ``app/`` passiert, darf sich
ändern, ohne fremde Plugins zu brechen; was hier steht, nicht — dafür gibt es
`API_VERSION`.

Beispiel::

    from stockinfo_plugin import Resolver, ResolveRequest, Resolved, NotFound

    class MyResolver(Resolver):
        name = "my-resolver"

        def handles(self, request: ResolveRequest) -> bool:
            return bool(request.isin and request.isin.startswith("CA"))

        def resolve(self, request: ResolveRequest):
            ...
"""

from stockinfo_plugin.sources import (
    DailyCloseSource,
    FxSource,
    MetadataSource,
    QuoteSource,
    Resolver,
    Source,
)
from stockinfo_plugin.types import (
    API_VERSION,
    Cost,
    DailyBar,
    DailyRequest,
    DailyResult,
    DailySeries,
    FieldKind,
    FieldSpec,
    FxRate,
    FxRequest,
    FxResult,
    Identity,
    IsinOnlyIdentity,
    ListedIdentity,
    NotFound,
    NotResponsible,
    PairIdentity,
    Quote,
    QuoteRequest,
    QuoteResult,
    Reading,
    Resolution,
    Resolved,
    ResolveRequest,
    Unavailable,
    Unit,
    Unsupported,
    convert,
    isin_of,
)

__all__ = [
    "API_VERSION",
    "Cost",
    "DailyBar",
    "DailyCloseSource",
    "DailyRequest",
    "DailyResult",
    "DailySeries",
    "FieldKind",
    "FieldSpec",
    "FxRate",
    "FxRequest",
    "FxResult",
    "FxSource",
    "Identity",
    "IsinOnlyIdentity",
    "ListedIdentity",
    "MetadataSource",
    "NotFound",
    "NotResponsible",
    "PairIdentity",
    "Quote",
    "QuoteRequest",
    "QuoteResult",
    "QuoteSource",
    "Reading",
    "Resolution",
    "Resolved",
    "ResolveRequest",
    "Resolver",
    "Source",
    "Unavailable",
    "Unit",
    "Unsupported",
    "convert",
    "isin_of",
]
