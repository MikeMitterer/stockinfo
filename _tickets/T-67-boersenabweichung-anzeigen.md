# T-67 · Abweichende Börse sichtbar machen

Ein aufgenommenes Papier kann an einer anderen Börse notieren als aktuell
bevorzugt. Die Assets-Ansicht soll diesen Unterschied sichtbar machen:
etwa NYSE Arca (ARCX) gegenüber Xetra (XETR), mit beiden Währungen.

Die Anzeige ist noch nicht umgesetzt. Sie folgt unmittelbar auf die
MIC-Katalogbereinigung in [T-21](T-21-identitaet-mic-und-ticker.md).
Codex implementiert, Claude prüft; die Kette steht in [STATUS.md](STATUS.md).
Aktuell ist keine zusätzliche Prüfung durch Mike angesetzt.

## Auftrag und Umfang

Abgetrennt durch Claudes Scope-Checkpoint zu T-21 am 2026-09-09, Prüfstand
8af898c, Entscheidung split. Keine Vertagung oder neue Produktentscheidung:
Mike hat den sichtbaren Vergleich bereits beauftragt. T-21 #2e verweist hierher.

**Scope-Vertrag:** Gemeinsame Ableitung und Darstellung des MIC-Vergleichs in
Desktop-Tabelle und mobilen Karten. Die vorhandene REST-Auskunft liefert
Präferenz und Katalog; InstrumentSummary die echte Identität und Kurswährung.
Tatsächlicher MIC und aktueller bevorzugter MIC werden verglichen. Beide
Kennungen, Anzeigenamen und Währungen erscheinen, DE/EN. Fehlende Werte
bleiben unbekannt, kein Ersatz der Kurswährung durch Katalogwerte. Pair und
isin_only tragen keinen Börsenvergleich. Ein ausdrücklich gewähltes Listing
kann abweichen: Der Hinweis benennt die aktuelle Präferenz, keinen Fehler
oder behaupteten historischen Aufnahmegrund.

**Zusätzlich von Mike ausdrücklich beauftragt, ohne weitere Tickets:**

- „API & Links“ ganz rechts in der Reihe der Einstellungs-Tabs.
- GitHub-Symbol mit Repo-Link direkt hinter „powered by MangoLila“.
- Unter der Einleitung der Börsenseite erklären, dass weitere Handelsplätze
  über Plugins implementiert werden können; Link auf docs/plugin-authors.md.

Der zusätzliche UI-Auftrag erweitert den ursprünglichen 7/5/600-Zuschnitt
vor Arbeitsbeginn auf **12 Produktdateien, 5 Test-/Dokudateien, 800 manuelle
Diff-Zeilen**. Flächen: AppDashboard, InstrumentsTable, InstrumentCard,
ExchangeDeviation, utils/exchangeDeviation, DE/EN, useHashTab, StatusBar,
ExchangesPanel, config und LinksPanel. Repo-/Dokulinks werden gemeinsam
definiert. Vorhandene Foundation-Slots und Komponenten werden verwendet.
Keine Backend-/API-/Schema-/Migrationsänderung, keine Abhängigkeit oder
Änderung im Foundation-Repo. Neue Fähigkeiten erhalten gezielte Tests,
die kleinen Link-/Reihenfolgeänderungen bestehende Prüfungen und Browser-Smoke.

## Verifikation

| # | Beobachtbares Ergebnis | AI |
|---|---|:--:|
| 2e | ARCX bei XETR zeigt beide MICs, Namen und die echte Kurswährung, Desktop/Mobil DE/EN | ➖ |
| matching | Gleicher MIC, pair und isin_only lösen keine Abweichung aus | ➖ |
| missing | Keine erfundene Abweichung bei fehlendem Katalog/unbekannter Präferenz; Nachladen aktualisiert | ➖ |
| interaction | Hinweiserklärung bedienbar ohne Chartöffnung; normale Zeilenauswahl bleibt möglich | ➖ |
| extras | Tab-Reihenfolge, GitHub-Link und Plugin-Autorenhinweis in DE/EN, Desktop/Mobil | ➖ |

Rote Tests am Eintritt InstrumentsTable mit echten Karten-/Hinweiskomponenten,
negativer Mutant, Dashboard-Suite mit ESLint und Build. Isolierter Browserlauf
mit temporären Daten, beide Sprachen und Breiten; keine Arbeitsdaten ändern.
Danach unabhängiges Review über STATUS.md.
