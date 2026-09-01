/** Deutscher Message-Katalog — Schema-Quelle für alle weiteren Sprachen. */
export const de = {
  /*
   * Wortmarke in zwei Teilen: Farbig ist der Teil, der die App
   * unterscheidet — "Stock" teilen sich alle. Getrennt im Katalog und
   * nicht im Template zerschnitten, sonst wandert die Teilung nicht mit
   * dem Namen.
   */
  app: { brandLead: 'Stock', brandAccent: 'Info' },

  /*
   * Was in einer Zelle steht, die keinen Wert hat — **an einer Stelle**. Jede
   * weitere Fassung im Quelltext wäre eine zweite Wahrheit, die niemand
   * mitzieht.
   *
   * Ein Bindestrich, kein Geviertstrich: Der Geviertstrich ist ein
   * Satzzeichen für Gedankenstriche, keine Marke für einen fehlenden Wert.
   */
  common: { noValue: '-' },

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
    toggleDetails: 'Details ein-/ausblenden',
    colIsin: 'ISIN',
    /*
     * Warum in diesen beiden Spalten ein Strich stehen kann — **die** Quelle
     * dafür, für jede Darstellungsform. Der Wortlaut nennt deshalb kein
     * einzelnes Papier: Er steht am Spaltenkopf der Tabelle wie neben dem
     * Strich der Karte.
     */
    noIsinReason:
      'Ein Bindestrich steht, wo es keine ISIN gibt: Ein Währungspaar trägt keine. Das ist die Form des Papiers, keine Lücke.',
    noSymbolReason:
      'Ein Bindestrich steht, wo es kein Börsensymbol gibt: Manche Papiere — etwa eine OTC-Anleihe — werden allein über ihre ISIN identifiziert.',
    colName: 'Name',
    colType: 'Typ',
    colPrice: 'Kurs',
    colTer: 'TER',
    colVola: 'Vola 1J',
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
    collector: 'Sammelcode',
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
    /*
     * **„Externe Abfragen" stand hier zu Unrecht.** Gemessen wird die
     * konfigurierte Kette — in einem reinen Dateiprofil verlässt dabei nichts
     * den Rechner. Der Cache bleibt außen vor, das gilt weiter.
     */
    hint: 'Misst die konfigurierte Quellenkette Rolle für Rolle — am Cache vorbei.',
    pickInstrument: 'Instrument wählen',
    orEnter: 'oder ISIN/Symbol eingeben',
    placeholder: 'ISIN oder Symbol (z.B. EUNL.DE)',
    run: 'Analysieren',
    running: 'Messe…',
    /*
     * **Rolle statt Anbietername.** Die Analyse misst, was die konfigurierte
     * Kette tut; welche Quelle in einer Rolle steht, entscheidet
     * `sources.yaml`. Ihr Name bleibt roh — er soll in der Datei
     * wiederzufinden sein.
     */
    colRole: 'Rolle',
    colSource: 'Quelle',
    role: {
      resolvers: 'Auflösung',
      quotes: 'Kurs',
      daily: 'Tagesreihe',
      etf_meta: 'Metadaten',
    },
    status: {
      ok: 'geliefert',
      empty: 'nichts',
      error: 'Fehler',
      /* Nicht „übersprungen": Die Kaskade hatte schon eine Antwort. */
      skipped: 'nicht gefragt',
    },
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
    /*
     * Wer für Kurse gefragt wird, in Rangfolge. **„Kurse", nicht „Quelle":**
     * Die Zeile nennt eine von fünf Rollen; die übrigen vier kann jemand
     * anderes bedienen.
     */
    quoteChain: 'Kurse: {chain}',
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

    /*
     * Der **Grund** hinter der Kategorie darüber, je Kennung aus
     * `ErrorDetail.code`. Das Backend schickt die Kennung und ihre Werte, den
     * Satz bildet das UI — so steht es in `app/models.py` zugesagt.
     *
     * Bis T-35 gab es diesen Katalog nicht: Jeder Fehlschlag zeigte nur seine
     * Kategorie, der Grund stand in der Browserkonsole. Eine unauflösbare ISIN
     * war damit von einem Netzausfall nicht zu unterscheiden.
     */
    reason: {
      /*
       * **Kein Text nennt eine Quelle beim Namen.** Welche Quellen antworten,
       * entscheidet `sources.yaml`; mit einem CSV-Profil oder einem fremden
       * Plugin wäre „über OpenFIGI und Yahoo" schlicht gelogen. Die
       * Oberfläche weiß es nicht und behauptet es deshalb nicht — wer wissen
       * will, wer gefragt wurde, findet es in `GET /sources`.
       */
      instrument_not_found:
        'Zu {identifier} hat keine der eingerichteten Quellen ein Wertpapier ' +
        'gefunden.',
      unsupported_instrument_type:
        '{symbol} ist ein {instrument_type} — diese Gattung nimmt StockInfo ' +
        'derzeit nicht auf.',
      quote_currency_mismatch:
        '{symbol} notiert in {expected}, die Quelle lieferte {delivered} — ' +
        'das ist ein anderes Instrument.',
      identifier_empty: 'Es wurde nichts eingegeben.',
      identifier_unknown_form:
        '{identifier} ist weder eine ISIN noch ein Symbol mit Börsenkürzel.',
      /*
       * **Und keiner behauptet mehr, als er weiß.** Hier stand „Das Papier
       * gibt es — nur konnte gerade niemand nachsehen." Das ist genau die
       * Aussage, die `Unavailable` **nicht** trägt: Wenn keine Quelle
       * geantwortet hat, ist offen, ob es das Papier gibt. Der Unterschied zu
       * `instrument_not_found` ist der ganze Sinn der beiden Kennungen.
       */
      quote_unavailable:
        'Keine Quelle konnte nachsehen: {identifier}. Ob es das Papier gibt, ' +
        'ist damit offen.',
      /*
       * **Dieselbe Trennung eine Ebene tiefer.** Die vier Kennungen darunter
       * kommen paarweise: Einmal hat die Kette vollständig geantwortet und
       * nichts gefunden, einmal war sie gestört. Wer beides gleich benennt,
       * schickt den Betreiber zur Fehlersuche bei einer Quelle, die gar nichts
       * falsch gemacht hat.
       */
      daily_series_not_found:
        'Für {identifier} führt keine der eingerichteten Quellen eine ' +
        'Kurshistorie.',
      daily_source_unavailable:
        'Die Kurshistorie zu {identifier} war nicht abrufbar — mindestens ' +
        'eine Quelle hat nicht geantwortet.',
      fx_pair_not_found:
        'Keine der eingerichteten Quellen führt den Kurs {base}/{quote}.',
      fx_source_unavailable:
        'Der Kurs {base}/{quote} war nicht abrufbar — mindestens eine Quelle ' +
        'hat nicht geantwortet.',
      invalid_currency_code:
        '{base} und {quote} müssen dreibuchstabige Währungscodes sein.',
      invalid_isin_format: '{isin} hat nicht das Format einer ISIN.',
      /*
       * Der Rückfall für eine Kennung, die diese Oberfläche nicht kennt —
       * etwa aus einem neueren Backend oder einem Plugin. Vorher stand die
       * rohe Kennung im Toast; `instrument_not_found` als Satz zu lesen ist
       * schlechter als ein ehrliches „unbekannt" mit der Kennung dahinter.
       */
      unknown: 'Die Quelle meldet einen Fehler, den diese Oberfläche nicht kennt: {code}.',
    },
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
    fromSource: 'Kommt aus der Quelle — von Hand nachgetragen wird nur, was dort fehlt.',
    markManual: 'Von Hand eingetragen — die Quelle liefert für dieses Papier nichts.',
    markShadowed:
      'Von Hand eingetragen: {value}. Angezeigt wird der Wert der Quelle — sie hat Vorrang. ' +
      'Die Eingabe bleibt gespeichert und greift wieder, sobald die Quelle nichts liefert.',
    removeOwn: 'Eigenen Wert entfernen',
    /*
     * Beschriftungen der fünf ETF-Extras, die T-15 nachträgt (T-09 deckte
     * TER, Volatilität und Thesaurierung bereits über die Tabellenköpfe ab).
     */
    fields: {
      provider: 'Anbieter',
      replication: 'Replikationsart',
      fundSize: 'Fondsvolumen',
      fundDomicile: 'Fondsdomizil',
      fundCurrency: 'Fondswährung',
    },
  },
  drilldown: {
    fetchedAt: 'Stand der Quelle',
    source: 'Quelle',
    /*
     * **Kein Text nennt eine Quelle beim Namen** — dieselbe Regel wie bei den
     * Fehlermeldungen unter `errors.reason`, nur eine Textgruppe weiter.
     *
     * Hier stand viermal „justETF". Im CSV-Profil heißt die Kennzahlen-Quelle
     * `metadata-file`, und die Zeile darüber zeigt das sogar korrekt an —
     * derselbe Aufklappbereich behauptete daneben justETF. Gesehen im
     * zweiten Browserlauf zu T-37.
     *
     * Bei drei der vier Texte war **nur der Name** falsch: Dass Kennzahlen
     * ausschließlich für ETFs und nur mit ISIN geholt werden, entscheidet die
     * **App** (`app/services/quote_service.py`: `if instrument_type ==
     * "etf":`), nicht der Anbieter. Ohne den Namen sind sie deshalb nicht
     * vager, sondern richtiger.
     */
    explain:
      'Die Kennzahlen holt die eingerichtete Quelle, wo sie welche hat. Von Hand ' +
      'lässt sich nur ergänzen, was sie nicht liefert — sie hat immer Vorrang.',
    // Die konkrete Gattung steht bereits als Kennzeichen in derselben Zeile;
    // hier zählt nur, dass die ETF-Anreicherung nicht zuständig ist.
    notEtf:
      'Kennzahlen werden nur für ETFs geholt — dieses Papier ist keiner. Die ' +
      'Quelle wird deshalb gar nicht erst abgefragt, alle Felder lassen sich von Hand nachtragen.',
    noIsin:
      'Ohne ISIN wird keine Kennzahlen-Quelle abgefragt. Sobald eine ISIN eingetragen ' +
      'ist (Kennung in der Zeile), greift die Quelle wieder; bis dahin lassen sich alle ' +
      'Felder von Hand nachtragen.',
    /*
     * **Ein Text für zwei Fälle, und das ist die ehrliche Fassung.**
     *
     * Vorher gab es hier zwei: „justETF deckt nur europäische UCITS-ETFs ab"
     * und „Die Quelle wurde abgefragt, hat aber nichts geliefert". Der erste
     * war justETFs Zuständigkeitsregel, im Frontend nachgebaut — eine zweite
     * Wahrheit über die Interna eines fremden Plugins. Der zweite behauptete
     * „wurde abgefragt", obwohl die Oberfläche genau das nicht weiß.
     *
     * Ob eine Quelle nicht gefragt wurde oder gefragt wurde und nichts hatte,
     * weiß nur das Backend — es ruft `is_responsible()`. Bis diese Auskunft
     * im Vertrag steht (Fähigkeitsdeklaration, T-31/T-38), sagt die
     * Oberfläche das, was in beiden Fällen stimmt.
     */
    nothingProvided:
      'Die eingerichtete Kennzahlen-Quelle hat für dieses Papier nichts geliefert — ' +
      'alle Felder lassen sich von Hand nachtragen.',
  },
  confirmDelete: {
    title: 'Asset löschen?',
    history: 'Keine Kurspunkte gespeichert. | 1 Kurspunkt geht verloren. | {count} Kurspunkte gehen verloren.',
    irreversible: 'Das lässt sich nicht rückgängig machen.',
  },

  /*
   * Der Identitäts-Umzug (T-21 Teil 3).
   *
   * `reason.*` sind die **stabilen Kennungen** aus `app/migration.py` — der
   * Server schickt die Kennung, der Satz steht hier. Genau deshalb heißt die
   * Regel „stabile Reason-Codes statt freier Texte": Ein Satz aus dem Backend
   * wäre in der zweiten Sprache sofort falsch.
   */
  migration: {
    checking: 'Zustand wird geprüft…',
    starting: 'Der Betrieb läuft an…',

    title: 'Der Bestand muss umgezogen werden',
    lead:
      'Jedes Papier bekommt eine eindeutige Identität aus Ticker und Börsenkürzel. ' +
      'Wo sich das alte Symbol nicht zweifelsfrei zerlegen lässt, wird es ' +
      'ausgelassen — geraten wird nicht.',

    balanceMigrating: 'Werden umgezogen',
    balanceUnchanged: 'Bleiben unverändert',
    balanceRejected: 'Verlassen den Bestand',

    removedTitle: 'Diese Papiere verlassen den Bestand',
    removedNote:
      'Sie stehen weiterhin im Bericht und lassen sich mit vollständiger Angabe ' +
      'wieder anlegen.',
    lossSummary:
      'Dabei entfallen {quotes} Intraday-Kurspunkte und {daily} Tagesschlusskurse.',
    rowLoss: '{quotes} Kurspunkte, {daily} Tagesschlusskurse',

    backupTitle: 'Vorher sichern',
    backupBody:
      'Der Umzug lässt sich nicht rückgängig machen. Legen Sie eine Kopie der ' +
      'Datenbankdatei an, bevor Sie bestätigen — danach sind die oben genannten ' +
      'Zeilen und ihre Kurse nur noch im Bericht vorhanden.',

    confirm: 'Umzug jetzt ausführen',
    confirming: 'Der Umzug läuft…',

    doneTitle: 'Der Umzug ist durch',
    doneLead: 'Der Bestand trägt jetzt durchgehend Ticker und Börsenkürzel.',
    doneNothingLost: 'Es musste kein Papier entfernt werden.',
    continue: 'Weiter zum Dashboard',

    startupFailedTitle: 'Umzug erledigt, Betrieb nicht angelaufen',
    startupFailedBody:
      'Die Daten sind umgezogen — daran ändert sich nichts. Der Hintergrund-Abruf ' +
      'für neue Kurse ist aber nicht gestartet, die Kurse würden also veralten. ' +
      'Ein weiterer Versuch startet nur den Betrieb, nicht den Umzug.',
    retry: 'Betrieb erneut starten',
    retrying: 'Der Betrieb wird gestartet…',

    downTitle: 'Der Dienst antwortet nicht',
    downBody: 'Die Datenbank ist nicht erreichbar. Prüfen Sie den Server und laden Sie neu.',

    reason: {
      symbol_without_exchange_suffix:
        'Dem Symbol fehlt das Börsenkürzel — aus ihm allein lässt sich der Handelsplatz nicht ableiten.',
      unknown_exchange_suffix:
        'Das Börsenkürzel im Symbol ist unbekannt und lässt sich keinem Handelsplatz zuordnen.',
      non_canonical_ticker:
        'Der Ticker entspricht nicht der kanonischen Schreibweise des Handelsplatzes.',
    },
  },
}
