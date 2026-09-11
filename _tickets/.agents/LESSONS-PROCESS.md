# Herkunft der lokalen Lessons-Verfahren

Diese Verfahrensabschnitte wurden am 2026-09-11 aus den Sammeldateien
verschoben. Sie gehören zum [Workflow](AGENT-WORKFLOW.md), nicht zum
Lessons-Bestand. Aktuelle Rollen, Übergabe und Rundenlimit regelt der Workflow.

## Übersicht

- [Gemeinsame Vorgabe zum Rundenlimit](#gemeinsame-vorgabe-zum-rundenlimit)
- [Leitplanken für das spätere Skill-Proposal](#leitplanken-für-das-spätere-skill-proposal)
- [Verwendung](#verwendung)
- [Wann ein Befund zum Muster wird](#wann-ein-befund-zum-muster-wird)

## Gemeinsame Vorgabe zum Rundenlimit

Maßgeblich ist der gemeinsame
[Ablauf zum Rundenlimit](AGENT-WORKFLOW.md#rundenlimit-rest-offenlegen-und-abschließen).
Die folgende Erfahrung erklärt den Anlass; sie ist keine zweite Regelkopie.

Anlass sind die von Mike benannten, zunächst liegen gebliebenen
Docstring-Korrekturen aus T-21 und Codex' anschließende zu starre
Eskalationsregel in `4dbb9bd`. Das ist eine ausdrückliche gemeinsame
Arbeitsvorgabe, keine Behauptung zusätzlicher unabhängiger Vorfälle.

[↑ Übersicht](#übersicht)

## Leitplanken für das spätere Skill-Proposal

Siehe auch die ausdrücklich von Mike beauftragte [T-66-Review-Lehre](lessons/SI-R-01.md)
zur Gewichtung von Befunden. Sie betrifft Claude als Verifier und Codex bei
der Übernahme seiner Empfehlung.

Dieser Abschnitt ist **kein Claude-Fehlermuster**, sondern das Prozesslearning
aus T-21 Teil 3. Dort brauchte ein reiner Entwurf die Runden 8 bis 24. Ein
Review-Skill muss deshalb nicht nur Fehler finden, sondern aktiv Konvergenz
erzwingen und klare Grenzen setzen:

1. **Scope-Grenze:** Eine Übergabe hat genau ein beobachtbares Ergebnis.
   Mehrere unabhängig lieferbare Regeln werden vor dem Review getrennt; ein
   vertikaler Schnitt darf mehrere Schichten berühren, muss aber als eine
   durchgehende Kette prüfbar bleiben.
2. **Runden-Leitplanke:** Ungefähr drei nicht erfolgreiche Entwurfsrunden sind
   ein Richtwert für eine ausdrückliche Konvergenzprüfung, keine absolute
   Grenze. Eine weitere Runde ist sinnvoll, wenn Rest und Abschlussweg konkret,
   klein und voraussichtlich abschließend sind; andernfalls verlangt der
   Reviewer eine konsolidierte Neufassung oder einen kleineren Zuschnitt.
   Nach jeder weiteren erfolglosen Runde wird neu bewertet.
3. **Entscheidungs-Grenze:** Eine neue Grundentscheidung invalidiert alle
   davon abhängigen Aussagen, Tests und Verify-Markierungen. Der Entwurf wird
   auf eine neue Basis gestellt; alte Regeln werden nicht mit Warnungen,
   Durchstreichungen und Nachträgen weitergeschleppt.
4. **Auswirkungs-Grenze:** Vor einer Vollständigkeitsbehauptung wird jede neue
   Fachregel einmal über ihre Erzeuger und Verbraucher verfolgt: Datenmodell,
   Repository, Service, REST, UI, Migration, Betrieb, Dokumentation und Tests.
   Nicht zutreffende Schichten werden ausdrücklich ausgeschlossen.
5. **Evidenz-Grenze:** Lange Prosa ersetzt keine ausführbare Gegenprobe.
   Vertrags- und Integrationsfragen werden früh mit kleinen Spikes oder Tests
   gegen den realen Umgebungscode geprüft.
6. **Rollen-Grenze:** Technische Folgefragen bleiben bei Implementierer und
   Reviewer. Der Mensch wird nur für eine echte Produktentscheidung oder eine
   notwendige Scope-Erweiterung unterbrochen, nicht für unbestimmte Fragen wie
   „trägt der Entwurf zu viele Sonderfälle?".
7. **Reviewer-Verantwortung:** Der Reviewer bewertet auch den Prozess. Er muss
   eine nicht konvergierende Schleife stoppen, selbst wenn jedes einzelne
   Finding sachlich korrekt ist.
8. **Skelett-Grenze:** Nennt ein Vorhaben einen Erfolgsweg, muss dieser Weg
   **einmal durchgelaufen** sein, bevor die Vorarbeiten weiterlaufen — als
   dünnstes lauffähiges Skelett, hartverdrahtet und hässlich erlaubt. Ein
   Maßstab, an dem erst am Ende gemessen wird, ist ein Wunsch.
9. **Budget-Grenze:** Überschreitet ein Ticket seine Time-Box um ein
   Vielfaches, ist das ein Anlass für eine ausdrückliche Zuschnittsprüfung —
   nicht für weitere Runden. Der Implementierer stellt die Frage, bevor der
   Mensch sie stellen muss.
10. **Testinfrastruktur-Grenze:** Unit-Tests und echte Online-
    Integrationstests über die vorhandenen Bibliotheks- und Sprach-APIs sind
    der Standard. Ein eigenes Test-Subsystem braucht vor Entwurf und Code eine
    ausdrückliche, im Ticket dokumentierte Freigabe von Mike.

**Beleg für Leitplanke 8 — und der Anlass, sie aufzuschreiben** *(Mike,
2026-08-27, nach Runde 52)*: Der Plugin-Entwurf vom 2026-08-19 nennt als
Maßstab ausdrücklich, „dass jemand in Toronto tatsächlich ein Plugin einsetzen
kann". Dieselbe Datei stellt den Lader (T-22, T-23) an Position sechs und
sieben. Nach 52 Runden war der Stand: **880 Zeilen zugesagter Plugin-Vertrag,
und der Core führt davon genau drei Namen aus** — `NotFound`,
`NotResponsible`, `Unavailable`. `sources.py`, `testing.py` und beide
Beispiel-Plugins hat StockInfo nie geladen.

Dass das gefährlich ist, belegen die teuersten Befunde derselben Runden. Sie
sind **alle vom selben Typ: geschrieben, nie ausgeführt.**

* Der `409` bei mehrdeutigem Symbol stand seit T-24 im **abgenommenen**
  Vertrag und war an keinem Endpunkt gebaut — über zwanzig Runden unbemerkt.
* Zwei Wächterregeln (Runden 48 und 49) passten nicht einmal auf den
  unveränderten Bestand.
* Die Pluralformen standen in beiden Katalogen verkehrt herum — sichtbar in
  einer Sekunde, sobald man sie einmal laufen lässt.

**Reviewqualität ersetzt keine Ausführung.** Ein Review findet Widersprüche
zwischen Artefakten; dass ein Vertrag der Wirklichkeit nie begegnet ist, findet
es nicht.

**Auslöser für das Skill-Proposal:** T-21 Teil 3 endete nach 17
Entwurfsrunden bei einer 936-zeiligen Spec. Die Runden 8, 9, 10, 13 und 17 bis
23 lieferten zugleich elf Belege für P-02. Das zeigt: Fachliche Gründlichkeit
ohne Scope-, Runden- und Entscheidungsgrenzen verhindert keine
Review-Eskalation.

[↑ Übersicht](#übersicht)

## Verwendung

Wenn Codex den Prüfgegenstand erstellt hat, liest der Verifier diese Datei
vor dem Review. Codex liest sie vor einer Übergabe seiner eigenen Arbeit.
Bei gemischter Autorenschaft werden die Sammlungen beider beteiligten Agenten
berücksichtigt. Entscheidend ist der Autor der geprüften Fassung, auch nach
einem Rollenwechsel.

Einzelbefunde bleiben zunächst in ihren Tickets; die Claude-Sammlung wird nicht
als Codex-Befund kopiert.

[↑ Übersicht](#übersicht)

## Wann ein Befund zum Muster wird

- **Mindestens zwei konkrete Belege derselben Fehlerklasse.**<br>
  Alternativ genügt eine ausdrücklich falsche Vollständigkeitsbehauptung mit
  dokumentierter Behauptung und Gegenbeleg. Eine Vermutung genügt nicht.

- **Jeder Eintrag macht die nächste Prüfung konkret.**<br>
  Er enthält Erkennungsregel, Prüffrage und verlinkte Belege mit Ticket,
  geprüfter Fassung oder Runde und beobachtetem Ergebnis. Die Zuordnung zu
  Codex muss belegt sein; der Name des aktuellen Owners allein genügt nicht.

- **Neue Belege ergänzen das vorhandene Muster.**<br>
  Stabile Kennungen wie `CX-01` verwenden. Menschliche Rückmeldungen bleiben
  im Original erhalten; ein Muster ersetzt weder Ticket noch Abnahmenachweis.

Wiederkehrende Probleme können Implementierung, Tests, Dokumentation,
Übergaben oder die Arbeit als Verifier betreffen. Die Rolle beim jeweiligen
Befund ausdrücklich nennen. Fachliche Regeln gelten unabhängig vom Agenten.

[↑ Übersicht](#übersicht)
