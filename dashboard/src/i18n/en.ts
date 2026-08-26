import type { de } from './de'

/** Englischer Message-Katalog — muss dem Schema von `de` entsprechen. */
export const en = {
  /*
   * Wortmarke in zwei Teilen: Farbig ist der Teil, der die App
   * unterscheidet — "Stock" teilen sich alle. Getrennt im Katalog und
   * nicht im Template zerschnitten, sonst wandert die Teilung nicht mit
   * dem Namen.
   */
  app: { brandLead: 'Stock', brandAccent: 'Info' },

  nav: {
    assets: 'Assets',
    exchanges: 'Exchanges',
    environment: 'Environment',
    links: 'API & Links',
    themes: 'Themes',
    analysis: 'Analysis',
    fx: 'FX',
    home: 'Go to start page',
    menu: 'Menu',
    settings: 'Settings',
  },
  toolbar: {
    placeholder: 'ISIN or symbol (e.g. VGWL.DE)',
    add: 'Add',
    refreshing: 'Refreshing…',
    refreshAll: 'Refresh all',
  },
  table: {
    title: 'Assets',
    empty: 'No securities cached yet — add one above by ISIN or symbol.',
    colSymbol: 'Symbol',
    colIsin: 'ISIN',
    colName: 'Name',
    colType: 'Type',
    colPrice: 'Price',
    colTer: 'TER',
    colVola: 'Vola 1y',
    colAccumulating: 'Acc.',
    colPoints: 'Pts.',
    yes: 'Yes',
    no: 'No',
    addIsin: 'Add ISIN',
    isinPlaceholder: 'Enter ISIN',
    isinInvalid: 'invalid ISIN',
    save: 'Save',
    cancel: 'Cancel',
    showJson: 'Show JSON response',
    extraetfProfile: 'extraETF profile',
    yahooFinance: 'Yahoo Finance',
    refresh: 'Refresh',
    remove: 'Delete',
    more: 'more',
    less: 'less',
    details: 'More metrics',
    sortBy: 'Sort by',
    sortNone: 'No sorting',
    sortAsc: 'Ascending',
    sortDesc: 'Descending',
    sortIdle: 'Sort',
  },
  chart: {
    title: 'Price history',
    priceLabel: 'Price',
    loading: 'Loading…',
    empty: 'No history in the selected range.',
    close: 'Close',
    periodChange: 'Change over the period',
    vsStart: 'vs. start',
    ranges: {
      intraday: '1D',
      oneWeek: '1W',
      oneMonth: '1M',
      threeMonths: '3M',
      oneYear: '1Y',
      max: 'Max',
    },
  },
  exchanges: {
    title: 'Exchange suffixes',
    hint:
      'When querying by symbol, the suffix selects the exchange (e.g. {example} = Xetra). ' +
      'The currency always comes from the live quote — London often trades in pence.',
    colSuffix: 'Suffix',
    colExchange: 'Exchange',
    colRegion: 'Region',
    colCurrency: 'Currency',
    noSuffix: '(none)',
    collector: 'collector code',
    default: 'Default',
    penceNote: 'often pence (1/100 GBP)!',
    regions: {
      germany: 'Germany',
      usa: 'USA',
      europe: 'Europe',
      global: 'Global',
    },
  },
  env: {
    title: 'Environment',
    refreshNote:
      'Automatic quote refresh: a background scheduler refreshes the quotes of all cached ' +
      'instruments every {hours} hours (refresh interval, configurable via settings). ' +
      'Independently, the cache TTL applies to every request — quotes older than the TTL ' +
      'are fetched fresh from the source right away.',
    version: 'Version',
    dbPath: 'DB path',
    cacheTtl: 'Cache TTL (h)',
    refreshInterval: 'Refresh interval (h)',
    metadataTtl: 'Metadata TTL (d)',
    defaultExchange: 'Default exchange',
    strictExchange: 'Strict exchange',
    strictExchangeHint:
      'When on (yes): quotes are queried only at the default exchange — if resolution ' +
      'finds nothing there, it returns an error (404) instead of falling back to ' +
      'another exchange.',
    hostPort: 'Host:Port',
    openfigiKeySet: 'OpenFIGI key set',
    yes: 'yes',
    no: 'no',
    sourceNote:
      'These values come from environment variables or the .env file (in Docker: ' +
      'the container environment), read at startup. Template of all keys: {example}.',
  },
  analysis: {
    title: 'Live analysis',
    hint: 'Measures the duration of each fetch step. Triggers real external requests (no cache).',
    pickInstrument: 'Pick instrument',
    orEnter: 'or enter ISIN/symbol',
    placeholder: 'ISIN or symbol (e.g. EUNL.DE)',
    run: 'Analyze',
    running: 'Measuring…',
    colStage: 'Step',
    colSeconds: 'Duration',
    colStatus: 'Status',
    total: 'Total',
    empty: 'No measurement yet — pick an instrument and click “Analyze”.',
  },
  fx: {
    title: 'FX',
    hint: 'Rate 1 base = x quote. Example: EUR→USD ≈ 1.15.',
    amount: 'Amount',
    base: 'Base', quote: 'Quote', swap: 'Swap',
    convert: 'Convert', converting: 'Fetching…',
    quoteTime: 'Quote time', source: 'Source', status: 'Status',
    fresh: 'fresh', stale: 'stale',
  },
  links: {
    title: 'API & Links',
    base: 'Base:',
    apiRoot: 'API root',
    swagger: 'Swagger UI (/docs)',
    openapi: 'OpenAPI (JSON)',
    health: 'Health',
    project: 'Project',
    repo: 'GitHub repo',
    issues: 'Issues',
  },
  themes: {
    title: 'Theme',
    hint: 'Your selection is saved and restored on the next start.',
    active: 'active',
    /*
     * Die Kennungen kommen aus dem Fundament; hier stehen nur die
     * Worte. Fehlt eines, zeigt die Kachel die Kennung — besser als
     * eine leere Beschriftung.
     */
    names: {
      mangolila: 'MangoLila',
      amber: 'Amber',
      petrol: 'Petrol',
      classic: 'Classic',
      macos: 'macOS',
      slate: 'Slate',
      ocean: 'Ocean',
      forest: 'Forest',
      aurora: 'Aurora',
      carbon: 'Carbon',
      paper: 'Paper',
      sepia: 'Sepia',
      meadow: 'Meadow',
      mono: 'Mono',
    },
  },
  language: {
    title: 'Language',
    de: 'German',
    en: 'English',
  },
  settings: {
    title: 'Settings',
    tab: {
      appearance: 'Appearance',
      language: 'Language',
      links: 'API & Links',
      environment: 'Environment',
    },
    language: {
      hint:
        'Without an explicit choice the language follows the browser. A selection ' +
        'here is saved and restored on next start.',
    },
  },
  status: {
    poweredBy: 'powered by',
    version: 'v{version}',
    instruments: 'no instruments | one instrument | {count} instruments',
    ok: 'Online',
    degraded: 'Checking…',
    down: 'Offline',
  },
  json: {
    copyUrl: 'Copy URL',
    copyJson: 'Copy JSON',
    copied: 'copied ✓',
    loading: 'Loading…',
    close: 'Close',
  },
  errors: {
    title: 'Error',
    closesIn: 'closes in {n} s',
    instruments: 'Could not load instruments',
    environment: 'Could not load environment',
    exchanges: 'Exchanges could not be loaded',
    history: 'Could not load history',
    daily: 'Could not load daily history',
    refresh: 'Refresh failed',
    rawQuote: 'Request failed',
    add: 'Adding failed',
    refreshOne: 'Refresh failed',
    remove: 'Delete failed',
    setIsin: 'Could not save ISIN',
    analysis: 'Analysis failed',
    fx: 'Exchange rate could not be loaded',
    overrides: 'Could not save the metrics',
  },
  hints: {
    more: 'More about this →',
    openSetting: 'To the setting →',
    points:
      'Stored price points for this instrument — the depth of the history, not ' +
      'how current it is. How often new ones arrive is set by the refresh interval.',
  },
  overrides: {
    edit: 'Edit',
    clear: 'Clear',
    notSet: 'not set',
    cycleTo: 'Switch to: {value}',
    fromSource: 'Comes from the data source — only missing values can be filled in by hand.',
    markManual: 'Entered by hand — the source has nothing for this instrument.',
    markShadowed:
      'Entered by hand: {value}. Shown is the value from the source — it takes precedence. ' +
      'Your entry stays stored and applies again as soon as the source has nothing.',
    removeOwn: 'Remove your entry',
    fields: {
      provider: 'Provider',
      replication: 'Replication method',
      fundSize: 'Fund size',
      fundDomicile: 'Fund domicile',
      fundCurrency: 'Fund currency',
    },
  },
  drilldown: {
    fetchedAt: 'Source as of',
    source: 'Source',
    explain:
      'Where available, the figures come automatically from justETF. You can only ' +
      'fill in by hand what the source does not provide — it always takes precedence.',
    notEtf:
      'justETF only covers ETFs — this instrument is a stock. The source is never ' +
      'queried for it, so every field can be entered by hand.',
    noIsin:
      'Without an ISIN, justETF cannot be queried. Once an ISIN is entered (the ' +
      'symbol in the row), the source takes over again; until then, every field can be entered by hand.',
    noEuropeanSource:
      'justETF only covers European UCITS ETFs (fund domicile EU, EEA, Switzerland or ' +
      'the UK). This ISIN falls outside that — the source is never queried for it, ' +
      'so every field can be entered by hand.',
    sourceEmpty: 'The source was queried but returned nothing — every field can be entered by hand.',
  },
  confirmDelete: {
    title: 'Delete asset?',
    history: 'No price points stored. | 1 price point will be lost. | {count} price points will be lost.',
    irreversible: 'This cannot be undone.',
  },

  /*
   * The identity migration (T-21 part 3).
   *
   * `reason.*` are the **stable codes** from `app/migration.py` — the server
   * sends the code, the sentence lives here. That is the whole point of
   * "stable reason codes instead of free text": a sentence coming from the
   * backend would be wrong in the second language immediately.
   */
  migration: {
    checking: 'Checking status…',
    starting: 'Service is starting…',

    title: 'The instruments need to be migrated',
    lead:
      'Every instrument gets a unique identity made of ticker and exchange code. ' +
      'Where the old symbol cannot be split beyond doubt, it is left out rather ' +
      'than guessed.',

    balanceMigrating: 'Will be migrated',
    balanceUnchanged: 'Stay unchanged',
    balanceRejected: 'Leave the portfolio',

    removedTitle: 'These instruments leave the portfolio',
    removedNote:
      'They remain in the report and can be added again with a complete identity.',
    lossSummary: 'This drops {quotes} intraday price points and {daily} daily closes.',
    rowLoss: '{quotes} price points, {daily} daily closes',

    backupTitle: 'Back up first',
    backupBody:
      'The migration cannot be undone. Make a copy of the database file before you ' +
      'confirm — afterwards the rows listed above and their prices exist only in ' +
      'the report.',

    confirm: 'Run the migration now',
    confirming: 'Migration running…',

    doneTitle: 'The migration is done',
    doneLead: 'Every instrument now carries a ticker and an exchange code.',
    doneNothingLost: 'No instrument had to be removed.',
    continue: 'Continue to the dashboard',

    startupFailedTitle: 'Migration done, service did not start',
    startupFailedBody:
      'The data has been migrated — that does not change. But the background ' +
      'refresh for new prices did not start, so prices would go stale. Trying ' +
      'again only starts the service, it does not repeat the migration.',
    retry: 'Start the service again',

    downTitle: 'The service does not answer',
    downBody: 'The database is unreachable. Check the server and reload.',

    reason: {
      symbol_without_exchange_suffix:
        'The symbol has no exchange suffix — the trading venue cannot be derived from it alone.',
      unknown_exchange_suffix:
        'The exchange suffix in the symbol is unknown and matches no trading venue.',
      non_canonical_ticker:
        'The ticker does not match the canonical spelling of its trading venue.',
    },
  },
} satisfies typeof de
