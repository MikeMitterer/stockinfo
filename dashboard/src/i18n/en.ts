import type { de } from './de'

/** Englischer Message-Katalog — muss dem Schema von `de` entsprechen. */
/** Die fünf Rollen der Quellenkette — einmal benannt, siehe die deutsche Fassung. */
const roles = {
  resolvers: 'Resolution',
  quotes: 'Quote',
  daily: 'Daily series',
  etf_meta: 'Metadata',
  fx: 'FX',
}

export const en = {
  details: {
    loading: 'Loading fields…',
    editField: 'Edit {field}',
    currency: 'Currency',
    shadowed: 'The source takes precedence over your value {value}.',
    loadFailed: 'Could not load field definitions.',
    empty: 'No detail fields are declared for this instrument.',
  },
  /*
   * Wortmarke in zwei Teilen: Farbig ist der Teil, der die App
   * unterscheidet — "Stock" teilen sich alle. Getrennt im Katalog und
   * nicht im Template zerschnitten, sonst wandert die Teilung nicht mit
   * dem Namen.
   */
  app: { brandLead: 'Stock', brandAccent: 'Info' },

  /* The placeholder for an empty cell — see the German file. */
  common: { noValue: '-' },

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
    toggleDetails: 'Show/hide details',
    colIsin: 'ISIN',
    /* Die eine Erklärung für beide Darstellungsformen — siehe die deutsche Fassung. */
    noIsinReason:
      'A hyphen means there is no ISIN: a currency pair carries none. That is the shape of the instrument, not a gap.',
    noSymbolReason:
      'A hyphen means there is no exchange symbol: some instruments — an OTC bond, say — are identified by their ISIN alone.',
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
    pluginHint: 'Plugins can add further trading venues and MICs. See the {guide} to learn how.',
    pluginGuide: 'plugin author guide',
    title: 'Trading venues',
    hint: 'Use the ticker and app suffix, e.g. {alias}. You can also use the MIC: {mic}. The YAML file only provides quotes for stored securities.',
    colSuffix: 'App suffix',
    colExchange: 'Trading venue',
    default: 'Default',
    penceNote: 'London often trades in pence (1/100 GBP).',
    mic: 'MIC',
    support: 'Quote source',
    reload: 'Reload',
    search: 'Search MIC, venue or source',
    empty: 'No trading venues found.',
    unspecified: 'Unspecified',
    noSupport: 'Not covered by the current profile',
    unspecifiedHint: 'Exchange coverage is unknown for these quote sources.',
    yamlRefreshInfo: 'After adding quotes for more trading venues to the YAML file, click “Reload”. The newly covered MICs will then appear.',
    sourceInfo: 'About the quote sources',
    marketInfo: 'This source offers quotes for the assigned trading venues. Quotes may be missing for individual securities.',
    inventoryInfo: 'This source only supplies stored prices or the latest recorded closing price. This does not imply general exchange coverage. The YAML-only profile makes no online requests.',
    showUnavailable: 'Show exchanges not covered',
    regions: {
      germany: 'Germany',
      usa: 'USA',
      europe: 'Europe',
      global: 'Global',
    },
    yamlFile: 'YAML file',
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
    /* „Externe Abfragen" stand hier zu Unrecht — siehe die deutsche Fassung. */
    hint: 'Measures the configured source chain role by role — bypassing the cache.',
    pickInstrument: 'Pick instrument',
    orEnter: 'or enter ISIN/symbol',
    placeholder: 'ISIN or symbol (e.g. EUNL.DE)',
    run: 'Analyze',
    running: 'Measuring…',
    rows: 'no rows | 1 row | {count} rows',
    unsupported: 'instrument type {type} is not supported',
    /* Rolle übersetzt, Quellenname roh — siehe die deutsche Fassung. */
    colRole: 'Role',
    colSource: 'Source',
    role: roles,
    status: {
      ok: 'answered',
      empty: 'nothing',
      error: 'error',
      skipped: 'not asked',
    },
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
  roles,
  backups: {
    title: 'Database backups',
    hint:
      '{keep} backups are kept; the oldest gives way when the next one is ' +
      'created. Backups are taken on demand, not on a schedule.',
    create: 'Back up now',
    restore: 'Restore',
    empty: 'No backup yet.',
    colCreated: 'Created',
    colSize: 'Size',
    colFit: 'Fit',
    fits: 'matches the running source setup',
    reason: {
      backup_schema_too_new: 'Schema {version} is newer than this app ({app})',
      backup_fingerprint_mismatch: 'Manifest and database name different fingerprints',
      backup_data_version_differ: 'Incompatible plugin data version',
      backup_sources_differ: 'Different source setup',
      line: '{field}: there {theirs}, here {ours}',
      packages: 'Packages',
      none: '—',
    },
    /* Der Neustart steht vor der Entscheidung — siehe die deutsche Fassung. */
    confirmTitle: 'Restore?',
    confirmBody: '{name} will be applied on the next start.',
    confirmRestart:
      'This requires restarting the app. Until then the current data keeps ' +
      'running unchanged.',
    confirmYes: 'Schedule',
    confirmNo: 'Cancel',
    forceLabel: 'Restore anyway — {reason}',
    pending: 'A restart is pending: {name} will be applied on the next start.',
    failed: 'Restoring failed: {reason}. It will not be retried.',
  },
  settings: {
    title: 'Settings',
    tab: {
      appearance: 'Appearance',
      language: 'Language',
      links: 'API & Links',
      backups: 'Backups',
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
    /* Which role this names — see the German file. */
    quoteChain: 'Quotes: {chain}',
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
    addIdentifier: 'Adding “{identifier}” failed',
    refreshOne: 'Refresh failed',
    remove: 'Delete failed',
    setIsin: 'Could not save ISIN',
    analysis: 'Analysis failed',
    fx: 'Exchange rate could not be loaded',
    overrides: 'Could not save the metrics',
    backupsLoad: 'Could not load the backups',
    backupCreate: 'Backup failed',
    backupRestore: 'Restore failed',

    /* The reason behind the category above, keyed by `ErrorDetail.code`. */
    reason: {
      /* No text names a source: which ones answer is up to `sources.yaml`. */
      instrument_not_found:
        'None of the configured sources found a security for {identifier}.',
      unsupported_instrument_type:
        '{symbol} is a {instrument_type} — StockInfo does not currently ' +
        'accept this instrument type.',
      quote_currency_mismatch:
        '{symbol} is quoted in {expected} but the source delivered ' +
        '{delivered} — that is a different instrument.',
      identifier_empty: 'Nothing was entered.',
      exchange_not_covered: 'No quote source is available for {mic} in the current profile. See “Exchanges” for available venues.',
      identifier_unknown_form:
        '{identifier} is neither an ISIN nor a symbol with an exchange suffix.',
      /* `Unavailable` does not say the security exists — nobody could check. */
      quote_unavailable:
        'No source could look it up: {identifier}. Whether the security exists ' +
        'is therefore open.',
      /* Die vier paarweisen Kennungen — siehe die deutsche Fassung. */
      daily_series_not_found:
        'None of the configured sources carries a price history for {identifier}.',
      daily_source_unavailable:
        'The price history for {identifier} could not be fetched — at least ' +
        'one source did not answer.',
      fx_pair_not_found:
        'None of the configured sources carries the rate {base}/{quote}.',
      fx_source_unavailable:
        'The rate {base}/{quote} could not be fetched — at least one source ' +
        'did not answer.',
      invalid_currency_code:
        '{base} and {quote} must be three-letter currency codes.',
      invalid_isin_format: '{isin} is not shaped like an ISIN.',
      /*
       * The only identity code that can arise here alone. The other three —
       * missing, unknown and non-canonical suffix — are shared with the
       * migration report and read from `migration.reason` (T-58).
       */
      ambiguous_exchange_suffix:
        'The exchange suffix matches more than one venue — the input does ' +
        'not say which one is meant.',
      /* Fallback for a code this UI does not know — from a newer backend or a plugin. */
      unknown: 'The source reports an error this interface does not know: {code}.',
    },
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
    /* No text names a source: which one answers is up to `sources.yaml`. */
    explain:
      'The configured source provides the figures where it has them. You can only ' +
      'fill in by hand what it does not provide — it always takes precedence.',
    notEtf:
      'Figures are only fetched for ETFs — this instrument is not one. The source is ' +
      'never queried for it, so every field can be entered by hand.',
    noIsin:
      'Without an ISIN, no metrics source is queried. Once an ISIN is entered (the ' +
      'symbol in the row), the source takes over again; until then, every field can be entered by hand.',
    /* One text for two cases — only the backend knows which one applies. */
    nothingProvided:
      'The configured metrics source provided nothing for this instrument — every ' +
      'field can be entered by hand.',
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
      'The migration cannot be undone. Back up the database before you confirm — ' +
      'afterwards the rows listed above and their prices exist only in the report.',
    backupNow: 'Create backup now',
    backingUp: 'Backing up…',
    backupDone: 'Backed up. The copy is with your backups.',

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
    retrying: 'Starting the service…',

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
