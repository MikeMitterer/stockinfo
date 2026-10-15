#!/usr/bin/env bash
# Config für docs-check.sh (ProjectTools) — wird gesourced, kein Custom-Parser.
# .sh-Endung fürs IDE-Highlighting. Format-Doku: ProjectTools/README.md
# Aufruf: make docs-check (läuft auch in make test, make check und vor jedem Commit)
# shellcheck disable=SC2034  # von docs-check.sh gesourct

# Pfadangaben in DOCS, LINKS_ONLY, EXCLUDE, REQUIRED, CODE_VARIABLES,
# SCREENSHOTS, DEPENDS und DEPENDS_HINT gelten ab dem Projekt-Root.
# Muster wie in .gitignore: * innerhalb eines Ordners, ** beliebig tief,
# ? genau ein Zeichen. Ordner und Muster treffen nur Dateien, die git nicht
# ignoriert.

# ─── Welche Dokumente geprüft werden ───────────────────────────────────────────

# Inhaltlich geprüfte Dokumente: die Anleitungen für Nutzer, Betreiber,
# Entwickler und Plugin-Autoren, die Lizenzerklärung und die README-Vorlage.
# AGENTS.md und _tickets/ sind intern und dürfen Ticketnummern nennen;
# CHANGELOG.md entsteht aus Commit-Nachrichten (make changelog) und darf alte
# Angaben behalten. Diese Dateien stehen nicht in DOCS, sondern in REQUIRED
# und teils in LINKS_ONLY.
DOCS=(
    "README.md"
    "README.de.md"
    "docker/README.md"
    "unraid/README.md"
    "contract/README.md"
    "docs"
    "LICENSING.md"
)

# Interne Doku: nur tote Links und Anker prüfen; Ticketnummern und
# Make-Targets sind hier erlaubt. Verweise auf andere Dokumente als Link
# schreiben, sonst fällt ein veralteter Verweis nicht auf. _tickets/ fehlt
# bewusst: Erledigte Tickets verlinken auf Dateien, die es heute nicht mehr
# gibt, und bleiben als Verlauf unverändert.
LINKS_ONLY=(
    "AGENTS.md"
    "CLAUDE.md"
)
# Die Arbeitsdokumente unter docs/ (stockinfo-currency-request.md,
# stockportfolio-quote-projection-review.md, markdown-styles/) stehen
# bewusst nicht hier: Der Ordner "docs" in DOCS geht vor, und sie bestehen
# die volle Prüfung.

# Datierte Entwürfe und Pläne dürfen interne Angaben enthalten und
# beschreiben teils verworfene Stände. Die erzeugte Docker-Hub-Vorschau ist
# eine Kopie von docker/README.md mit absoluten Links; geprüft wird ihre
# Quelle, die Vorschau selbst über DEPENDS.
EXCLUDE=(
    "docs/superpowers"
    "docker/preview"
)

# ─── Was in den Dokumenten stehen darf ─────────────────────────────────────────

