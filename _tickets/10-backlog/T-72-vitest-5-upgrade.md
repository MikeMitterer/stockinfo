# T-72 · Dashboard-Tests auf Vitest 5 umstellen

Das Dashboard soll **Vitest 5 verwenden**, damit die bekannte kritische
Schwachstelle im bisherigen Testwerkzeug behoben ist und die Tests weiterhin
zuverlässig laufen.

Am 2026-09-25 nannte `dashboard/package.json` noch `vitest@^2.1.8`;
das Lockfile installierte Version 2.1.9.
`npm audit` meldete dafür den kritischen Befund
[GHSA-5xrq-8626-4rwp](https://github.com/advisories/GHSA-5xrq-8626-4rwp).
Das Paket ist eine Entwicklungsabhängigkeit: `npm audit --omit=dev` meldete
keinen Befund für Produktionsabhängigkeiten. Das ist kein Anlass, den
ausgelieferten Container sofort zu ersetzen, aber ein Grund für ein gezieltes
Upgrade der Testumgebung.

**Stand:** Noch nicht umgesetzt oder eingeplant. T-71 und seine laufende
Review-Übergabe bleiben unverändert. Für Mike ist aktuell kein Handgriff nötig.

## Umsetzung und technische Nachweise

| Repo | Time-box | Scope | GH-Issue |
|---|---|---|---|
| StockInfo | 1–2 h | Dashboard-Testwerkzeuge und nötige Kompatibilitätsanpassungen | — |

`dashboard/package.json` und `dashboard/package-lock.json` auf einen aktuellen
Patchstand von Vitest 5 (mindestens 5.0.2) umstellen. Testkonfiguration und
Tests nur anpassen, soweit der Versionswechsel es erfordert. Andere
Abhängigkeiten nur ändern, wenn eine belegte Kompatibilitätsanforderung
besteht. Keine App-Funktion und keinen API-Vertrag ändern.
`npm audit fix --force` ist kein Ersatz für die gezielte Prüfung des
Versionswechsels.

### Verify

Legende: ➖ noch keine Live-Verifikation. Die Ausgangsmessung oben ist kein
Nachweis für die spätere Umsetzung.

| # | Handgriff | Erwarteter Nachweis | AI |
|---|---|---|:--:|
| 1 | Im Verzeichnis `dashboard/` `npm ci` und `npm ls vitest --depth=0` ausführen | Lockfile ist reproduzierbar; Vitest 5 ist installiert | ➖ |
| 2 | Dort `npm test` ausführen | Alle Dashboard-Tests bestehen; nötige Anpassungen sind auf den Versionswechsel begrenzt | ➖ |
| 3 | Dort `npm run build` und `npm run lint` ausführen | Dashboard-Build, Typprüfung und Lint bestehen | ➖ |
| 4 | Dort `npm audit` und `npm audit --omit=dev` ausführen | Der kritische Vitest-Befund ist weg; verbleibende Befunde sind einzeln eingeordnet; Produktionsabhängigkeiten bleiben ohne Audit-Befund | ➖ |
| 5 | Aus dem Projektroot `make build` ausführen | Der Docker-Build über den vorhandenen Makefile-Pfad funktioniert mit dem neuen Lockfile | ➖ |

Die Ergebnisse mit Commit, Versionen und relevanten Befunden hier eintragen.
Ein grüner Testlauf allein ersetzt weder den Audit- noch den Docker-Nachweis.

### Akzeptanzkriterien

- [ ] Vitest 5 steht im Manifest und im Lockfile; `npm ci` installiert ihn.
- [ ] Die Dashboard-Tests sowie Build und Lint bestehen.
- [ ] GHSA-5xrq-8626-4rwp wird für die installierte Vitest-Version nicht mehr gemeldet.
- [ ] `make build` funktioniert; andere Audit-Befunde sind dokumentiert und nach Wirkung eingeordnet.
- [ ] Die aktuellen Testanleitungen in der README sind geprüft und bei geändertem Aufruf angepasst.

### Side-Effects

Der Wechsel betrifft die lokale Testumgebung und die Dashboard-Build-Stage,
nicht das ausgelieferte Python-/Dashboard-Laufzeitimage. Kein Deployment,
Registry-Push oder automatisches Update anderer Projekte. Falls Vitest 5 weitere
Werkzeug-Upgrades erzwingt, deren Umfang vor der Umsetzung im Ticket begründen.

### Auflösung

Offen. Noch keine Umsetzung oder Verifikation. Die unabhängige Prüfung folgt
erst nach Aktivierung und Übergabe gemäß `_tickets/STATUS.md`.
