"""One source, two roles, one venue.

The example answers for a single US exchange, NASDAQ (`XNAS`). Everything it
does that is not about that venue is about *saying so* — which is most of what
a plugin does in practice.
"""

from datetime import datetime, timezone
from typing import Any, Protocol

from stockinfo_plugin import (
    ListedIdentity,
    NotFound,
    NotResponsible,
    Quote,
    QuoteRequest,
    QuoteResult,
    QuoteSource,
    Resolution,
    Resolved,
    ResolveRequest,
    Resolver,
    Unavailable,
)

VENUE = "XNAS"
"""The one exchange this source knows, as a MIC (ISO 10383)."""


class Market(Protocol):
    """What this plugin needs from a vendor — nothing more.

    Declaring the transport as a protocol rather than importing an HTTP client
    is what lets the tests run offline. It is also honest about the coupling:
    two methods, both returning plain data.
    """

    def lookup(self, isin: str) -> dict[str, Any] | None:
        """Ticker and description for an ISIN, or ``None`` if unknown."""

    def price(self, ticker: str) -> dict[str, Any] | None:
        """Last price for a ticker, or ``None`` if unknown."""


class MarketUnreachable(Exception):
    """The vendor could not be asked. Distinct from "asked, nothing there"."""


class _FakeMarket:
    """A stand-in vendor with four papers, used when no real one is injected.

    A real plugin would put an HTTP client here. Keeping a fake in the package
    means the example is runnable — and installable — without an account.
    """

    _PAPERS: dict[str, dict[str, Any]] = {
        "US0378331005": {"ticker": "AAPL", "name": "Apple Inc.", "type": "stock"},
        "US5949181045": {"ticker": "MSFT", "name": "Microsoft Corp.", "type": "stock"},
        "US67066G1040": {"ticker": "NVDA", "name": "NVIDIA Corp.", "type": "stock"},
        "US9229087690": {
            "ticker": "VOO",
            "name": "Vanguard S&P 500 ETF",
            "type": "etf",
        },
    }

    _PRICES: dict[str, float] = {
        "AAPL": 231.4,
        "MSFT": 402.15,
        "NVDA": 118.9,
        "VOO": 512.33,
    }

    def lookup(self, isin: str) -> dict[str, Any] | None:
        return self._PAPERS.get(isin)

    def price(self, ticker: str) -> dict[str, Any] | None:
        value = self._PRICES.get(ticker)
        if value is None:
            return None
        return {
            "price": value,
            "currency": "USD",
            "as_of": "2026-08-28T20:00:00+00:00",
        }


