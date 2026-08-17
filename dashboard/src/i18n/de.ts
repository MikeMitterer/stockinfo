/** Deutscher Message-Katalog — Schema-Quelle für alle weiteren Sprachen. */
export const de = {
  /*
   * Wortmarke in zwei Teilen: Farbig ist der Teil, der die App
   * unterscheidet — "Stock" teilen sich alle. Getrennt im Katalog und
   * nicht im Template zerschnitten, sonst wandert die Teilung nicht mit
   * dem Namen.
   */
  app: { brandLead: 'Stock', brandAccent: 'Info' },

  nav: {
    assets: 'Assets',
    exchanges: 'Börsen',
    environment: 'Environment',
    links: 'API & Links',
    themes: 'Themes',
    analysis: 'Analyse',
    fx: 'Devisen',
    home: 'Zur Startseite',
    menu: 'Menü',
    settings: 'Einstellungen',
  },
  toolbar: {
    placeholder: 'ISIN oder Symbol (z.B. VGWL.DE)',
    add: 'Hinzufügen',
    refreshing: 'Aktualisiere…',
    refreshAll: 'Alle aktualisieren',
  },
  table: {
    title: 'Assets',
    empty: 'Noch keine Wertpapiere gecacht — oben per ISIN oder Symbol hinzufügen.',
    colSymbol: 'Symbol',
    colIsin: 'ISIN',
    colName: 'Name',
    colType: 'Typ',
    colPrice: 'Kurs',
    colTer: 'TER',
    colVola: 'Vola',
    colAccumulating: 'Thes.',
    colPoints: 'Pkt.',
    yes: 'Ja',
    no: 'Nein',
    addIsin: 'ISIN nachtragen',
    isinPlaceholder: 'ISIN eintragen',
    isinInvalid: 'ungültige ISIN',
    save: 'Speichern',
    cancel: 'Abbrechen',
    showJson: 'JSON-Abfrage anzeigen',
    extraetfProfile: 'extraETF-Profil',
    yahooFinance: 'Yahoo Finance',
    refresh: 'Aktualisieren',
    remove: 'Löschen',
    more: 'mehr',
    less: 'weniger',
    details: 'Weitere Kennzahlen',
    sortBy: 'Sortieren nach',
    sortNone: 'Ohne Sortierung',
    sortAsc: 'Aufsteigend',
    sortDesc: 'Absteigend',
    sortIdle: 'Sortieren',
  },
  chart: {
    title: 'Kurshistorie',
    priceLabel: 'Kurs',
    loading: 'Lade…',
    empty: 'Keine Historie im gewählten Zeitraum.',
    close: 'Schließen',
    periodChange: 'Veränderung über den Zeitraum',
    vsStart: 'ggü. Start',
    ranges: {
      intraday: '1T',
      oneWeek: '1W',
      oneMonth: '1M',
      threeMonths: '3M',
      oneYear: '1J',
      max: 'Max',
    },
  },
  exchanges: {
    title: 'Börsen-Suffixe',
    hint:
      'Bei der Abfrage per Symbol bestimmt das Suffix die Börse (z.B. {example} = Xetra). ' +
      'Die Währung kommt immer aus dem Live-Kurs — London notiert häufig in Pence.',
    colSuffix: 'Suffix',
    colExchange: 'Börse',
    colRegion: 'Region',
    colCurrency: 'Währung',
    noSuffix: '(ohne)',
    default: 'Standard',
    penceNote: 'oft Pence (1/100 GBP)!',
    regions: {
      germany: 'Deutschland',
      usa: 'USA',
      europe: 'Europa',
      global: 'Global',
    },
  },
  env: {
    title: 'Environment',
    refreshNote:
      'Automatischer Kurs-Update: Ein Hintergrund-Scheduler aktualisiert die Kurse aller ' +
      'gecachten Instrumente alle {hours} Stunden (Refresh-Intervall, per Setting änderbar). ' +
      'Unabhängig davon gilt bei jeder Abfrage die Cache-TTL — ist ein Kurs älter, wird er ' +
      'direkt frisch von der Quelle geholt.',
    version: 'Version',
    dbPath: 'DB-Pfad',
    cacheTtl: 'Cache-TTL (h)',
    refreshInterval: 'Refresh-Intervall (h)',
    metadataTtl: 'Metadaten-TTL (d)',
    defaultExchange: 'Default-Börse',
    strictExchange: 'Strikte Börse',
    strictExchangeHint:
      'Aktiv (ja): Kurse werden nur an der Default-Börse abgefragt — findet die ' +
      'Auflösung dort nichts, gibt es einen Fehler (404) statt Ausweichen auf eine ' +
      'andere Börse.',
    hostPort: 'Host:Port',
    openfigiKeySet: 'OpenFIGI-Key gesetzt',
    yes: 'ja',
    no: 'nein',
    sourceNote:
      'Diese Werte stammen aus Umgebungsvariablen bzw. der .env-Datei (im ' +
      'Docker-Container: Container-Environment) und werden beim Start gelesen. ' +
      'Vorlage aller Schlüssel: {example}.',
  },
  analysis: {
    title: 'Live-Analyse',
    hint: 'Misst die Dauer der einzelnen Abfrage-Schritte. Löst echte externe Abfragen aus (kein Cache).',
    pickInstrument: 'Instrument wählen',
    orEnter: 'oder ISIN/Symbol eingeben',
    placeholder: 'ISIN oder Symbol (z.B. EUNL.DE)',
    run: 'Analysieren',
    running: 'Messe…',
    colStage: 'Schritt',
    colSeconds: 'Dauer',
    colStatus: 'Status',
    total: 'Gesamt',
    empty: 'Noch keine Messung — Instrument wählen und „Analysieren" klicken.',
  },
  fx: {
    title: 'Devisen',
    hint: 'Wechselkurs 1 Basis = x Ziel. Beispiel: EUR→USD ≈ 1,15.',
    amount: 'Betrag',
    base: 'Basiswährung', quote: 'Zielwährung', swap: 'Tauschen',
    convert: 'Umrechnen', converting: 'Hole…',
    quoteTime: 'Kurszeit', source: 'Quelle', status: 'Status',
    fresh: 'aktuell', stale: 'veraltet',
  },
  links: {
    title: 'API & Links',
    base: 'Basis:',
    apiRoot: 'API-Wurzel',
    swagger: 'Swagger-UI (/docs)',
    openapi: 'OpenAPI (JSON)',
    health: 'Health',
    project: 'Projekt',
    repo: 'GitHub-Repo',
    issues: 'Issues',
  },
  themes: {
    title: 'Theme',
    hint: 'Auswahl wird gespeichert und beim nächsten Start wiederhergestellt.',
    active: 'aktiv',
    /*
     * Die Kennungen kommen aus dem Fundament; hier stehen nur die
     * Worte. Fehlt eines, zeigt die Kachel die Kennung — besser als
     * eine leere Beschriftung.
     */
    names: {
      mangolila: 'MangoLila',
      amber: 'Bernstein',
      petrol: 'Petrol',
      classic: 'Klassisch',
      macos: 'macOS',
      slate: 'Schiefer',
      ocean: 'Ozean',
      forest: 'Wald',
      aurora: 'Aurora',
      carbon: 'Karbon',
      paper: 'Papier',
      sepia: 'Sepia',
      meadow: 'Wiese',
      mono: 'Mono',
    },
  },
  language: {
    title: 'Sprache',
    de: 'Deutsch',
    en: 'Englisch',
  },
  settings: {
    title: 'Einstellungen',
    tab: {
      appearance: 'Darstellung',
      language: 'Sprache',
      links: 'API & Links',
      environment: 'Environment',
    },
    language: {
      hint:
        'Ohne eigene Wahl folgt die Sprache dem Browser. Eine Auswahl hier wird ' +
        'gespeichert und beim nächsten Start wiederhergestellt.',
    },
  },
  status: {
    poweredBy: 'powered by',
    version: 'v{version}',
    instruments: 'keine Papiere | ein Papier | {count} Papiere',
    ok: 'Online',
    degraded: 'Prüfe…',
    down: 'Offline',
  },
  json: {
    copyUrl: 'URL kopieren',
    copyJson: 'JSON kopieren',
    copied: 'kopiert ✓',
    loading: 'Lade…',
    close: 'Schließen',
  },
  errors: {
    // Überschrift des Fehler-Toasts; der Text darunter ist die Meldung selbst.
    title: 'Fehler',
    /*
     * Zähler im Toast. Heute unsichtbar — die Anzeigedauer steht fest auf 0,
     * Fehler bleiben also stehen. Der Eintrag steht trotzdem hier, weil das
     * Fundament die Beschriftung verlangt statt sie fest zu verdrahten: Es hat
     * keinen Katalog, und ein deutsches Wort darin wäre in `en` sofort falsch.
     */
    closesIn: 'schließt in {n} s',
    instruments: 'Instrumente konnten nicht geladen werden',
    environment: 'Environment konnte nicht geladen werden',
    exchanges: 'Börsen konnten nicht geladen werden',
    history: 'Historie konnte nicht geladen werden',
    daily: 'Tageshistorie konnte nicht geladen werden',
    refresh: 'Refresh fehlgeschlagen',
    rawQuote: 'Abfrage fehlgeschlagen',
    add: 'Hinzufügen fehlgeschlagen',
    refreshOne: 'Aktualisieren fehlgeschlagen',
    remove: 'Löschen fehlgeschlagen',
    setIsin: 'ISIN konnte nicht gespeichert werden',
    analysis: 'Analyse fehlgeschlagen',
    fx: 'Wechselkurs konnte nicht geladen werden',
    overrides: 'Kennzahlen konnten nicht gespeichert werden',
  },
  /*
   * Kurzerklärungen am Begriff — zwei, drei Sätze dort, wo die Frage entsteht.
   * `more` und `openSetting` sind die beiden Verweise darin.
   */
  hints: {
    more: 'Mehr dazu →',
    openSetting: 'Zur Einstellung →',
    points:
      'Gespeicherte Kurspunkte dieses Papiers — die Tiefe der Historie, nicht ' +
      'die Aktualität. Wie oft neue dazukommen, bestimmt das Refresh-Intervall.',
  },
  overrides: {
    edit: 'Bearbeiten',
    clear: 'Leeren',
    notSet: 'nicht gesetzt',
    cycleTo: 'Umschalten auf: {value}',
    markManual: 'Von Hand eingetragen — die Quelle liefert für dieses Papier nichts.',
    markShadowed:
      'Von Hand eingetragen: {value}. Angezeigt wird der Wert der Quelle — sie hat Vorrang. ' +
      'Die Eingabe bleibt gespeichert und greift wieder, sobald die Quelle nichts liefert.',
  },
  confirmDelete: {
    title: 'Asset löschen?',
    history: 'Keine Kurspunkte gespeichert. | 1 Kurspunkt geht verloren. | {count} Kurspunkte gehen verloren.',
    irreversible: 'Das lässt sich nicht rückgängig machen.',
  },
}
