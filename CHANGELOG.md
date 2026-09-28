# Changelog

Generated from release tags and Conventional Commits.

## v1.3.0+260928.1407.95b90 — 2026-09-28

About-Seite mit Datenhinweisen und Anbieterangaben

### Fixes

- Backup in den Einstellungen einheitlich benennen (`67f72c0`)
- consolidate About provider details (`eece7d4`)
- Fehlermeldung bei leerer Serverantwort anzeigen (`cb7fbe7`)
- YAML-Tagesreihen ohne Datumsfenster prüfen (`78059a8`)

### Features

- add data use notice and About links (`6134b6b`)
- complete StockInfo About provider panel (`5d0ea26`)
- Changelog aus Tags erzeugen und veröffentlichen (`66ca7b1`)

## v1.2.0+260927.2159.9e591 — 2026-09-27

StockInfo unter EUPL 1.2 bereitstellen

### Documentation

- README und API-Referenzen auf aktuellen Stand bringen (`d2f0827`)
- document defaults and complete review evidence (`a7e37ba`)
- add dedicated Docker Hub installation guide (`efeab04`)
- Installation und Betrieb in eigene Anleitung auslagern (`68702c6`)
- Installationskurzfassung gemäß Skill ergänzen (`f6abd45`)
- Doppelte Installationsangaben durch Verweise ersetzen (`b975952`)
- Apps als Standardinstallation beschreiben (`a26fbbf`)

### Features

- sync readme after successful image push (`6f31bbc`)

### Fixes

- call isolated Bash uploader from push (`0cef0f0`)

## v1.1.0+260926.1131.84631 — 2026-09-26

Instrument-Types können abgefragt werden

### Fixes

- Feldbeschreibungen durchgehend auf Englisch liefern (`fc0063e`)
- Plugin-Typkatalog auch aus Swagger weiterleiten (`fc67ea3`)

### Features

- Verfügbare Plugin-Assettypen über REST bereitstellen (`a559c09`)

## v1.0.0+260925.1818.661d5 — 2026-09-25

StockInfo 1.0.0: AGPL-Lizenz und geprüfte Docker-Veröffentlichung

### Documentation

- Screenshots und README für 0.6.0 — Oberfläche auf Englisch (`1b2bb35`)
- Design für das Plugin-System — deklarativ und als Code (`5117084`)
- nur Python-Plugins — der deklarative Weg entfällt (`a43364a`)
- Runde 2 der Codex-Review eingearbeitet, Spec wird Rückkanal (`cf6bf42`)
- Runde 3 — StockPortfolio ist ein Konsument, das ändert T-21 (`bd9ae47`)
- Begründung für den REST-Vertrag korrigiert (`0b52f2a`)
- Runde 4 — Core geschlossen, Details offen; Profilwechsel als T-25 (`1d423bd`)
- Runde 5 — listing\_id, abfragbarer Vertrag, T-26 angelegt (`9f406c0`)
- Runde 6 eingearbeitet, T-27 für die Test-Infrastruktur (`4259c8d`)
- Runde 7 — Testbarkeit beantwortet, T-27 geschnitten (`d94c249`)
- Runde 8 — Ticket-Schleife aufgelöst, Crash-Matrix nachgetragen (`b79a1cd`)
- Frage zur generation\_id an Codex, T-35 ist committet (`15771c0`)
- Runde 9 — Generationstransport entschieden (`cf91985`)
- Runde 10 — Ticket-Schleife entfernt, vier Begriffe geschärft (`c98c527`)
- Runde 11 — auch die Generationsbestätigungen können sich überholen (`0e4c501`)
- Runde 12 — Single-Flight gewählt, T-35 neu nummeriert (`99d9036`)
- Entwurf abgenommen — Umsetzung kann beginnen (`2907004`)
- T-21 Teil 3 entworfen — Kombination im Vertrag statt Handzuordnung (`f65dfcc`)
- T-21 Teil 3 ueberarbeitet — Alias, Waehrung und Inventur berichtigt (`7321bfc`)
- T-21 Teil 3 Runde 11 — Exchange-Descriptor statt Laengenregel (`72f2b8a`)
- T-21 Teil 3 Runde 12 — ein Alias, getrennte Sammelcodes, POST (`8904093`)
- T-21 Teil 3 Runde 12 an Codex uebergeben (`9211a74`)
- Entwurfsrunden im Automationsvertrag geregelt (`8f0e9b4`)
- T-21 Teil 3 Runde 14 — Erfolgsvertrag und eine Mitgliedschaft (`fecd40d`)
- T-21 Teil 3 Runde 15 — IntakeResult und atomare Vertragsgrenze (`fb1bc55`)
- T-21 Teil 3 Runde 16 — nullable Identitaet und created aus der Transaktion (`1dca99e`)
- T-21 Teil 3 Runde 17 — keine halbe Identitaet mehr (`201c960`)
- T-21 Teil 3 Runde 18 — Meldung vor Datenverlust, Ticket entwidersprochen (`c9d6670`)
- T-21 Teil 3 Runde 19 — zweiphasige Migration, Ticket einstimmig (`20a4422`)
- T-21 Teil 3 Runde 20 — Pending-Guard, /ready bleibt gesund (`5970806`)
- T-21 Teil 3 Runde 21 — /ready bleibt 503, Allowlist nach Pfad (`28ba9f9`)
- T-21 Teil 3 Runde 22 — Allowlist konkret, /operational, 2A/2B (`a9fde37`)
- T-21 Teil 3 Runde 23 — Static-Allowlist abgeleitet, Vite-Proxy ergaenzt (`fd79566`)
- T-21 Teil 3 Runde 24 — / ist ein Alias, keine Datei (`c5d0388`)
- strengerer /quote?symbol= wandert nach Uebergabe 2A (`b5044c3`)
- der Diagnosevertrag nennt alle vier 503-Gruende (`22735a1`)
- Plugin-MVP vor Folgearbeiten priorisieren (`c3f72f5`)
- T-22 freigegeben, Arbeit an T-27a aufgenommen (`11d8009`)
- Restprosa des Offline-Modells entfernen (`08814ff`)
- Orakel und Verdrahtung trennen — und was die Orakel entschieden haben (`08acf51`)
- T-31 Runde 5 zurueckgeben (`bf99282`)
- den Vertrag propagieren — Beispiel, Pflichtfelder, Contract-Kit (`96b3184`)
- Scope-Unterbrecher spezifizieren (`d9653f0`)
- Scope-Spec formatieren (`4f428fc`)
- Scope-Guard-Umsetzung planen (`a07b836`)
- Scope-Guard als umgesetzt markieren (`2b47b53`)
- T-37 Rollenvertrag begrenzt zurueckgeben (`e727932`)
- englischer Autorenleitfaden mit lauffaehigem Beispielpaket (`951f866`)
- T-50 Runde 5 — Waechter raus, WAL-Ursache belegt, vier Drains (`62127bf`)
- das dritte Quellenprofil entfaellt (T-52 R3) (`14a270f`)
- T-54 Scope-Checkpoint — zweiter Defekt blockiert Verify 2 (`1370cfe`)
- T-53 Scope-Checkpoint — 26 Stellen schreiben den Text, nicht eine (`f9e27b1`)
- Review des Agenten-Workflow-Serverentwurfs (`ef265a4`)
- context\_budget als gesetzte Grenze, nicht als Fensteranteil (`34314ec`)
- Runde 2 zur Stellungnahme, acht Punkte je Befund (`fa07047`)
- Runde 3 zum Kanban-Schnitt, acht Befunde (`b7407f1`)
- Runde 3, Nachtrag mit Mikes Entscheidungen (`73cf97d`)
- Antwort auf Codex' Stellungnahme, Konsolidierung als Vorschlag (`4efbd8b`)
- K-01 bis K-04 in den Vorschlag, Herkunft der Regeln getrennt (`61a8aab`)
- Rueckmeldung an Codex zum Reviewvorgehen (`d83e53d`)
- data\_version in Beispielplugins explizit zeigen (`6d85046`)
- Ticket verwerfen, Bestandsschutzregel nach T-30 uebernehmen (`35a7545`)
- define T-30 contract and scope checkpoint (`d0e6ad0`)
- MIC-Regeln und Prüfbeschreibungen korrigieren (`f0fb8c8`)
- MIC-Vertrag ohne Ablösungshinweis beschreiben (`4bacaf2`)
- T-67 Runde 1 mit changes\_requested beantworten (`56ffe1f`)
- kleinen Migrationsablauf zur Umfangsprüfung vorbereiten (`b2abac0`)
- Paketversion und Startriegel aktuell beschreiben (`fdd3312`)
- unabhängige Freigabe dokumentieren (`a386a47`)
- Ticket aktualisieren und abschliessen (`c1ce421`)
- Einstieg auf den fertigen Stand bringen (`debb3d1`)
- Verweise auf die verschobenen Dateien anpassen (`3d01098`)
- Relative Links im Archiv vervollständigen (`d76ac27`)
- Ticketregeln und Projektdokumentation konsolidieren (`778e449`)
- AGPL-Pflicht in Alltagssprache erklären (`216466a`)
- AGPL-Nutzung und MIT-Ausnahmen klarstellen (`3b0f817`)