class UsExampleSource(Resolver, QuoteSource):
    """Resolves and prices papers listed on one US venue.

    **Two roles, one class — but one instance per role.** The operator writes
    `us-example` (this class's `name`, not the entry-point key) on both the
    `resolvers:` and the `quotes:` line, and the host builds the source once
    for each. Nothing in `self` is therefore shared between the two roles,
    which is why this example keeps no per-request state there.
    """

    name = "us-example"
    cost = "free"

    # Written out, never inherited. The loader rejects a class that does not
    # carry this value in its own body — an inherited version number would
    # silently follow the host through a contract change the plugin has not
    # been adapted to.
    api_version = 2

    # One venue, two genera. An empty set would mean "promised nothing", and
    # the host would skip this source for every known genus.
    SUPPORTED_KINDS = frozenset({"listed"})
    SUPPORTED_TYPES = frozenset({"stock", "etf"})

    def __init__(
        self, config: dict[str, Any] | None = None, market: Market | None = None
    ) -> None:
        """
        Args:
            config: The `providers.us-example` block from `sources.yaml`.
                `api_key` is required; `base_url` is optional and only
                recorded here to show how a second setting travels.
            market: The vendor. Injected by the tests; left out in production,
                where the built-in fake stands in for a real client.
        """
        super().__init__(config)
        self._api_key = str(self._config.get("api_key") or "").strip()
        self._base_url = str(self._config.get("base_url") or "").strip()
        self._market = market or _FakeMarket()

    def configuration_problem(self) -> str:
        """Why this source cannot work — addressed to whoever runs it.

        The sentence names the setting *and* the way to supply it. "Not
        configured" tells an operator that something is wrong and nothing
        about what to do next.
        """
        if not self._api_key:
            return (
                "api_key is missing — set providers.us-example.api_key in "
                "sources.yaml, e.g. to ${US_MARKET_API_KEY}"
            )
        return ""

    # ── Resolver ─────────────────────────────────────────────────────────────

    def handles(self, request: ResolveRequest | QuoteRequest) -> bool:
        """Is this source responsible at all?

        Asked before every call so an unrelated paper costs neither a request
        nor a quota. One method serves both roles here because the answer is
        the same question in both: is this a US paper on our venue?

        Being *not responsible* is not a failure. It is the answer that lets
        the chain move on to the next source.
        """
        if isinstance(request, QuoteRequest):
            identity = request.identity
            return isinstance(identity, ListedIdentity) and identity.mic == VENUE
        # The ISIN prefix decides, and `preferred_mic` deliberately does not.
        #
        # It is a *wish*, not a filter — and it is never empty: the host fills
        # it with `XETR` by default. Reading it as a filter is the first
        # mistake an author makes here, and it makes the source answer
        # `NotResponsible` to everything while looking perfectly reasonable.
        #
        # A resolver may return a different venue than the one asked for; the
        # host logs the deviation. What it must not do is claim a paper it
        # cannot identify.
        return bool(request.isin and request.isin.startswith("US"))

    def resolve(self, request: ResolveRequest) -> Resolution:
        """Answer the identity question.

        **Never raises — and the guard covers the whole body, not just the
        call.** A vendor that replies `200 OK` with a missing field fails
        during conversion, not during the request; a guard around the call
        alone would let that through.

        Every failure becomes `Unavailable`; the chain decides what to do, and
        a plugin that lets an exception through fails the contract suite.

        The three answers below are three different facts, and the host acts
        differently on each: `NotResponsible` lets the next source try,
        `NotFound` says the paper does not exist here (404), `Unavailable`
        says nobody could look (502, and the stored value survives).
        """
        if not self.handles(request):
            return NotResponsible()
        try:
            paper = self._market.lookup(request.isin or "")
            if paper is None:
                return NotFound()
            # All three fields are mandatory. A hit without `name` or
            # `instrument_type` is incomplete and must not stop the chain.
            return Resolved(
                identity=ListedIdentity(
                    ticker=paper["ticker"], mic=VENUE, isin=request.isin
                ),
                name=paper["name"],
                instrument_type=paper["type"],
            )
        except Exception as error:  # noqa: BLE001 — see the docstring
            return Unavailable(error=f"us-example: {type(error).__name__}: {error}")

    # ── QuoteSource ──────────────────────────────────────────────────────────

    def fetch_quote(self, request: QuoteRequest) -> QuoteResult:
        """Answer the price question. **Never raises**, same as `resolve` —
        including the conversion of the answer, not only the call.

        The request carries the identity, not a vendor symbol: turning
        `AAPL` + `XNAS` into whatever this vendor calls it is this source's
        job and nobody else's.
        """
        if not self.handles(request):
            return NotResponsible()
        identity = request.identity
        try:
            tick = self._market.price(identity.ticker)
            if tick is None:
                return NotFound()
            return Quote(
                price=float(tick["price"]),
                # ISO 4217, and in the major unit. A venue quoting in cents
                # converts here — the host has no way to know it did not.
                currency=str(tick["currency"]),
                as_of=self._as_of(tick["as_of"]),
            )
        except Exception as error:  # noqa: BLE001 — see the docstring
            return Unavailable(error=f"us-example: {type(error).__name__}: {error}")

    @staticmethod
    def _as_of(raw: str) -> datetime:
        """Parse the vendor timestamp, and never hand out a naive one.

        A timestamp without a zone is a wrong timestamp for everyone outside
        the vendor's own — UTC is the assumption made explicit here rather
        than left to whoever displays it.
        """
        parsed = datetime.fromisoformat(raw)
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=timezone.utc)
        return parsed