# Text, der in keinem Dokument aus DOCS stehen darf. Geprüft wird jede Zeile,
# auch in Codeblöcken; jeder Treffer lässt make test scheitern. Die Meldung
# nennt Zeilen, gefundenen Text und Grund.
#
# Ein Eintrag hat eine von zwei Formen, jeweils optional mit "|<grund>":
#
#   "<text>"             Genau dieser Text, Groß-/Kleinschreibung zählt.
#                        Trifft auch innerhalb von Wörtern: "UID" trifft
#                        "PUID".
#
#   "/<muster>/<flags>"  Regulärer Ausdruck in JavaScript-Syntax:
#                          \b      Wortgrenze: "/\bUID\b/" trifft nicht "PUID"
#                          (a|b)   Alternative: "/\bP(U|G)ID\b/"
#                          a|b     ganze Alternativen: "/PUID|nobody:users/"
#                          \d+     Ziffern: "/\b99:\d+\b/"
#                        Flag i: Groß-/Kleinschreibung egal.
#                        "|" im Muster ist erlaubt: Das Muster endet am
#                        ersten "/", dem nur Flags und dann "|" oder das
#                        Zeilenende folgen. Ein "/" im Muster wird "\/".
#                        Ein ungültiger Ausdruck bricht mit Exit-Code 2 ab.
#
# In doppelten Anführungszeichen bleiben "\b" und "\d" erhalten;
# Dollarzeichen und Backticks brauchen einen Backslash davor.
#
# Anleitungen beschreiben Benutzung und aktuelles Verhalten; interne
# Arbeitsabläufe und Review-Geschichte gehören in die Tickets (AGENTS.md,
# Abschnitt „Dokumentation gehört zur Änderung“).
FORBIDDEN=(
    # Ticketnummern und Verweise ins Ticket-Board
    "/\bT-\d+[a-z]?\b/|interne Ticketgeschichte, gehört nicht in Nutzerdoku"
    "_tickets/|Ticket-Board ist intern, gehört nicht in Nutzerdoku"
    # Alte Fassungen der EUPL-Pflichten ohne Bedingung (Mike, 2026-10-15)
    "/if you change or redistribute|wer \S+ ändert oder weitergibt|preserve the required notices/i|EUPL-Pflichten ohne Bedingung: Satz aus dem Lizenz-Baustein verwenden"
)

# Höchstens zwei farbige Hinweisboxen je Dokument; mehr nehmen jeder
# einzelnen die Wirkung.
MAX_ALERTS=2

# ─── Variablen zwischen Doku und Code ──────────────────────────────────────────

# Variablen, die die Doku nennt, die aber in keiner versionierten Datei
# vorkommen: Variablen anderer Apps, Platzhalter und Beispielnamen.
KNOWN_VARIABLES=(
    # Gehört zu StockPortfolio; docker/README.md nennt sie für den Betrieb
    # beider Apps.
    "STOCKINFO_API_URL|Variable von StockPortfolio, nicht von StockInfo"
    # Platzhalter in Beispielbefehlen der Unraid-Anleitung
    "YOUR_UNRAID_SERVER|Platzhalter für die eigene Serveradresse"
    # Beispielnamen in der Plugin-Anleitung; ein Plugin-Autor wählt eigene
    "MY_MARKET_API_KEY|Beispiel in docs/plugin-authors.md"
    "US_MARKET_BASE_URL|Beispiel in docs/plugin-authors.md"
)

# Code, dessen Umgebungsvariablen in einem Dokument aus DOCS stehen müssen:
# Backend, Plugin-Vertrag, Dashboard und Projektskripte. Jede Variable, die
# der Code dort liest, braucht eine Beschreibung (meist docs/development.md,
# docker/README.md oder docs/plugin-authors.md); sonst scheitert make test.
#
# Grenzen: Erkannt werden nur ausdrückliche Lesezugriffe in einer Zeile wie
# os.environ["X"] oder import.meta.env.X.
# - Die Felder der Settings-Klasse in app/config.py liest pydantic-settings
#   ohne solchen Aufruf. Neue Einstellungen dort von Hand in
#   docs/development.md und docker/README.md eintragen (Configuration).
# - Shell-Variablen ($X) zählen nicht; docker/entrypoint.sh steht deshalb
#   nicht in der Liste, seine Variablen deckt docker/README.md ab.
CODE_VARIABLES=(
    "app"
    "plugin_api/src"
    "dashboard/src"
    "scripts"
)

# Vom Code gelesen, bewusst nicht dokumentiert, je mit "|<grund>".
# Nicht hier, weil docs-check den Lesezugriff über zwei Zeilen nicht sieht:
# CONTRACT_PATH (app/contract.py), Pfad des Vertragsartefakts, nur nötig,
# wenn die App nicht neben contract/ liegt.
INTERNAL_VARIABLES=(
)

# ─── Dateien, die es geben muss ────────────────────────────────────────────────

