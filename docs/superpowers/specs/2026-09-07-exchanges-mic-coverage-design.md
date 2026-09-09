# Exchanges: MIC-Katalog und Plugin-Abdeckung

Entwurf vom 2026-09-07 für Mikes Auftrag während T-56. Gehört fachlich zu
T-30; keine Umsetzung oder Freigabe von T-30 wird damit behauptet.

## Ergebnis

Die Seite zeigt Handelsplätze über ihre MICs und kennzeichnet, welche der
aktiven Plugins eine Unterstützung erklären. Die bloße Existenz im Katalog
ist keine Aussage über Quellenunterstützung. Yahoo-Suffixe sind optionale
Anbieterangaben, keine Identität eines Handelsplatzes.

## Katalogumfang

Für die erste Umsetzung wird der bestehende StockInfo-Katalog verwendet.
Mike hat den weltweiten ISO-Katalog als zu umfangreich eingeordnet. Die Seite
bezeichnet den Bestand deshalb nicht als vollständiges ISO-Verzeichnis.
Ein ISO-Import samt Aktualisierung und Statuspflege ist nicht Teil dieses
Zuschnitts. Suche und Kennzeichnung der Quellenunterstützung gelten für die
vorhandenen Einträge.

Der Referenzkatalog erweitert nicht automatisch die bisher akzeptierten
Eingabeformen oder die Alias-Rückrechnung in `app/exchanges.py`.

## Plugin-Auskunft

Der heutige Vertrag kennt `SUPPORTED_KINDS`, `SUPPORTED_TYPES` und
anfrageabhängiges `handles()`, aber keine allgemeine MIC-Abdeckung.
`handles()` mit einem erfundenen Ticker aufzurufen wäre kein Nachweis einer
Handelsplatzunterstützung.

Erforderlich ist eine ausdrückliche, optionale Deklaration je Rolle:

- Genannte MICs: vom Plugin unterstützte Handelsplätze für diese Rolle.
- Leere Deklaration: keine MIC-basierten Listings in dieser Rolle.
- Fehlende Deklaration: Unterstützung nicht angegeben; ältere Plugins bleiben
  lauffähig, erhalten aber keine positive Markierung.

Die technische Form und ihre Versionsbehandlung werden im Scope-Vertrag von
T-30 festgelegt. Es gibt kein implizites „alle“ und keine aus Yahoo-Suffixen
abgeleitete Unterstützung. Operating-MICs werden nicht automatisch auf alle
Segment-MICs ausgedehnt.

Für dateibasierte Plugins bedeutet eine vorhandene Instrumentzeile keine
vollständige Abdeckung der betreffenden Börse. Solche Abdeckung wird als
bestandsabhängig ausgewiesen, sofern das Plugin sie deklariert.

Der Core liest die Auskunft aus den laufenden, konfigurierten Quellen und
validiert sie. Das Dashboard erhält ausschließlich REST-Daten. Ein installiertes,
aber in keiner Kette aktiviertes Plugin macht keine Börse grün. Eine nicht
einsatzbereite Quelle bleibt als solche sichtbar und zählt nicht als aktive
Unterstützung. Die Liste prüft keine Live-Kurse und verspricht keinen Treffer
für jedes einzelne Papier.

## Oberfläche

Spalten: MIC, Handelsplatz, Region und Quellenunterstützung. Bei den Quellen stehen Name und
Rolle; mindestens Kurs und Tageshistorie werden unterscheidbar angegeben.
Fehlende Deklaration wird als „Nicht angegeben“ kenntlich, ausdrücklich
fehlende aktive Abdeckung als „Keine aktive Quelle“.

Die konfigurierte Standardbörse bleibt markiert. Sammelcodes wie `US`
erscheinen separat mit ihren Mitgliedern und werden nie als MIC ausgegeben.
Anbietersuffixe stehen nur als zusätzliche Information dort, wo sie bekannt
sind. Sie werden nicht als universell gültige Eingabe beworben.

## Umsetzung und Nachweise

Erwartete Bereiche: Referenzdaten/Lader, Plugin-Vertrag, Registry-Auskunft,
REST-Modelle/-Route, `ExchangesPanel`, DE/EN-Kataloge und Autorendokumentation.
Keine Änderung der Kursabfrage, Identitätsmigration oder Eingabe-Rückrechnung.

Zuerst ein vertikaler Nachweis: Test-Plugin deklariert einen MIC für Kurse,
der Core liefert ihn mit Quelle/Rolle, das UI markiert exakt diesen Eintrag.
Ein Plugin ohne Deklaration darf denselben Eintrag nicht grün machen.
Danach Ausfall/deaktivierte Quelle, Rollenunterschiede, Katalogsuche,
Pagination und mobile Ansicht prüfen. Keine echte Betriebsdatenbank für Tests.

Die Neufassung ersetzt nicht stillschweigend den breiteren alten Zuschnitt
von T-30 (Plugin-Aliase und deren Kollisionen). Vor Produktänderungen ist der
verbindliche Umfang im Ticket abzugrenzen.