### Fixes

- das fehlende Symbol für das CA-Listing erzeugen (`fb96b5d`)
- bekanntes Instrument beim Refresh nicht neu auflösen (`b7a08f4`)
- Gattung beim Refresh mitgeben, sonst fällt der ETF-Schutz aus (`7011b95`)
- unbekannte Gattung gilt nicht mehr als vollständige Metadaten (`1222c4f`)
- Yahoo-Fallback nimmt das Listing der bevorzugten Börse (`f6c5b28`)
- Fortschrittsbalken sitzt an der Oberkante der Seite (`5c094f8`)
- fünf Fehler aus dem Code-Review behoben (`5ec9c37`)
- Befunde der Codex-Review eingearbeitet (`399dbd5`)
- Drei stille Fehler im Antwortpfad behoben (T-17) (`84c9c2d`)
- Codex-Befunde aus Runde 1 zu T-17 eingearbeitet (`1a2f2bd`)
- Negativ-Fixtures muessen ihre Verletzung nachweisen (T-24) (`9d01750`)
- Waehrungspflicht auch im Cache, Schnappschuss folgt Verweisen (T-24) (`f10f45e`)
- Composite reicht den Kontext bis zum Abruf durch (T-18) (`69e18c1`)
- Diagnose wertet alle vier Antwortarten aus (T-20) (`34cf386`)
- Bereinigung zerstoert keine echten Listings mehr (T-21) (`48cdaf9`)
- Nur bewiesene Gleichheit fuehrt zusammen (T-21) (`7da4aae`)
- Pruef-Oracle rechnet vorwaerts statt sich selbst recht zu geben (T-21) (`d6c4c19`)
- Sammelcode faellt auf, leerer Lauf gilt nicht als bestanden (T-21) (`92ee6a2`)
- Widerspruechlicher Status wird geheilt statt konserviert (T-21) (`4b7a88a`)
- Echter MIC ist Bedingung, kaputter Status kostet keine Zuordnung (T-21) (`3148d09`)
- MIC-Schreibweise wird geprueft, nicht nur der Sammelcode (T-21) (`62dcfd2`)
- MIC-Pruefung mit fullmatch, Smoke bekommt eigenes Orakel (T-21) (`be5f38d`)
- jeder Aufnahmeweg erzeugt die Identitaet (T-21, Runde 3) (`c6f69a9`)
- geteilte Aussengrenzen und Bezeichner-Bereinigung (T-21, Runde 4) (`3cc223d`)
- Resolver-Handoff vollständig bereinigen (`1ea5936`)
- Test-Helfer typisieren und Testaufbau richtig beschreiben (`806c1a1`)
- Alias optional, Provenienz als diskriminierte Union (`083414c`)
- Boersenauswahl unterscheidet aliaslose Plaetze (`43003a9`)
- Identitaetsindizes brechen den Start einer Alt-Datenbank nicht mehr (`638e9cc`)
- Bestaetigung startet den Scheduler (`d361fbc`)
- drei betriebsgefaehrdende Fehler aus Codex-Runde 30 (`d06a6a1`)
- gescheiterter Scheduler-Start meldet keinen Normalbetrieb (`21865c0`)
- der Riegel wird eine Zustandsgroesse statt dreier Flags (`2c9f454`)
- der Wiederholungsweg zeigt nicht mehr den ausstehenden Umzug (`7d9c671`)
- Eingabeidentitaet, Vertragspaket und benannter Suffixkonflikt (`c04a36b`)
- Konfliktpfade, Vertragspaket und zwei DRY-Befunde aus Runde 42 (`385b819`)
- Identitaetskonflikt als typisierter 409 und eine Source of Truth (`36d54ce`)
- vier Befunde aus Codex-Runde 1 zu T-22 (`d5bb327`)
- vier Befunde aus Codex-Runde 1 zu T-27a (`db53189`)
- vier Befunde aus Codex-Runde 2 zu T-27a (`d9ad4ad`)
- Integer-Grenze aus Codex-Runde 3 an drei Fundstellen (`f1254fe`)
- drei Befunde aus Codex-Runde 4 zu T-27b (`cd3e2f3`)
- sechs Befunde aus Codex-Runde 2 (`4e23cde`)
- vier Befunde aus Codex-Runde 4 (`d4f9036`)
- drei Befunde aus Codex-Runde 5 zu T-23 (`a9e49f9`)
- fuenf Befunde aus dem UI-Lauf T-35 (`405d659`)
- vier Befunde aus Codex-Runde 1 zu T-36 (`27ffe81`)
- Erklaertexte im Aufklappbereich nennen keine Quelle mehr (`0094d02`)
- sieben Befunde aus Codex-Runde 2 (`cc0f028`)
- vier Restbefunde aus Codex-Runde 3 (`c44b932`)
- Snapshot nach \`extra=forbid\` auf den Identity-Modellen (`56c2f80`)
- Kit und Loader pruefen dieselbe Schranke (Codex P1 #5) (`c3eab35`)
- eine leere Deklaration heisst nichts, nicht alles (P1 #3) (`3cba9f0`)
- die Datei-Kursquelle deklariert ihre Gattungen (`129bd2a`)
- leere Deklaration und Quellenausfall (Codex #2 und #3) (`e471e58`)
- die Metadatenkaskade fragt die Deklaration (Codex #4) (`7975369`)
- die fuenfte Antwort durch alle vorhandenen Verbraucher ziehen (`ffb3ee7`)
- vollstaendige Feldauskunft und Leerraum als fehlender Wert (`34930da`)
- unnoetigen Inhaltshelper entfernen (`1a1466a`)
- beim Laden wirklich validieren, Zusagen auf das Machbare bringen (`3e97a9e`)
- die fuenf Rollenvertraege erfuellen — und den Lade-Rand schliessen (`b464471`)
- die Formgrenze einmal vollstaendig, statt Einzelfaelle nachzureichen (`1c70425`)
- die Validator-Schicht zu Ende verdrahten (`7a3e90b`)
- der geprueste Wert ist auch der gespeicherte (`d4e01b3`)
- die Herkunft nennt die Quelle, die geantwortet hat (`0bb5c20`)
- die neuen Formen ueberleben Migration, Gattung und Drilldown (`bdedd8e`)
- die Regel einhalten, die das Beispiel lehrt (`1110d76`)
- vier Anzeigebefunde aus dem Browserlauf — und der Riegel dahinter (`288c527`)
- das Caret bekommt seine eigene Spalte (`13d4652`)
- das Caret behaelt seine Kantenlaenge (`35ddf27`)
- dieselbe Regel in beiden Ansichten, die Typregel an einer Stelle (`d3f1949`)
- der Strich traegt seinen Grund selbst (`100bff5`)
- der Klick auf den Strich endet am Strich (`66d887e`)
- der Klick auf den Strich oeffnet den Kursverlauf wie die ganze Zeile (`37891a0`)
- der Strich tut dasselbe wie das Symbol an seiner Stelle (`be8f10d`)
- der Hinweis steht einmal im Spaltenkopf statt in jeder Zeile (`e7bbd03`)
- ein Bindestrich als Platzhalter, aus einer Quelle (`22ea317`)
- der Platzhalter hat ueberall dieselbe Breite (`c6f5001`)
- eine Regel je Fall, und die Caret-Regeln zurueck (`09f37d0`)
- die Statuszeile nennt die Kurskette, nicht ihren Kopf (`f8e0fda`)
- Laufzeitkette in Quellenkommentaren korrekt erklaeren (`1f1fbb7`)
- 404 und 502 sagen, was sie meinen (`cc7cafc`)
- das ISIN-Format kommt oben an, nicht unter \`detail\` (`5668dc7`)
- sieben Wege, drei Formen — der 422 wird vollstaendig zugesagt (`f51393a`)
- \`detail\` ist in der Fliesstext-Variante Pflicht (`2a68c5c`)
- der Fonds gehoert nicht in die Fallback-Vorlage (`ee468b7`)
- Fallback-Vorlage auf aktuelle Regel begrenzen (`5295e98`)
- die fuenf Antwortarten behalten ihre Bedeutung (T-46 R2) (`5d88d8b`)
- parallele Sicherungen serialisieren (T-47 Runde 2) (`aa239fb`)
- Quelle schuetzen, Fehlerzustand benennen, Herkunft erhalten (T-47 1b R2) (`a904d42`)
- Fehlerzustand ohne pending\_restore, Nutzerweg im Orakel (T-47 1b R4) (`e898f7a`)
- Fehlerwege aus dem Katalog, Bestaetigung sperren (T-47 UI R2) (`e9221bc`)
- Passungsgrund sprachneutral als Kennung (T-47) (`2f70655`)
- backup\_not\_found ist keine Passungsursache (T-47) (`47966f6`)
- gestoerte Datei liefert keinen alten Wert als aktuellen (T-48 R2) (`4186cc8`)
- eine abgelehnte Signatur wird nicht gemerkt (T-48 R3) (`08214cf`)
- ein offener Grund sperrt den Signatur-Fast-Path (T-48 R4) (`e57ab4c`)
- das Analysefeld zeigt seinen Platzhalter wieder (T-50 Phase B) (`475e72a`)
- der API-Test oeffnet die Betriebsdatenbank nicht mehr (T-55) (`0bebb89`)
- jedes Profil zeigt auf seine eigene Fachdatei (T-52 R2) (`db83ac3`)
- ein Papier mit Boersensuffix laesst sich wieder aufnehmen (T-54) (`a2e65ad`)
- Boerse, Ablehnung und Ausfall im Suffixweg (T-54 R2) (`ede5c3a`)
- auch ein Treffer mit fremder Gattung wird abgelehnt (T-54 R3) (`c142f17`)
- der Analyzer komponiert keinen Satz mehr (T-53, Variante A) (`05823a7`)
- Identitaetskennungen finden ihren Satz auch im Aufnahmeweg (`a2b33b0`)
- Toast-Titel folgt dem Sprachwechsel (`cb33dcb`)
- Relative Quellenprofile und Yahoo-Langnamen nutzen (`d7afe20`)
- Detailfelder ohne doppelte Zeitangaben erklären (`53d8d9f`)
- Überflüssige Hinweise an Detailfeldern entfernen (`fe323ff`)
- Feldherkunft nur im Tooltip anzeigen (`8bf2d53`)
- Feldschema bei Quellenausfall erhalten (`c0c859f`)
- Herkunfts-Tooltip am Feldanfang ausrichten (`a97bf2c`)
- Störende Herkunfts-Tooltips entfernen (`cb14e4b`)
- Rotes Löschsymbol neben dem Textfeld halten (`2a38254`)
- Abstand zum Löschsymbol verkleinern (`5a11ddb`)
- Fondswährung kompakt neben dem Betrag anzeigen (`31580b6`)
- Fondsvolumen ohne feste Währung beschriften (`02afd8c`)
- Feldbeschriftungen von Detailwerten abheben (`84f60ff`)
- Kleinere Schriftstufe für Feldlabels verwenden (`009725f`)
- Währung beim Fondsvolumen auswählbar machen (`983e659`)
- Gesamtkostenquote um TER ergänzen (`f9cb30b`)
- Manuelle Detailwerte einheitlich rechts löschen (`8f428d9`)
- Veraltete Kennzahlen ohne Detaildeklaration ausblenden (`aa680cc`)
- App-Suffix mobil hervorheben (`1814232`)
- MIC und App-Suffix durchgehend einfärben (`e427013`)
- Unübersetzte Servertexte aus Fehlermeldungen entfernen (`1985037`)
- address coverage review findings (`f3b383b`)
- preserve error contract rationale and naming (`b10e110`)
- Sammelcodes durch konkrete MICs ablösen (`1166745`)
- beende Rückfrage an bevorzugter Börse (`13ef760`)
- clarify exchange choice with original input (`8099fc6`)
- bestätigte Dialoggestaltung übernehmen (`41085c3`)
- laufenden und fehlgeschlagenen Start unterscheiden (`16cf3d3`)
- Docker-Quellenprofil ins Startvolume schreiben (`aaf48fd`)
- Beispielwerte ohne Inline-Kommentare lesbar machen (`b08a583`)
- Dashboard beim amd64-Build nativ bauen (`47049e9`)
- Lizenz und Quellverweis im Image bereitstellen (`bb99413`)
- Buildartefakt und Lizenzen automatisch prüfen (`768f312`)
- Vorgemerkte Änderungen vor dem Build abweisen (`6c04622`)
- Alten Push-Nachweis auch bei Tagfehler löschen (`7dbf5d8`)
- Nur geprüfte Einzelplattform-Images freigeben (`eeb9c2e`)

### Other changes

- Zielplattform im Makefile festschreiben, x86 als Vorgabe (`33ebd40`)
- Test-Target ergänzt und Konfig-Leck in Kindprozesse geschlossen (`6ee6bbe`)
- OpenFIGI-Wissen zieht zum Provider (T-21, Teil 2b) (`556c23d`)
- eine Boersenableitung fuer Auswahl und Identitaet (`192ac94`)
- QuoteResponse-Aufrufe auf die Identitaets-Union falten (`735acbf`)
- eine Weiche statt dreier Fassungen (`ea2e1f1`)
- T-37 auf den abgespaltenen Umfang zurueckschneiden (`472a5e9`)
- Pruefdaten zu den Tests, Betriebsvorlagen ins Repo (`f24354f`)

### Features

- ETF-Metadaten je nach Domizil aus justETF oder Yahoo (`809c48a`)
- Vertragspaket für Datenquellen-Plugins skizziert (`840121c`)
- REST-Core als pruefbares Artefakt festgeschrieben (T-24, Teil 1) (`403020b`)
- Vertrag zur Laufzeit abfragbar, Waehrung ist Pflicht (T-24, Teil 2) (`d792ce9`)
- Aufloesung erreicht mehr Maerkte (T-18) (`32e08ea`)
- Quellen antworten differenziert statt mit None (T-20) (`5d79a6d`)
- (ticker, mic) und listing\_id neben symbol (T-21, Teil 1) (`fce1bab`)
- neue Papiere bringen ticker und mic mit (T-21, Teil 2) (`6abce88`)
- Boersenkatalog trennt Handelsplaetze von Sammelcodes (`0f79eec`)
- Ablehnungsgruende und Vorschau-Bausteine fuer T-21 2A (`18040d4`)
- Umzug ausfuehren, Bericht ueberlebt die geloeschte Zeile (`595e134`)
- Pending-Guard mit abgeleiteter Allowlist (`0a33c50`)
- /quote?symbol= lehnt ein unzuordenbares Symbol ab (`6d9ebaa`)
- Pflichtablauf verdrahtet — Guard, Endpunkte, /operational (`f702bee`)
- die Pflicht-Oberflaeche fuer den Identitaets-Umzug (`5b0fa31`)
- created als Tatsache der schreibenden Transaktion (`38940ec`)
- Zwei-Formen-Eingaberegel und Intake-Service (`20daa7a`)
- core\_version 2.0.0 mit Aufnahmeweg und zugesagter Identitaet (`62130cb`)
- mehrdeutiges Symbol ist ein 409 mit Kandidaten statt geratenem Listing (`2dd0dc3`)
- Quellen aus sources.yaml statt aus der Verdrahtung (T-22) (`20af8fa`)
- Contract-Kit fuer alle fuenf Rollen (T-27a) (`6121a94`)
- OpenFIGI als Resolver-Rolle, mit Integrationstest (`ebf8a14`)
- Registry laedt Quellen ueber zwei Wege (`e2578c6`)
- justETF und yfinance als Rollen, Auswahl per Konfiguration (`e6ca003`)
- vertikaler Lauf Registry -\> Core -\> REST, beide Ladewege (`e35d190`)
- fuenf Befunde aus Codex-Runde 3, inklusive Installationsweg (`adcb505`)
- CSV-Profil mit derselben Pruefstrecke (T-37) (`d313318`)
- Union durch Vertrag, Plugins, Adapter und Schema (`b9078dc`)
- Identitaet als ein Feld mit diskriminierter Union (`6c9d02e`)
- Repository und Services auf die Union (`56c9fe8`)
- Cache-Weg und Test-Doubles auf die Union (`cdd6ef9`)
- identity im Vertragsartefakt statt ticker/mic/isin (`740bcd4`)
- Konfliktmeldung und Aufnahmeweg auf die Union (`94fd38c`)
- identity auch in den veroeffentlichten Fixtures (`d71f920`)
- der duenne vertikale Pfad — ein Paar kommt herein (`df279d9`)
- eine Fehlerform statt zweier, und die Kennung im Katalog (`2940f64`)
- die Waehrung des Paars gehoert zur Identitaet (Matrix #7) (`d39ce87`)
- quote\_unavailable als Zustand, nicht als Fliesstext (`516b53f`)
- die Anleihe kommt ohne Kurs in den Bestand — Pfad vollstaendig (`2f0de62`)
- die Union ist an den Raendern genau (Codex P1 #4) (`296fd98`)
- BTC-EUR kommt durch die \*\*reale\*\* Kette (Codex P0) (`65e312b`)
- eine fuenfte Antwort fuer "erkannt, aber nicht gefuehrt" (`5b3c406`)
- Name und Gattung werden Pflichtfelder (T-38) (`e108801`)
- die REST-Zusage zieht mit — Name und Gattung garantiert (`1920e91`)
- ein Plugin, eine Datei, fuenf Rollen — vier CSV-Quellen entfallen (`f34cc3f`)
- der Smoke bekommt sein YAML-Profil, die Doku zieht nach (`6494064`)
- Kurs- und History-Kaskaden ausfuehren (`35979d8`)
- konfigurierte Quellen als Kaskade abfragen (`6b734cb`)
- YAML als echten Online-Fallback verdrahten (`115ac6c`)
- die Statuszeile nennt die Kursquelle (`50b7341`)
- die Diagnose misst die konfigurierte Kette (T-46) (`9e97d24`)
- Sicherung, Manifest und Liste (T-47 Runde 1a) (`c56c7b6`)
- Wiederherstellen pruefen, vormerken, beim Start einloesen (T-47 1b) (`0e6ca65`)
- Sicherungen im Dashboard anzeigen und wiederherstellen (T-47 UI) (`b0f5280`)
- eine geaenderte Fachdatei wirkt ohne Neustart (T-48) (`a9d66a0`)
- beide Quellenprofile als Vorlagen unter examples/ (T-52) (`d9819c0`)
- das Gate legt die Sicherung an, zu der es raet (`7b8d3bc`)
- Plugin-Felder in REST und Dashboard durchreichen (`abda3c9`)
- Kompatibilität über Plugin-data\_version prüfen (`ac49828`)
- merge plugin MIC declarations into intake and REST (`0336d10`)
- Plugin-Handelsplätze dynamisch anzeigen (`7e70827`)
- expose active exchange coverage (`2c1d01b`)
- validate exchange coverage during asset intake (`d7b4ab3`)
- ergänze Projektlinks und plane Aufnahmeentscheidung (`11e77fa`)
- bestätige abweichendes Listing vor dem Speichern (`9c1eb3d`)
- Datenmigration vor dem Fachbetrieb ausführen (`37c9025`)

### Breaking changes

- Identitaet als getaggte Union, API\_VERSION 2 (`c767ca1`)
- QuoteResponse verbietet unbekannte Felder (`29bed9f`)
- core\_version auf 3.0.0 — und warum hier statt in T-38 (`15f94f4`)
- Identitaets-Union bis in die Oberflaeche (`e792447`)
- der Frischstart zerstoert die Formregel nicht mehr (`fadd6f6`)

## v0.6.0+260819.1053.222ed — 2026-08-19

ETF-Extras im Detailbereich, Datenverlust-Fehler behoben

### Documentation

- README auf Englisch + Screenshots für README und CA-Template (`78101aa`)
- Excel-Beispielmappe mit Power-Query-Anbindung hinzugefügt (`ee10c6a`)
- Design für Analyse-Tab + Volatilität aus akkumulierendem EOD-Cache (`6d22a2a`)
- Implementierungsplan Analyse-Tab + EOD-Volatilität-Cache (`9530de1`)
- Design für weltweite Default-Börsen + FX-Endpoint (`52c7d55`)
- Währungs-Spec um UI (datengetriebene Börsen + Devisen-Tab) und FX-Semantik ergänzt (`df74da5`)
- Implementierungsplan Währungen (weltweite Börsen + FX, Backend + UI) (`5da4f2e`)
- Ticket-Board (\_tickets) sowie FX-Spec und -Plan ergänzen (`d62bfdf`)
- T-05 (Responsive-Header) nach solved; Spec und Plan ergänzen (`5a36a75`)
- T-11a — Design Navigation entrümpeln + Einstellungsseite (`66b4102`)
- T-11a — Implementierungsplan Navigation + Einstellungsseite (`f60887d`)
- T-11b — Implementierungsplan Token-Aliase (`8e36fe6`)
- T-11c — Implementierungsplan mobile Kartenliste (`3355e15`)
- T-11d — Implementierungsplan elf Paletten (`307c6bc`)
- T-11d auf dreizehn Paletten umgeschrieben (`743be12`)
- ETF-Extras vollständig nachtragen + aufklappbare Zeile (`a5c1f3b`)
- Implementierungsplan für ETF-Extras und Schublade (`db65984`)
- Namensregel am Bestand ausrichten, Helfer englisch (`0c75db1`)
- Rundlauf-Test von Task 2 nach Task 4 ziehen (`47ee780`)
- DRY als globale Vorgabe, nicht nur als Sonderfall (`d9cc73b`)
- Bezeichner ausnahmslos englisch, auch lokale (`90fc5c4`)
- deutschen Testbezeichner im Task-5-Block ersetzen (`ba7a3cb`)
- Übergabe für T-15 — Stand, offene Punkte, Urteile (`4b24802`)
- Übergabe nachgezogen — Branch ist nicht mergefähig (`4de0462`)
- Verweise auf die gelöschte ManualMetric.vue klarstellen (`67b5de9`)
- Betriebsmodell und Readiness im README (`3bf1f66`)
- Übergabe zu T-15 entfernen — die Einheit ist gemerged (`ed089e2`)

### Features

- make status zeigt Git-Status der Workspace-Repos (`452d170`)
- Volatilität aus akkumulierendem EOD-Cache statt pro Fetch neu laden (`d7426c5`)
- QuoteAnalyzer für Stage-Timing eines Live-Fetch (`3a9686b`)
- GET /analyze-Endpoint für Stage-Timing (`250f105`)
- useAnalysis-Composable + analyzePath (`b259bf1`)
- Analyse-Tab mit Stage-Timing-Panel (`83aff1e`)
- weltweite Börsentabelle + OpenFIGI micCode/exchCode-Auflösung (US-Composite) (`5075d90`)
- strict\_exchange-Schalter (kein Fallback → 404) + /env (`dff90fe`)
- GET /exchanges als eine Quelle der Wahrheit für Börsen (`e761368`)
- FxRate-Modell + yfinance fetch\_fx\_rate + fx\_ttl\_hours (`672aaab`)
- fx\_rates-Cache + CachedFxService (TTL, serve-stale) (`add3577`)
- GET /fx-Endpoint (Validierung, 422/502) (`1729bee`)
- Börsen-Panel datengetrieben (/exchanges) + strict\_exchange sichtbar (`0745a4a`)
- Devisen-Tab (FxPanel) über /fx (`1850317`)
- nur europäische UCITS-ISINs scrapen, nicht-europäische überspringen (`aee2c84`)
- formatDateTime-Util für lokalisierte Zeitstempel (`26f747e`)
- currenciesFromExchanges-Util (dedupe, sort, GBp→GBP) (`d0c4fdd`)
- FxPanel Rate auf 3 Stellen + formatierte Kurszeit (`081d166`)
- FxPanel Währungs-Dropdowns aus /exchanges (GBp→GBP) (`522be21`)
- Header-Navigation mobil als Hamburger-Drawer (`f5037d8`)
- Environment-Tab erklärt Config-Herkunft und Strikte Börse (`23a4c5e`)
- Kurs-Graph zeigt %-Veränderung (Achse, Badge, Tooltip) (`1260294`)
- Devisen — konkreten Betrag umrechnen (`781b699`)
- useHashTab parst adressierbare Settings-Reiter (T-11a) (`6ab21b8`)
- SettingsPanel mit adressierbaren Reitern (T-11a) (`3ff915a`)
- #/settings rendert SettingsPanel (T-11a) (`facd0e2`)
- Hauptmenü auf 4 Arbeitsbereiche + Zahnrad statt DE/EN (T-11a) (`d59be94`)
- Hauptmenü linksbündig + #/settings-Hash normalisieren (T-11a) (`d91848c`)
- useIsCompact — md-Grenze als Composable (T-11c) (`8aebb47`)
- InstrumentCard für die mobile Kartenliste (T-11c) (`1e98ee9`)
- Assets unter md als Kartenliste + Sortierleiste (T-11c) (`bc35625`)
- Sortierung auch mobil persistieren (T-11c) (`8256f9c`)
- Loeschen eines Assets bestaetigen lassen (T-11i) (`60aac2b`)
- auf ux-foundation und Naive UI umgestellt (T-12) (`67af83a`)
- native Bedienelemente durch Naive UI ersetzt (`f4e2539`)
- Zustandsmeldungen als Toast, Dialoge auf NModal (T-13) (`02b120d`)
- „Alle aktualisieren" in die Kopfzeile, Meldungen darunter (`3566518`)
- Erklärungen am Begriff statt Beitext (T-13, aus T-11e) (`5378eb0`)
- Kennzahlen von Hand nachtragen — DB und Endpoint (T-09) (`dd7a7b1`)
- Kennzahlen an Ort und Stelle nachtragen (T-09) (`bbf25c3`)
- Spalten für alle ETF-Extras und deren Overrides (`2514a04`)
- alle acht ETF-Extras im Override-Modell (`7af3b08`)
- Endpoint nimmt alle acht Kennzahlen entgegen (`e7e5af4`)
- Fondsdomizil holen, Fondswährung getrennt führen (`0636fe4`)
- Kennzahlen-Editor mit Entfernen für verdeckte Werte (`d80b09a`)
- Schublade mit allen acht ETF-Kennzahlen (`29e8f74`)
- Symbol und Name öffnen die Schublade in der Tabelle (`8c74bba`)
- Kartenliste nutzt dieselbe Schublade wie die Tabelle (`23a14dc`)
- Vorschlagslisten der Schublade einmal oben bilden (`935a045`)
- Schublade erklärt sich immer, nicht nur im Ausnahmefall (`5c2d97f`)
- Schublade nennt die Quelle der Kennzahlen (`3df83fd`)
- Escape schließt die Schublade (`7dd389d`)

### Other changes

- inkrementelle EOD-Sync in wiederverwendbare DailyCloseSync ziehen (`0208dc0`)
- TabKey auf finale Arbeitsbereiche + Settings bereinigt (T-11a) (`1295824`)
- Nav-Icons an ux-standards angleichen — Schieberegler statt Zahnrad, Globus für Assets (T-11a) (`c17ef92`)
- Börsen-Icon als Kurstafel; veraltete Zahnrad-Kommentare (T-11a) (`4094aee`)
- Theme-Paletten als RGB-Tripel + ux-standards-Token (T-11b) (`842e491`)
- $color-\*/$health-\* auf Token, token()-Funktion (T-11b) (`20c59bb`)
- hartkodierte Farben auf Token (T-11b) (`3d3fd0a`)
- color-mix durch token(--x, alpha) ersetzt (T-11b) (`1b35029`)
- ISIN-Editor aus der Tabelle herausgezogen (T-11c) (`dc44acc`)
- mobile Sortierung als leise Textzeile statt Formularleiste (T-11c) (`e41b6ac`)
- Lage der Meldungen aus dem Fundament übernehmen (`9c300f2`)
- Overrides über OVERRIDE\_FIELDS statt Einzelparameter (`866d83f`)
- englische Bezeichner in neuem Overrides-Code (`e4c997a`)
- Tabelle zeigt Kennzahlen nur noch an (`6aacb48`)
- Override-Modell auf alle acht Felder erweitern (`5a1e437`)
- repository.py auf englische Bezeichner (`c02958c`)
- OverrideField aus OVERRIDE\_FIELDS ableiten (`25f86b8`)
- InstrumentOverrides aus OVERRIDE\_FIELDS ableiten (`e12f833`)
- Feldbeschriftungen an einer Stelle (`b3485b5`)
- Pfeil und Erklärzeichen kommen aus dem Fundament (T-16) (`d913827`)
- „Schublade" heißt jetzt „Detailbereich" (`41a35d4`)

### Fixes

- finale Fixwave nach Code-Review – Volatilität, Cleanup, UX (`8244fe4`)
- unbekannte Börse löst mit XETR-MIC statt Original-Key auf (`b27393f`)
- review-fixwave for exchanges panel and FX convert (`e64ca2b`)
- Dev-Proxy für /exchanges, /fx, /analyze durchreichen (`fb0f277`)
- Header-Breakpoint 1280px und ☰ links (`b2a515f`)
- Analyse-Dropdown auf Mobile nicht mehr über den Rand (`1aabbaa`)
- Chart-Flächenfarbe nach Token-Umstellung reparieren (T-11b) (`19601b4`)
- Karten-Fußzeile umbrechen lassen — 44px-Ziele passen sonst nicht (T-11c) (`4553fbc`)
- Sortier-Auswahl auf 44px Trefferflaeche (T-11c) (`9f9644b`)
- Chart-Dock-Werkzeugzeile umbrechen lassen (T-11c) (`bdda62e`)
- Sortier-Auswahl mit Platzhalter und sichtbarer Beschriftung (T-11c) (`12636fc`)
- Zeitraum-Auswahl im Dock bricht um statt abzuschneiden (T-11c) (`2487d0d`)
- Sortierzeile in die Ueberschriftenzeile (T-11c) (`7cd09b4`)
- Zeitraum-Knoepfe im Dock auf 44px Trefferflaeche (T-11c) (`505ebe1`)
- eine Sorte Knopf — eigenes CSS auf Naive-Komponenten entfernt (`9292aae`)
- Altlasten der Marke entfernt, Plakette und FavIcon auf ein Motiv (`085fa14`)
- Thesaurierung lässt sich wieder auf jeden Zustand stellen (`ef98e17`)
- in jeder Kurs-Antwort wirksam, nur in Lücken pflegbar (`3f292a5`)
- englische Bezeichner in der Migrations-Hilfsfunktion (`7bfe7f7`)
- Validierungstest auf Task 2 zuschneiden, Endpoint-Tests lockern (`fe36404`)
- lokale Variable in Test auf Englisch umbenennen (`a976054`)
- Textfelder im Editor als Auswahl mit freier Eingabe (`30b76f0`)
- Vorschläge auch mobil an die Kartenliste durchreichen (`7971fc7`)
- Wert bei gesperrten Feldern anzeigen (`3ae5c04`)
- Schublade nennt den richtigen Grund für die leere Quelle (`75f4b46`)
- getippte Fondswährung in Großbuchstaben übernehmen (`e5531b6`)
- Escape schließt erst die Auswahlliste, dann die Schublade (`b95d898`)
- Pfeil sitzt mittig in der Zeile und ist größer (`a1cdefa`)
- Metadaten überleben Duplikat-Merge und Provider-Ausfall (`07848d3`)
- unbrauchbare Zahlen, geratene Aussagen und ein blinder Healthcheck (`91ed077`)
- Symbole, Zeitgrenzen und Statuscodes prüfen statt durchreichen (`62a0444`)

### Performance

- den ungenutzten Gettex-Kurs nicht mehr mitholen (`7eb59bb`)

## v0.5.0+260715.1816.8829a — 2026-07-15

Chart-Dock, Copy-Fallback ohne https, dezente Scrollbars

### Fixes

- Kopieren funktioniert auch ohne https (Unraid) (`0cf017c`)

### Features

- Kurshistorie als Dock am unteren Rand (`9d1f30c`)
- Scrollbars dünn und nur beim Scrollen sichtbar (`7df461b`)

## v0.4.0+260715.1234.edcb6 — 2026-07-15

Spalten-Sortierung, Environment-Hinweis zum Auto-Refresh, sofortige Container-Logs, CA-Template auf :latest

### Other changes

- Template pinnt :latest statt exaktem Build-Tag (`58d9826`)

### Documentation

- Unraid-Template-Install als Hint (`fcd928e`)

### Fixes

- Container-Logs erscheinen sofort (PYTHONUNBUFFERED) (`4b680fb`)

### Features

- Hinweis auf automatischen Kurs-Update im Environment (`fff7680`)
- Spalten-Sortierung in der Assets-Tabelle (`9136741`)

## v0.3.0+260715.1136.9ac04 — 2026-07-15

Swagger-UI dark, DE/EN-Umschaltung (vue-i18n), Unraid-Template-Automatik

### Fixes

- JSON-Modal kopiert vollständige URL statt nur den Pfad (`2d017d2`)
- Sprach-Umschalter näher an die Navigation gerückt (`b6faba1`)

### Features

- Template folgt dem Image-Tag automatisch nach jedem Push (`c4b02a5`)
- Swagger-UI in Dark-Optik, ReDoc entfernt (`e0400b7`)
- DE/EN-Umschaltung mit vue-i18n (`1526dac`)

## v0.2.0+260715.1041.cf4ea — 2026-07-15

Versionen gleichgezogen

### Features

- Container-Template für Unraid hinzufügen (`316e56f`)
- PNG-Icon für Community-Applications-Kompatibilität (`1a64d24`)

### Documentation

- Template-Beschreibung und Parameter auf Englisch umgestellt (`1722fd9`)
- TZ-Default UTC + OpenFIGI-/Timezone-Hinweise in Overview (`433967d`)

### Fixes

- Versionen pinnen — Build-Abbruch durch pip-Backtracking behoben (`0be5c12`)
- Datenlücken, verlorene Cache-Kurse und Refresh-Kollisionen behoben (`3f0a0b9`)
- Chart-Races, unsichtbare Fehler und URL-Encoding behoben (`e4d52f5`)

### Other changes

- Registry-Login-Logik in BashLib auslagern (`45319f8`)
- totes API\_KEY-Setting entfernt (`67817c1`)
- pyproject.toml als Versions-Quelle statt VERSION-Datei (`679e17e`)

### Performance

- BuildKit-Cache-Mounts für npm/pip + UTF-8-Locale (`189b815`)

## v0.1.0 — 2026-07-13

Release v0.1.0: Single-Container-Deployment (Backend serviert Dashboard) + build.sh

### Features

- StockInfo-Grundgerüst mit REST-Health-Endpoint und Makefile-Steuerung (`e5947bf`)
- ISIN-/Symbol-Kursabfrage mit OpenFIGI-Xetra-Auflösung und justETF-TER (`8bfd6de`)
- Kurs-Endpoints mit SQLite-Cache (Lazy-TTL), Stale-Fallback und Historie (`313e21d`)
- periodischer Hintergrund-Refresh aller bekannten Instrumente (`42a7b7d`)
- Dashboard-Response-Modelle (InstrumentSummary, EnvInfo, RefreshResult) (`fe010f4`)
- Instrumentenübersicht mit letztem Kurs und Löschen per ISIN (`6a31c82`)
- refresh\_one, Instrumentenliste, Löschen + CORS-Origins-Setting (`79696c8`)
- Dashboard-Endpoints (instruments, env, refresh, delete) + CORS (`c748b9f`)
- Vue+Vite+TS+SCSS-Gerüst (`b2d3695`)
- Typen und typisierter API-Client (`ef70098`)
- Composables für Instrumente, Environment und Historie (`5b13896`)
- Aktions-Composables (Refresh, Hinzufügen, Löschen) (`7d2a989`)
- UI-Komponenten (Toolbar, Environment, Tabelle, Chart) + App-Verdrahtung (`3cfee60`)
- Dockerfile, docker-compose (persistenter SQLite-Cache) + Makefile up/down/logs (`73f0909`)
- make dev-up/dev-down (overmind) und Docker-Stack inkl. Dashboard (`89d47ce`)
- API- & Links-Bereich (docs, redoc, openapi, health) (`9fddd50`)
- MangoLila-Dark-Redesign — Header, Statuszeile, Health-Ampel, Tabs (`df5c4ea`)
- Refresh und Delete auch per Symbol (für Papiere ohne ISIN) (`5f6782b`)
- Home-Link, Tab-Icons, Favicon, 8 persistente Themes, Aktionen für alle Zeilen (`854b7bf`)
- Kurs-Historie auch per Symbol (für Papiere ohne ISIN) (`9510ea1`)
- mehr Kontrast, Refresh-Indikator und Historie für ISIN-lose Papiere (`aa74be0`)
- Langfrist-Historie mit echten Tages-Schlusskursen (yfinance-EOD), inkrementell gecacht (`8fd0738`)
- Zeitraum-Umschalter + echte Zeitachse (Tagesverlauf vs. Schlusskurse) (`e605fa6`)
- Börsen-Legende-Tab, Tab 'Assets', deep-linkbare Hash-Routen (`8f9a784`)
- Profil-Links pro Asset (extraETF ETF/Stock, Yahoo), .env-konfigurierbar (`a414cf7`)
- ISIN nachträglich erfassen (manuell) für Assets ohne ISIN (`636abcd`)
- JSON-Abfrage pro Asset im Popup (URL + JSON kopierbar) (`afda1b0`)
- GitHub-Repo und Issues im 'API & Links'-Tab verlinken (`749d917`)
- eigenes StockInfo-Logo (Header + Favicon) und 'powered by MangoLila'-Link (`5bcceea`)
- Volatilität und Thesaurierend/Ausschüttend erfassen (`3675111`)
- Dashboard als statische Dateien ausliefern (konditionaler Mount) (`ca7f90e`)
- relative API-URLs + vite-Dev-Proxy für lokalen Dev-Flow (`68b9648`)
- vereinheitlichtes Multi-Stage-Image (Backend serviert Dashboard) (`9e4b4de`)
- build.sh (Build/Push nach Ökosystem-Konvention) (`0243e21`)

### Documentation

- Spec für Vue-Dashboard (DB/Environment-Visualisierung, Refresh, History-Graph) (`e6628b6`)
- detaillierter Umsetzungsplan (Backend-Endpoints + Vue-Frontend, TDD) (`7aa644b`)
- allgemein verständliches README hinzugefügt (`fc4e8a6`)
- Dashboard-URL in make hints ergänzen (`da30fb2`)
- hints klarer — Backend/Dashboard getrennt, http-Hinweis, Dashboard-Startbefehl (`ba4bae2`)
- README auf aktuellen Funktionsstand aktualisiert (`c1c81b3`)
- Spec für Single-Container-Deployment + build.sh (`31103ad`)
- Umsetzungsplan für Single-Container-Deployment (`a224237`)

### Other changes

- effizienter Instrument-Count für /refresh und sauberer Test-Output (`bc70077`)

### Fixes

- GITHUB\_OWNER für GHCR-Image-Referenz lowercasen (`114bcf5`)
- docs-Links im Dev proxien + README-Dev-Anleitung korrigieren (`044b1ec`)