# Dateien, die es geben muss: versioniert, nicht leer, Markdown mit
# Überschrift. Ohne "/" irgendwo im Projekt, "./" heißt Projekt-Root.
REQUIRED=(
    # Projekt- und Nutzerdoku
    "./README.md|Projekt-README"
    "./README.de.md|Projekt-README auf deutsch"
    "docker/README.md|Container-Anleitung, Quelle der Docker-Hub-Beschreibung"
    "docker/preview/README.md|Docker-Hub-Beschreibung, aus docker/README.md erzeugt"
    "unraid/README.md|Unraid-Anleitung"
    "docs/development.md|Entwicklerdoku, im README verlinkt"
    "contract/README.md|Prüfung der Vertragsdateien, in der Entwicklerdoku verlinkt"
    "docs/plugins.md|im README verlinkt"
    "docs/plugin-authors.md|im README verlinkt"
    "docs/rest-core-contract.md|im README verlinkt"
    "docs/release-notes.md|im README verlinkt"

    # ChangeLog - wird mit make changelog generiert
    "./CHANGELOG.md|Release-Historie, im README verlinkt"

    # Neben der Vorlage im Skill - die Vorlage für das README dieses Projektes
    "docs/README.template.md|Vorlage für den Skill readme-conventions"

    # Lizenz
    "./LICENSE|EUPL 1.2, englischer Lizenztext"
    "./LICENSE.de.txt|EUPL 1.2, amtlicher deutscher Lizenztext"
    "./LICENSING.md|Anbieter- und Verbrauchererklärung"

    # Projektregeln für Agenten
    "./AGENTS.md|Projektregeln"
    "./CLAUDE.md|verweist Claude auf AGENTS.md"

    # Ticket-Board
    "_tickets/README.md|Ablage und Ablauf der Tickets"
    "_tickets/STATUS.md|Rollen und Kommunikationsstatus"
    "_tickets/.agents/AGENT-ACTIVATION.md|Startwege der Agenten, in AGENTS.md genannt"
    "_tickets/.agents/AGENT-WORKFLOW.md|gemeinsamer Ablauf von Coder und Verifier, in AGENTS.md genannt"
    "_tickets/.agents/CLAUDE-LESSONS.md|Einstieg in Claudes Lessons, in AGENTS.md genannt"
    "_tickets/.agents/CODEX-LESSONS.md|Einstieg in Codex' Lessons, in AGENTS.md genannt"
    "_tickets/.agents/LESSONS-ACCESS.md|Lese- und Pflegeregeln der Lessons, in AGENTS.md genannt"
)

# ─── Abhängige Dateien und Screenshots ─────────────────────────────────────────

# Abhängige Dateien müssen ihrer Basis folgen: Screenshots dem UI-Code,
# Übersetzungen und Kurzfassungen ihrem Original, erzeugte Dateien ihrer
# Quelle. Ändert sich die Basis nach der abhängigen Datei, meldet die Prüfung
# das. Maßgeblich ist der letzte Commit laut git, uncommittete Änderungen
# zählen als jetzt; Dateidatum und Tagesdatum zählen nicht.
#
# Quittieren statt sinnlos anfassen: Verlangt eine Änderung der Basis nichts
# (Tippfehler im README, Codeänderung ohne sichtbare Folge), die Meldung aus
# SCREENSHOTS, DEPENDS oder DEPENDS_HINT nach dem Prüfen quittieren:
#
#   .libs/ProjectTools/src/bash/docs-check.sh --ack unraid/screenshots/dashboard.png
#   .libs/ProjectTools/src/bash/docs-check.sh --ack unraid/screenshots   # ganzer Ordner
#   .libs/ProjectTools/src/bash/docs-check.sh --ack                      # alle offenen
#
# Das schreibt je Paar den letzten Commit der Basis nach .docs-check.ack; die
# Datei mitcommitten. Die Quittung gilt, bis die Basis einen neueren Commit
# hat, dann kommt die Meldung zurück. Nicht quittieren lassen sich Einträge mit
# Frist 0 (die Vorschau neu erzeugen) und uncommittete Basen (erst committen).

