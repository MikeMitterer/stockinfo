"""The contract suites, plus the handful of facts specific to this example.

**Most of this file is six lines of setup.** `ResolverContract` and
`QuoteContract` bring roughly thirty assertions each — that a source never
raises, that it says why it stands still, that an unrelated request costs
nothing, that a hit carries every mandatory field. An author writes the three
requests and inherits the rest.

Nothing here touches a network or needs a key. The vendor is injected, and the
one test that needs an outage injects one.
"""

import pytest
from stockinfo_plugin import (
    ListedIdentity,
    NotFound,
    NotResponsible,
    PairIdentity,
    Quote,
    QuoteRequest,
    Resolved,
    ResolveRequest,
    Unavailable,
)
from stockinfo_plugin.testing import QuoteContract, ResolverContract

from stockinfo_source_us_example.source import MarketUnreachable, UsExampleSource

# Looked up by hand from the fake vendor, not read back out of it: an expected
# value taken from the thing under test only proves it answers consistently.
KNOWN = "US0378331005"  # Apple, ticker AAPL
ABSENT = "US38259P5089"  # a well-formed US ISIN the fake does not carry
FOREIGN = "DE0007164600"  # SAP — a real paper, but not on this venue

CONFIG = {"api_key": "test-key", "base_url": "https://example.invalid"}


def _source() -> UsExampleSource:
    return UsExampleSource(CONFIG)


class TestUsExampleResolver(ResolverContract):
    """Identity, name and genus for a US listing."""

    responsible = ResolveRequest(isin=KNOWN)
    not_responsible = ResolveRequest(isin=FOREIGN)
    unknown = ResolveRequest(isin=ABSENT)

    def make_source(self) -> UsExampleSource:
        return _source()


class TestUsExampleQuote(QuoteContract):
    """The last price for a listing on this venue."""

    responsible = QuoteRequest(
        identity=ListedIdentity(ticker="AAPL", mic="XNAS", isin=KNOWN)
    )
    not_responsible = QuoteRequest(identity=ListedIdentity(ticker="SAP", mic="XETR"))
    unknown = QuoteRequest(identity=ListedIdentity(ticker="ZZZZ", mic="XNAS"))

    def make_source(self) -> UsExampleSource:
        return _source()


# ── What the suites cannot know ──────────────────────────────────────────────


def test_a_hit_carries_the_venue_and_the_genus() -> None:
    """The three mandatory fields, with the values this source promises.

    The suite checks that they are *present*. Only this example knows that
    `US0378331005` is Apple, on NASDAQ, and a stock.
    """
    answer = _source().resolve(ResolveRequest(isin=KNOWN))

    assert isinstance(answer, Resolved)
    assert answer.identity == ListedIdentity(ticker="AAPL", mic="XNAS", isin=KNOWN)
    assert answer.name == "Apple Inc."
    assert answer.instrument_type == "stock"


def test_a_missing_key_stops_the_source_and_says_so() -> None:
    """Standing still is fine. Standing still without a reason is not.

    The sentence has to name the setting and the way to supply it — an
    operator reads it in `GET /sources` and needs a next action, not a
    diagnosis.
    """
    problem = UsExampleSource({}).configuration_problem()

    assert "api_key" in problem
    assert "US_MARKET_API_KEY" in problem, "the message does not say how to supply it"
    assert UsExampleSource({}).is_configured() is False
    assert _source().is_configured() is True


@pytest.mark.parametrize(
    ("request_", "reason"),
    [
        (ResolveRequest(isin=FOREIGN), "a non-US ISIN is not this venue's business"),
        (ResolveRequest(symbol="AAPL"), "without an ISIN there is nothing to look up"),
    ],
)
def test_not_responsible_is_an_answer_not_a_failure(request_, reason: str) -> None:
    """`NotResponsible` is what lets the next source in the chain try.

    Returning `NotFound` here would be a lie with consequences: the host
    treats it as "this paper does not exist", and a source that knows nothing
    about a paper would have decided that for every source behind it.
    """
    assert isinstance(_source().resolve(request_), NotResponsible), reason


def test_a_preferred_venue_does_not_cancel_responsibility() -> None:
    """**The mistake this example was written wrong for, on the first try.**

    `preferred_mic` is a wish, and it is never empty — the host fills it with
    `XETR` by default. Read as a filter, it makes a source answer
    `NotResponsible` to every request while the code still looks reasonable.

    A resolver may answer with a venue other than the one asked for; the host
    logs the deviation. That is what makes a specialist source useful at all.
    """
    answer = _source().resolve(ResolveRequest(isin=KNOWN, preferred_mic="XETR"))

    assert isinstance(answer, Resolved)
    assert answer.identity.mic == "XNAS"


def test_a_pair_identity_is_not_this_venues_business() -> None:
    """The genus filter is a pre-filter, not the decision.

    `SUPPORTED_KINDS` keeps the host from asking at all; `handles` still has
    to answer correctly when someone does ask.
    """
    answer = _source().fetch_quote(
        QuoteRequest(identity=PairIdentity(base="BTC", quote_currency="EUR"))
    )

    assert isinstance(answer, NotResponsible)


def test_an_outage_is_not_the_same_as_an_unknown_paper() -> None:
    """The distinction the whole result union exists for.

    `NotFound` becomes a 404 and is final. `Unavailable` becomes a 502, keeps
    the stored value, and lets the operator see which source failed — which is
    why the message carries the source name.
    """

    class _Down:
        def lookup(self, isin: str):
            raise MarketUnreachable("HTTP 503")

        def price(self, ticker: str):
            raise MarketUnreachable("HTTP 503")

    source = UsExampleSource(CONFIG, market=_Down())

    outage = source.resolve(ResolveRequest(isin=KNOWN))
    unknown = source.resolve(ResolveRequest(isin=ABSENT))

    assert isinstance(outage, Unavailable)
    assert "us-example" in outage.error, "the operator cannot tell which source failed"
    # Same source, same call, different fact: nothing was reachable either
    # way, so this one is an outage too — the *unknown* case needs a working
    # vendor to be observable at all.
    assert isinstance(unknown, Unavailable)
    assert isinstance(_source().resolve(ResolveRequest(isin=ABSENT)), NotFound)


def test_the_price_carries_currency_and_a_zoned_timestamp() -> None:
    """A price without a currency is a number, and a naive timestamp is wrong.

    Both are mandatory in `Quote`; this checks the values this example
    promises, and that the timestamp did not arrive without a zone.
    """
    answer = _source().fetch_quote(
        QuoteRequest(identity=ListedIdentity(ticker="AAPL", mic="XNAS", isin=KNOWN))
    )

    assert isinstance(answer, Quote)
    assert answer.price == 231.4
    assert answer.currency == "USD"
    assert answer.as_of.tzinfo is not None


def test_the_contract_version_is_written_out_not_inherited() -> None:
    """The loader rejects a class that inherits its version number.

    A version that travels by inheritance follows the host through a contract
    change the plugin has never been adapted to — a barrier that lets everyone
    through is not one.
    """
    assert "api_version" in UsExampleSource.__dict__
