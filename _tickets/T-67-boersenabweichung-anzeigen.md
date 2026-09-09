# T-67 · Abweichende Börse sichtbar machen

Ein aufgenommenes Papier kann an einer anderen Börse notieren als aktuell
bevorzugt. Nach dem Absenden der Asset-Erfassung soll eine Meldung diesen Unterschied
sichtbar machen:
etwa NYSE Arca (ARCX) gegenüber Xetra (XETR), mit beiden Währungen.

Die Meldung wird nach T-21 und T-65 umgesetzt, gemäß Mikes Prioritätskette.
Codex implementiert, Claude prüft; die Kette steht in [STATUS.md](STATUS.md).
Aktuell ist keine zusätzliche Prüfung durch Mike angesetzt.

## Auftrag und Umfang

Abgetrennt durch Claudes Scope-Checkpoint zu T-21 am 2026-09-09, Prüfstand
8af898c, Entscheidung split. Keine Vertagung oder neue Produktentscheidung:
Mike hat den sichtbaren Vergleich bereits beauftragt. T-21 #2e verweist hierher.

**Nachsteuerung Mike, 2026-09-09:** Der Hinweis erscheint beim Absenden der
Erfassung, vor dem Speichern. Mike: „Der User kann dann entscheiden ob er das
Asset dennoch aufnehmen möchte oder den Vorgang abbricht. Entscheidet er sich
für die Aufnahmen dann ist das Thema erledigt“.
Die verworfene Listen-/Tooltipdarstellung ist entfernt.

**Vorgeschlagener Scope-Vertrag:** Beim Submit prüft der normale Aufnahmeweg
vor seiner Speicherung, ob das neue Listing vom bevorzugten MIC abweicht.
Dann erscheint ein Dialog mit tatsächlichem und bevorzugtem Handelsplatz,
MIC und Währung sowie „Dennoch aufnehmen“ / „Abbrechen“. Abbruch schreibt
nichts; Bestätigung nimmt das konkret angezeigte Listing auf. Danach kein
Listenhinweis und keine erneute Rückfrage beim Lesen oder Aktualisieren.
Gleicher MIC, pair, isin_only und bereits vorhandene Listings brauchen keine
Rückfrage. Fehlende/unbekannte Präferenz erzeugt keine erfundene Abweichung.

**Technischer Zuschnitt zur Scope-Prüfung:** Der bestehende POST erhält eine
optionale angeforderte Börsenprüfung (`check_exchange`) und die bestätigte
Listing-Identität (`confirmed_listing`). Das Dashboard fordert die Prüfung
an; direkte API-Aufnahme bleibt eine direkte Aufnahme. Bei nötiger Entscheidung
antwortet er mit 202 und einer typisierten Bestätigungsanforderung statt einer
InstrumentSummary. Der gemeinsame Cache-/Speicherweg ruft vor dem ersten
Schreiben eine vom IntakeService gelieferte Prüfung mit dem fertigen Kurs auf.
So stehen die echte Währung und das Listing fest, ohne eine Zeile anzulegen.
Bei Bestätigung wird erneut geprüft und nur das bestätigte Listing akzeptiert;
eine geänderte Auflösung braucht eine neue Entscheidung. Kein Draft-Repository,
Token-Speicher oder DB-Schema, kein Speichern mit anschließendem Zurücklöschen.
Bestehende Abdeckungs- und Identitätsprüfungen bleiben im selben Pfad.

**Zusätzlich von Mike ausdrücklich beauftragt, ohne weitere Tickets:**

- „API & Links“ ganz rechts in der Reihe der Einstellungs-Tabs.
- GitHub-Symbol mit Repo-Link direkt hinter „powered by MangoLila“.
- Unter der Einleitung der Börsenseite erklären, dass weitere Handelsplätze
  über Plugins implementiert werden können; Link auf docs/plugin-authors.md.

Der Plugin-Hinweis übernimmt Prüfpunkt #5 aus
[T-64](solved/T-64-boersen-ui-und-autorennachweise.md). Mikes Ergänzung dort meint
Handelsplätze und MICs sowie den Link zur Anleitung auf GitHub. Mike hat T-64
am 2026-09-09 geschlossen und diesen Rest ausdrücklich hierher abgegeben.
Umsetzung und Nachweis stehen ausschließlich bei `extras`; keine Doppelprüfung.

**Scope-Checkpoint vor Backendarbeit, Basis 9f13a7f:** vorgeschlagen höchstens
16 Produktdateien, 6 Test-/Dokudateien, 900 manuelle Diff-Zeilen. Drei
Fachänderungen: Aufnahmeentscheidung vor Speicherung, Dialog/Bestätigung,
Mikes drei kleine UI-Ergänzungen. Produktflächen: IntakeService, QuoteCache,
Aufnahme-Router, Container, Python-/TS-Modelle, useInstrumentActions,
AppDashboard, ConfirmExchangeDialog, DE/EN, useHashTab, StatusBar,
ExchangesPanel, config und LinksPanel. Tests: echte Aufnahme mit temporärer
DB, Composable und Dialog, bestehende StatusBar-Tests; T-67 und REST-Vertrag.
Neue Backend-/API-Fläche ersetzt die reine UI-Annahme; deshalb Scope-Prüfung.
Keine neue Abhängigkeit, Migration oder Änderung im Foundation-Repo.

## Verifikation

| # | Beobachtbares Ergebnis | AI |
|---|---|:--:|
| 2e | Nach Submit zeigt der Dialog ARCX bei XETR mit beiden MICs, Namen und echter Kurswährung vor dem Speichern, Desktop/Mobil DE/EN | ➖ |
| matching | Gleicher MIC, pair und isin_only lösen keine Abweichung aus | ➖ |
| missing | Keine erfundene Abweichung bei fehlendem Katalog/unbekannter Präferenz | ➖ |
| interaction | Vor Submit keine Rückfrage; Abbrechen schreibt nichts, Bestätigung speichert nur das bestätigte Listing; danach keine erneute Warnung | ➖ |
| extras | Tab-Reihenfolge, GitHub-Link und Plugin-Autorenhinweis in DE/EN, Desktop/Mobil | ➖ |

Rote Tests am öffentlichen Aufnahme-Composable mit echtem API-Client und
kontrollierten Fetch-Antworten, negativer Mutant, Dashboard-Suite mit ESLint
und Build. Isolierter Browserlauf über das echte Formular mit temporären
Daten, beide Sprachen und Breiten. Danach unabhängiges Review über STATUS.md.