# Screenshots der Anleitungen und der Code, dessen Oberfläche sie zeigen, je
# "<ui-code>|<bilder>|<grund>" (UI-Code: mehrere Pfade mit Komma). Hat sich
# der Code nach einem Bild geändert, erscheint ein Hinweis: prüfen, ob das
# Bild die Oberfläche noch richtig zeigt, sonst neu aufnehmen. Verglichen
# wird mit dem letzten Commit des Codes, nicht mit dem Tagesdatum; die
# Prüfung scheitert daran nie.
SCREENSHOTS=(
    # Dashboard-Übersicht und aufgeklappter Detailbereich
    "dashboard/src/App.vue,dashboard/src/components,dashboard/src/i18n,dashboard/src/styles|unraid/screenshots/dashboard.png|Dashboard"
    "dashboard/src/App.vue,dashboard/src/components,dashboard/src/i18n,dashboard/src/styles|unraid/screenshots/detail-area.png|Detailbereich im Dashboard"
    # Swagger-Seite: eigene /docs-Route und die Routen, die sie auflistet
    "app/docs.py,app/main.py,app/routers|unraid/screenshots/swagger.png|API-Dokumentation"
)

# Dateien, die ihrer Basis bald nach deren Änderung folgen müssen, je
# "<basis>|<abhängig>|<tage>|<grund>". Ändert sich die Basis später, ist das
# ein Hinweis, nach <tage> Tagen ein Problem; 0 heißt: im selben Commit.
DEPENDS=(
    # Erzeugt mit dem Vorschaubefehl aus AGENTS.md (Docker-Hub-Beschreibung).
    # make push ruft docker/build.sh --push auf; das lädt nach dem Image
    # docker/README.md als Beschreibung zu Docker Hub hoch.
    "docker/README.md|docker/preview/README.md|0|Vorschau neu erzeugen"

    # Deutsche Fassung des Projekt-README
    "README.md|README.de.md|3|deutsche Fassung"

    # Kurzfassungen der Anbieter- und Verbrauchererklärung
    "LICENSING.md|README.md|3|Lizenzabschnitt"
    "LICENSING.md|README.de.md|3|Lizenzabschnitt"
    "LICENSING.md|docker/README.md|3|Lizenzabschnitt"
)

# Gleiches Format, auch überfällig nur ein Hinweis: Die Basis ändert sich oft,
# ohne dass die abhängige Datei etwas nachziehen muss.
DEPENDS_HINT=(
    # docker/README.md übernimmt Aussagen aus README.md (Schnellstart,
    # Warnung, Schwester-App)
    "README.md|docker/README.md|14|übernommene Aussagen"

    # Die READMEs folgen der Projektvorlage
    "docs/README.template.md|README.md|30|Gliederung nach der Vorlage"
    "docs/README.template.md|README.de.md|30|Gliederung nach der Vorlage"

    # Die Funktionsliste nennt Seiten und Einstellungen im Wortlaut der App
    "dashboard/src/i18n/en.ts|README.md|30|Bedienelemente im Wortlaut der App"
    "dashboard/src/i18n/de.ts|README.de.md|30|Bedienelemente im Wortlaut der App"

    # Die Entwicklerdoku beschreibt die Make-Targets
    "Makefile|docs/development.md|30|Befehle"

    # Unraid-Betrieb teilt Aussagen mit der Container-Anleitung
    "docker/README.md|unraid/README.md|30|gemeinsame Aussagen zum Betrieb"
)

# Sprachfassungen mit derselben Gliederung: Überschriften und je Abschnitt
# Linkziele, Bilder, Code, Hinweisboxen, Anker und Absätze müssen
# übereinstimmen; jede Abweichung ist ein Problem.
TRANSLATIONS=(
    "README.md|README.de.md|deutsche Fassung"
)
