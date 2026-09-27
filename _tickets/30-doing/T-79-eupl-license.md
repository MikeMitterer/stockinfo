# T-79 · EUPL-Lizenz für StockInfo

Mike beauftragt am 2026-09-27 die Umstellung wie in StockPortfolio T-57,
einschließlich Docker und weiterer Auslieferungswege. Codex implementiert,
Claude prüft unabhängig. Stand: in Arbeit.

## Scope-Vertrag

Ergebnis: StockInfo wird unter EUPL 1.2 only angeboten und ausgeliefert.

1. Offizielle EN/DE-Texte und LICENSING.md nach StockPortfolio T-57;
   kommerzielle Zusatzlizenz entfernen, eigenständige MIT-Pakete erhalten.
2. Python/npm-Metadaten, Docker-Label und vorhandene Lizenzprüfung umstellen;
   neue Lizenzdokumente ins Image aufnehmen. Unraid-XML im Template-Repo abgleichen.
3. Root-, Docker- und Unraid-Anleitung konsistent halten; historische
   Release-Notizen mit damaligem Lizenzstand eindeutig kennzeichnen.

Erwartet: 5 Build-/Metadatendateien, bis zu 8 Lizenz-/Dokudateien,
1 externe XML-Datei, Boarddateien. Keine neue Testdatei erforderlich;
vorhandene Docker-Tests, echter amd64-Build, Image-Hashes, Hub-Vorschau.
Budget: 400 handgeschriebene Diff-Zeilen plus der ausdrücklich beauftragte
vollständige Austausch offizieller Lizenztexte (ca. 1.200 Diff-Zeilen).
Keine neue App-Funktion, kein Versionssprung, kein Image-/Hub-Push.
StockPortfolio bleibt unverändert. Quellcodezugang über das bestehende
GitHub-Repository und den im Image-Tag identifizierten Quellcommit.

## Prüfschritte

- [ ] Lizenztexte bytegleich zu den EU-Originalen, Metadaten konsistent.
- [ ] Docker-Build und tatsächliche Dokumente/Labels im Image geprüft.
- [ ] Bestehende betroffene Tests und Shell-Prüfungen erfolgreich.
- [ ] Doku-Abgleich und echte Docker-Hub-Vorschau geprüft.
- [ ] Lokales Unraid-Template angepasst und XML geprüft.

## Offene persönliche Wiedervorlagen

Wie StockPortfolio T-57: Die interne Rechtevereinbarung zwischen Michael
Mitterer (Urheber) und MangoLila GmbH (Anbieterin/Lizenzgeberin) sowie die
österreichische Rechtsprüfung sind nicht als abgeschlossen nachgewiesen.
Die dort beschlossene Verbraucherklärung wird separat übernommen;
die offiziellen Lizenztexte bleiben unverändert.

## Lessons

Inventar aller lokalen Lessons; Codex-Fassungen SI-CX-01, SI-R-02, SI-T-66
und gemeinsame AL-R-02/AL-R-12 gelesen. Frische temporäre Containerdaten,
vollständiges Lizenz-/Dokumentinventar und eigene Artefaktprüfung vorgesehen.
