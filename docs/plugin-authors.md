# Writing a StockInfo data source

StockInfo can be run anywhere, but it can only be tested against a few
markets. If you sit in one of the others, you will find a problem with your
market in minutes — and you should be able to fix it without touching this
repository.

This guide is for the author of such a plugin. It is not a reference: the
authoritative field lists live in the contract package itself
([`stockinfo_plugin/types.py`](../plugin_api/src/stockinfo_plugin/types.py)
and [`sources.py`](../plugin_api/src/stockinfo_plugin/sources.py)), and every
implemented role contract has a test suite you inherit. Migration tests
also need to check the specific data transformation supplied by the author.

A complete, installable example accompanies this text:
[`plugin_api/examples/us-example/`](../plugin_api/examples/us-example/). It is
short enough to read in one sitting and is built, installed and exercised the
way this guide describes.

## Contents

- [1. The mental model](#1-the-mental-model)
- [2. The contract](#2-the-contract)
- [Data compatibility](#data-compatibility-is-independent-of-package-releases)
- [Plugin data migrations](#plugin-data-migrations)
- [3. The smallest package that works](#3-the-smallest-package-that-works)
- [4. Installing it](#4-installing-it)
- [5. Choosing sources](#5-choosing-sources-sourcesyaml)
- [6. Environment variables](#6-environment-variables)
- [7. Fallback](#7-what-fallback-means-here)
- [8. Troubleshooting](#8-when-it-does-not-work)
- [Further reading](#where-to-go-next)
- [Open detail fields](#open-detail-fields)

---

## 1. The mental model

A plugin offers one or more of **five roles**:

| Role | Question it answers |
|---|---|
| `resolvers` | Which listing is this paper? |
| `quotes` | What does it cost right now? |
| `daily` | What were its closing prices? |
| `etf_meta` | What are its key figures — expense ratio, provider, domicile? |
| `fx` | What is the rate between these two currencies? |

One class may serve several roles. The bundled `yaml-file` source serves all
five from a single file; the US example serves two.

**Being loaded and being used are two different things.** Installing a package
makes a source *available*; `data/sources.yaml` decides which sources are
asked, in which role, and in which order. A source nobody lists is never
called, and it is not an error — it is a configuration.

[↑ Contents](#contents)

---

## 2. The contract

`GET /fields` describes REST fields under `core` and plugin fields under
`plugin_contract`. Their `meaning` descriptions are always in English,
regardless of `Accept-Language` or the dashboard language.

### Identity comes in three shapes

Not every paper trades on an exchange, so there is no single "identity" field:

| Shape | Carries | Used for |
|---|---|---|
| `ListedIdentity` | `ticker` + `mic`, optionally `isin` | shares, ETFs, ETCs, listed bonds |
| `PairIdentity` | `base` + `quote_currency` | native crypto (`BTC`/`EUR`) |
| `IsinOnlyIdentity` | `isin` | OTC bonds, funds without a venue |

A ticker without a venue is ambiguous — `RY` exists in Toronto and in New
York, at different prices in different currencies. A venue without a ticker
says nothing. Both shapes exist because forcing every paper into
`ticker` + `mic` meant a coin needed an invented exchange.

Declare which shapes you serve in `SUPPORTED_KINDS`. The default is
`{"listed"}`, and an **empty** set means "promised nothing" — not "everything".

### Genus is an open list

`stock`, `etf`, `etc`, `fund`, `crypto`, `bond`. Declare yours in
`SUPPORTED_TYPES`. The list grows; an empty set again means you promised
nothing rather than everything, so a genus added next year does not silently
become your responsibility.

### Three fields are mandatory on a hit

`Resolved` requires `identity`, `name` **and** `instrument_type`. None of them
has a default, and that is deliberate: a default value is permission to leave
it out. When they were optional, sources left them out, papers displayed
blank, and — because the genus was missing — the metadata source was never
asked at all. For months, without a message.

If you do not know one of them, return `NotFound`. A later source in the chain
may know better; half an answer takes that chance away, because the chain
stops at the first hit.

### Four ways to say no, and they are not interchangeable

| Answer | Means | The host does |
|---|---|---|
| `NotResponsible` | "not my market" | asks the next source |
| `NotFound` | "my market, and this paper is not in it" | 404 — but keeps asking the chain |
| `Unavailable` | "could not look — network, quota, error" | 502, keeps the stored value |
| `Unsupported` | "recognised, and I do not carry this *kind* of paper" | 400 |

`Unsupported` is the only one that says something about the *paper* rather
than about your source: an index is not a tradeable instrument, and no amount
of retrying will make it one.

The difference between `NotFound` and `Unavailable` is the reason the union
exists. An outage that arrives as "not found" deletes a paper the operator
still owns.

### Normal role methods never raise

`resolve`, `fetch_quote`, `fetch_daily`, `fetch` and `fetch_rate` turn every
failure into `Unavailable` (or `None`, where the role says so). The chain
decides what happens next; a plugin that lets an exception through fails the
contract suite. There is no timeout the host can impose on you — synchronous
Python in the same process cannot be interrupted — so set your own on every
I/O call you make.

### The version is written out, never inherited

```python
class MySource(Resolver):
    name = "my-source"
    api_version = 2      # in your own class body, always
    data_version = 1     # independent of package and API versions
```

The loader rejects a class that does not carry `api_version` in its own
`__dict__`. An inherited number would follow the host through a contract
change your plugin has never been adapted to — a barrier that lets everyone
through is not one.

### Data compatibility is independent of package releases

`data_version` is a positive integer, initially `1`. Increase it only when
stored data needs conversion. Package releases, chain order and profile names
do not trigger a migration. `API_VERSION` remains `2`; the migration API is an
optional addition in `stockinfo-plugin-api` 0.3.0.

StockInfo records versions by source name in `meta.plugin_data_versions`.
Backups carry that record and are compared with active source declarations.
Missing entries in existing databases mean version `1`. A new database starts
with the declared versions and does not run migrations. Removed sources are
not compared; their saved versions remain available if they are reactivated.

### Plugin data migrations

Implement the optional static method on your source class:

```python
from stockinfo_plugin import MetadataSource, MigrationContext

class Example(MetadataSource):
    name = "example"
    api_version = 2
    data_version = 2

    @staticmethod
    def migrate(context: MigrationContext, from_version: int, to_version: int) -> None:
        if (from_version, to_version) != (1, 2):
            raise ValueError("Unsupported data version")
        context.execute(
            "UPDATE meta SET value=? WHERE key=? AND value=?",
            ("new", "example-data", "old"),
        )
```

The source still implements its normal role methods. The executable migration
example lives in [`plugin_api/examples/migration.py`](../plugin_api/examples/migration.py).
It changes one example-owned metadata value and leaves other data and the
shared schema alone. Test your own transformation against mixed data.

`context.execute(statement, parameters=())` runs one SQL statement. Bind values
through parameters. SELECT results are a list of dictionaries keyed by column
name; statements without result rows return an empty list. The context exposes
no cursor, connection or commit method. StockInfo owns the transaction.

On a version increase, StockInfo creates a normal backup before calling the
function. It commits the data changes and new version together. An exception
or process crash rolls back that plugin's transaction; earlier successful
plugin migrations stay committed. A restart skips their completed versions.
Failed backups prevent the function from running. Missing functions,
unsupported origins and downgrades keep normal operation blocked; the server
log names the source, stored version, target and error. With an unchanged
version no migration function is needed.

The author selects the right data and supports or rejects version jumps such
as `1 → 3`. StockInfo does not search for intermediate migrations. Do not alter
the shared schema, start or end transactions, open another write connection,
write external files or call the network. Those changes would escape the host's
rollback. Plugins remain trusted Python code; this is not a sandbox.

Migrations run before business requests and scheduled refreshes. An outstanding
identity-migration confirmation comes first. There is no additional migration
dialog; `/ready` and `/operational` report a failed start as degraded.

---

## 3. The smallest package that works

```
my-source/
├── pyproject.toml
├── src/
│   └── stockinfo_source_my_market/
│       ├── __init__.py
│       └── source.py
└── tests/
    └── test_my_source.py
```

`pyproject.toml`, in full:

```toml
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[project]
name = "stockinfo-source-my-market"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = ["stockinfo-plugin-api>=0.2"]

[project.optional-dependencies]
testing = ["stockinfo-plugin-api[testing]>=0.2"]

[project.entry-points."stockinfo.sources"]
my-source = "stockinfo_source_my_market:MySource"

[tool.setuptools.packages.find]
where = ["src"]
```

**What an operator writes in `sources.yaml` is your class's `name`
attribute** — not the entry-point key. The host reads the key only to find the
class, then takes `MySource.name` from there. Keep the two identical anyway;
a package whose entry point says one thing and whose class says another is a
puzzle for whoever configures it.

Announce a source class **once**. The host derives all of its roles from the
base classes it inherits; repeating the same class under another entry-point
key adds no role. It only registers the same class `name` twice, which the
loader reports as a duplicate before keeping the last registration.

Since a role gets its own instance, keep per-request state out of `self` — or
accept that it is not shared with your other role.

Depend on the contract package and nothing of the host. A plugin that reaches
into StockInfo's internals is a fork that happens to install.

### Take your transport as an argument

```python
def __init__(self, config=None, market=None):
    super().__init__(config)
    self._api_key = str(self._config.get("api_key") or "").strip()
    self._market = market or _RealClient(self._api_key)
```

This one line is what lets your tests run without a network and without a key.
The host only ever passes `config`; the second parameter is for you.

### Say why you cannot work

```python
def configuration_problem(self) -> str:
    if not self._api_key:
        return ("api_key is missing — set providers.my-source.api_key in "
                "sources.yaml, e.g. to ${MY_MARKET_API_KEY}")
    return ""
```

The sentence is read by someone who did not write your plugin, in
`GET /sources`. "Not configured" tells them something is wrong and nothing
about what to do. Name the setting and the way to supply it.

### Declare venues and coverage

The optional declarations below require `stockinfo-plugin-api>=0.3` (the
next additive release; this checkout already contains them). Existing API-2
plugins can omit them; their coverage is shown as **unspecified**, not absent.
`data_version` does not change for these descriptive additions.

```python
from types import MappingProxyType
from stockinfo_plugin import ExchangeSpec, MicCoverage

# Class attributes on your source:
EXCHANGES = (ExchangeSpec("XBUD", "Budapest", "europe", "HUF"),)
MIC_SUPPORT = MappingProxyType({
    "quotes": MicCoverage(("XBUD",), scope="market"),
    "daily": MicCoverage((), scope="market"),
})
```

Declare only roles your class implements. An omitted role means unknown;
an empty MIC tuple explicitly promises no coverage. Use `inventory` for a
file or limited inventory; `market` describes general market coverage, not a
guarantee that every request succeeds. FX has no MIC declaration.

`EXCHANGES` adds venues missing from the core catalog. Core MICs such as
`XNAS` belong in `MIC_SUPPORT`; do not redefine their names or aliases.

For a file-backed source, override the additive class method
`get_mic_support(config)` (available with the exchange contract in 0.3).
It receives only your source's configuration and returns the same mapping
of roles to `MicCoverage`. The default returns `MIC_SUPPORT`. Do not make
network requests here: this hook is read again when `/exchanges` is requested.
The host also reads it for `POST /instruments/intake`, used by the UI when
adding assets. Listings require a declared MIC in a usable `quotes` source;
metadata-only, missing, or invalid coverage does not permit admission.
Symbol inputs are checked before querying sources; ISIN inputs after resolution
and before fetching a quote or writing the asset. Cached listings are checked
too. Pair and ISIN-only identities have no MIC requirement. Coverage still
does not guarantee that the source knows the requested security.
Raise on unreadable/invalid inventory; never return an old coverage snapshot.
The host validates current declarations and displays failed coverage as unknown.
For contract tests, `make_source()` must provide valid inventory/configuration
so that the current coverage hook can run successfully. Constructors without
the base configuration storage are tested with an empty configuration mapping.

The bundled YAML source reports only MICs actually present in its file:
resolver coverage for listed identities, quotes for a price or history,
history for stored closes, and metadata for stored fields. Pair and ISIN-only
instruments do not create exchange coverage. Its `inventory` scope means
**only stored instruments**, not the entire market. Static `EXCHANGES` is
still required when inventory references a venue unknown to the host.
Removing an online source from the configured chains removes its coverage;
a YAML-only profile never inherits online coverage. The bundled online
sources declare their known MIC universe explicitly; a newly added plugin
venue does not silently extend that universe. Instrument type and fund
domicile restrictions still apply to individual metadata requests.

New venues use their MIC as the app suffix (`DEMO.XBUD`). Vendor symbol
translation remains inside your plugin. Conflicting definitions are rejected
by the host; identical declarations may coexist. Removing the plugin removes
its catalog contribution without rewriting stored assets.

Every inherited role contract validates declaration structure. Catalog
conflicts need a host run. The bundled US example declares inventory coverage
for both its roles using only public imports. Run it from the repository root
against the checkout, without waiting for the package release:

```bash
PYTHONPATH=plugin_api/src:plugin_api/examples/us-example/src .venv/bin/python -m pytest -q plugin_api/examples/us-example/tests
```

### Inherit the tests

```python
from stockinfo_plugin.testing import QuoteContract, ResolverContract

class TestMyResolver(ResolverContract):
    responsible = ResolveRequest(isin="US0378331005")
    not_responsible = ResolveRequest(isin="DE0007164600")
    unknown = ResolveRequest(isin="US38259P5089")

    def make_source(self):
        return MySource({"api_key": "test"})
```

Six lines buy you the whole role suite: that you never
raise, that you say why you stand still, that an unrelated request costs
nothing, that a hit carries every mandatory field, that no mutable state lives
on the class.

Write the three requests, inherit the rest, then add the handful of facts only
you know — that this ISIN is Apple, on NASDAQ, and a stock.

Run them:

```bash
python -m pip install -e ".[testing]"
python -m pytest -q
```

And build the wheel you hand around:

```bash
python -m pip wheel --no-deps -w dist .
```

[↑ Contents](#contents)

---

## 4. Installing it

**While developing**, drop a `.py` file into `data/plugins/` and export
`SOURCES`:

```python
SOURCES = [MySource]
```

Restart, and the name appears in `GET /sources`. Files starting with `_` are
skipped.

**To hand it around**, build a wheel and pin it in `data/sources.yaml`:

```yaml
plugins:
  packages:
    - stockinfo-source-my-market==0.1.0
```

On start-up the app installs the list into `data/plugin-env/<hash>` and adds
that directory to the import path. Three rules apply:

* **Pinned versions only.** The directory name is a checksum over the list;
  without `==`, the same hash would point at a different package tomorrow.
  `>=`, a bare name, a git URL or a pip option are refused by name.
* **Wheels only.** Otherwise build tools would have to ship in the image, and
  a `setup.py` would run as code on start-up.
* **The contract stays the host's.** A constraint prevents a plugin from
  pulling a different version of `stockinfo-plugin-api` into the directory,
  where it would sit in front on the import path and win.

Same list ⇒ same directory ⇒ **no installation** on the next start. A changed
list means a new directory; the old one stays, so rolling back is a one-line
edit.

Why not plain `pip install`? In the official container, `site-packages` lives
in the *image* and is gone after the next `docker pull`. `/data` is the volume
and survives the update.

> **Nothing is ever discovered.** The app installs exactly the packages
> listed under `plugins.packages` and looks for nothing else — no registry
> scan, no suggestions, no updates. A plugin runs with the app's permissions,
> so what gets installed stays a line somebody typed.

[↑ Contents](#contents)

---

## 5. Choosing sources: `sources.yaml`

```yaml
plugins:
  packages:
    - stockinfo-source-us-example==0.1.0

resolvers: [us-example, openfigi, yahoo-search, yaml-file]
etf_meta:  [justetf, yfinance, yaml-file]
quotes:    [us-example, yfinance, yaml-file]
daily:     [yfinance, yaml-file]
fx:        [yfinance, yaml-file]

providers:
  us-example:
    api_key: ${US_MARKET_API_KEY}
    base_url: ${US_MARKET_BASE_URL}
  openfigi:
    api_key: ${OPENFIGI_API_KEY}
  yaml-file:
    path: /data/assets.yaml
```

Three separate decisions live in that file, and it helps to keep them apart:

1. **What is installed** — `plugins.packages`.
2. **What is used, and in which role** — the five role lines.
3. **How each source is configured** — `providers`.

The order is your statement and is never re-sorted. `GET /sources` afterwards
shows what actually applies, including sources that **cannot** work and why.

[↑ Contents](#contents)

---

## 6. Environment variables

`${NAME}` in a value is replaced by the process environment — exactly the
value, no shell, no defaults, no partial substitution beyond the placeholder.
A missing variable leaves the source unconfigured, which `GET /sources`
reports as such rather than starting with an empty key.

The key never goes into the YAML file or into version control.

**Local development** — a `.env` beside the app:

```bash
US_MARKET_API_KEY=sk-your-key-here
```

**Docker Compose**:

```yaml
services:
  stockinfo:
    image: mikemitterer/stockinfo:latest
    environment:
      - US_MARKET_API_KEY=${US_MARKET_API_KEY}   # from the host's .env
    volumes:
      - ./data:/data
```

**Unraid** — add a variable in the template editor:

```
Config Type: Variable
Name:        US_MARKET_API_KEY
Key:         US_MARKET_API_KEY
Value:       sk-your-key-here
```

[↑ Contents](#contents)

---

## 7. What "fallback" means here

Every role asks its chain **in the written order** and takes the first solid
answer:

```yaml
quotes: [yfinance, yaml-file]
```

Online wins where it has a price; the hand-maintained file steps in only where
none arrives — for a bond, say, that no online source carries. The file never
overwrites an online hit.

Two details worth knowing:

* For `daily`, an **empty** series is an answer — "looked, nothing in this
  period" — and ends the chain. Only "could not look" falls through.
* `GET /fx` names the source that **delivered** the rate, not the one that
  happens to be first in the list.

And one that costs an hour if you miss it: **a file source has to appear in
`resolvers` too.** A paper no online source knows cannot be added at all —
the intake fails at resolution, long before anyone asks for a price.

[↑ Contents](#contents)

---

## 8. When it does not work

| Symptom | Cause | Check |
|---|---|---|
| Name missing from `GET /sources` | package not installed, or entry point not declared | `plugins_loaded` in the log lists what was found |
| `'my-source' is not a known source` | the name in the role line differs from the entry-point name | compare `sources.yaml` against `pyproject.toml` |
| Loaded but skipped | wrong `api_version`, or it is not in its own class body | the loader logs the rejection with the reason |
| `configured: false` | `configuration_problem()` spoke | the reason is in the `/sources` entry |
| Pinned package refused | `>=`, a bare name or a git URL in `plugins.packages` | pin with `==` |
| Installation fails | not available as a wheel, or the index cannot be reached | `plugin_env_install_failed` in the log carries pip's output |
| Never asked for a paper | `SUPPORTED_KINDS` / `SUPPORTED_TYPES` do not cover it, or `handles` says no | both are pre-filters; `handles` is the decision |

The one that catches almost everyone: **`preferred_mic` is a wish, not a
filter, and it is never empty** — the host fills it with `XETR` by default.
Read as a filter, it makes your source answer `NotResponsible` to everything
while the code still looks perfectly reasonable.

[↑ Contents](#contents)

---

## Where to go next

* [`plugin_api/examples/us-example/`](../plugin_api/examples/us-example/) — the
  package this guide describes, with its tests.
* [`plugin_api/examples/yaml_file.py`](../plugin_api/examples/yaml_file.py) —
  one source serving all five roles from a file.
* [`docs/plugins.md`](plugins.md) — the operator's view, in German.
* [`plugin_api/src/stockinfo_plugin/`](../plugin_api/src/stockinfo_plugin/) —
  the implemented contract, migration context and role tests.

[↑ Contents](#contents)

## Open detail fields

A metadata source declares its fields through `FIELDS`. The host persists all
valid declared readings, including fields that the dashboard has never seen.
The eight existing metrics retain their canonical names; new keys are exposed
as `<source.name>.<field.name>` (for example `risk-demo.score`). Incompatible
canonical types or units cause the source to be rejected when its chain is built.

```python
FIELDS = (
    FieldSpec("score", kind="number", label_en="Risk score",
              label_de="Risikoscore", plausible=(0, 100)),
    FieldSpec("verified", kind="boolean", label_en="Verified",
              overridable=False),
    FieldSpec("provider", label_en="Fund provider",
              instrument_types=frozenset({"etf", "fund"})),
)
```

`instrument_types=None` inherits `SUPPORTED_TYPES`. An explicit subset restricts
one field; an empty subset makes it applicable to no instrument. This lets a
source serve both funds and crypto without advertising fund fields for coins.
`SUPPORTED_KINDS` also limits applicability. The dashboard uses the returned
schema and instrument details to choose its fields and editors.

`GET /fields` returns the configured, validated detail schema, including
`name`, `kind`, `unit`, labels, `overridable`, `sources`, `scopes`, numeric bounds
and `currency_required`. Its integer `details_version` increases whenever that
schema changes, including removals. Temporary source health does not change
the schema. `generation_id` and its endpoint/header are not implemented;
do not rely on them for cache invalidation today. Their planned status is
documented under `planned.generation_runtime` in the
[core contract artifact](../contract/core-contract.json); they are not part
of T-25's migration completion criteria.

Both quote responses and `GET /instruments` carry a `details` map. Each value
includes `value`, `unit`, `currency`, `origin`, `source`, `as_of`, `shadowed`,
`manual_value` and `manual_currency`. Source priority is applied per field;
`0` and `false` are values, not missing data. Existing top-level metrics remain
compatibility projections of the same stored values.

Use `PATCH /instruments/by-id/{listing_id}/details` with a partial object:

```json
{"risk-demo.score": {"value": 0}}
```

An omitted field is unchanged; `{"value": null}` removes only its manual
value. The server rejects unknown, inapplicable and read-only fields with
HTTP 422 and validates the entire patch before writing. Absolute amounts
require a three-letter uppercase currency code. Provider values take
precedence; a retained manual value is reported as shadowed when applicable.

[↑ Contents](#contents)
