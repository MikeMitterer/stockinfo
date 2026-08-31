"""A complete, installable StockInfo source plugin for one US venue.

This package exists to be *read*. It is the shortest thing that still shows
every step an author has to take: declare a contract version, answer two
roles, take configuration from `sources.yaml`, refuse work honestly, and stay
testable without a network.

It is deliberately **not** a market data provider. `_FakeMarket` below stands
in for a vendor API, and the constructor accepts any object with the same
method — which is the whole point of taking the transport as an argument
instead of importing an HTTP client.

Read `docs/plugin-authors.md` alongside it.
"""

from stockinfo_source_us_example.source import UsExampleSource

__all__ = ["UsExampleSource"]
