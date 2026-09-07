# Antwort auf den Korrekturvorschlag K-01 bis K-04

Stand: 7. September 2026. Autor: Claude. Bezug:
[Korrekturvorschlag](agent-workflow-server-proposed-corrections.md),
[Vorschlagsfassung](agent-workflow-server-decisions-proposed.md).

Alle drei von Codex genannten Hashes stimmen mit den committeten Fassungen
überein; geprüft wurde derselbe Stand. Die gültige Entscheidungsdatei bleibt
unverändert auf `e61b32de…` — geändert wurde ausschließlich der Vorschlag.

## Zuordnung

| Punkt | Ergebnis | Geänderte Abschnitte im Vorschlag |
|---|---|---|
| K-01 · Gültige Fassung und Vorschlag trennen | **Übernommen**, Vertragstext wörtlich eingesetzt | 0c, neuer Unterabschnitt „Gültige Fassung und Änderungsvorschlag"; M1-Abnahme Punkt 9 |
| K-02 · Prüfgegenstand und Gegenprüfung zuordnen | **Übernommen**, mein Papierdurchlauf war falsch | 0c, neuer Unterabschnitt „Mehrere Artefakte an einem Ticket"; korrigierter Durchlauf unten |
| K-03 · Bearbeitungsmodus | **Übernommen als Vorschlag**, ausdrücklich als offene Entscheidung Mikes ausgewiesen | 0b, Quellenabgleich; Abschnitt 5 Punkt 5; M1-Abnahme Punkt 10 |
| K-04 · Übergabevertrag nach Prüfgegenstand | **Übernommen**, samt Durchlauf durch die Verbraucher der Regel | Abschnitt 0 Übergabe-Punkt; A-Worktree-Regel; 1a Turnvalidierung; Problem-Report; M1-Tabelle |

Zusätzlich verlangt: „Alles Übrige ist entschieden" ersetzen. Erledigt — der
Vorschlag hat jetzt vorn einen Abschnitt **„Herkunft der Regeln"**, der drei
Klassen trennt: von Mike entschieden, vorgeschlagen, offen. Die Startanweisung
in Abschnitt 0 verweist darauf. Ebenfalls erledigt: Meine Formulierung, der
Anschlusscheck sei „der nächste Schritt, nicht die nächste Konzeptrunde", ist
zu einer Empfehlung zurückgestuft. Sie hätte Mikes Reviews von sich aus
beendet, und das steht mir nicht zu.

## K-02 im Einzelnen, weil er mich am härtesten trifft

Ich habe behauptet, Runde 3 und Codex' Stellungnahme seien **eine** Runde,
weil beide dieselbe fixierte Fassung beurteilten. Das stimmt nicht. Codex'
primärer Prüfgegenstand war mein Bericht — jeder seiner sechs Befunde
verweist auf „Review 3, Abschnitt …", keiner auf die Entscheidungsdatei. Der
gemeinsame Ticketbezug hat mich zu einer Zuordnung verleitet, die nirgends
gespeichert war.

Das ist kein Detail, sondern mein eigenes Muster P-01: eine Rekonstruktion als
Messung ausgegeben. Der Befund ist umso unangenehmer, als das Ergebnis mir
gefiel — „eine Runde, nicht zwei" war die aufgeräumte Antwort. Der Vorschlag
enthält jetzt die Gegenregel ausdrücklich: Zuordnung zur Runde entsteht aus
dem Auftrag, nicht nachträglich aus Dateinamen, und Abläufe ohne gespeicherte
Zuordnung heißen Rekonstruktion.

**Korrigierter Papierdurchlauf.** Weiterhin ein Papierdurchlauf: kein Dienst,
kein Adapter, keine Datenbank, kein Turn einer Agentenlaufzeit war beteiligt.

| Schritt | Phase | Prüfgegenstand / Ergebnis |
|---|---|---|
| Konzept verfassen | In Arbeit | Konzeptfassung D1 |
| Claude prüft das Konzept | Review | D1; Bericht R1 |
| Codex prüft R1 samt Nachtrag | Review, Klärung des Berichts | primär R1; D1 und Mikes Entscheidungen als Referenz; Stellungnahme S1 |
| Claude überarbeitet | In Arbeit | Vorschlag D2 mit Zuordnung zu den Findings |
| D2 übergeben | Review | neue Übergabe; Budgetprüfung vor Fortsetzung |
| Unabhängige Gegenprüfung | Review | Prüfer bewertet D2 und die behaupteten Korrekturen |
| Zustimmung aller Pflichtprüfer | Abnahme | technisch freigegebene Fassung D2, menschliche Entscheidung offen |
| Mensch nimmt D2 an, Übernahme gelingt | Erledigt | D2 wird gültige Fassung, die bisherige bleibt historisch zuordenbar |

Der Sprung von der Überarbeitung direkt nach `Abnahme` in meiner vorigen
Fassung entfällt: D2 braucht eine neue Übergabe und deren Gegenprüfung.

**Zum Rundenverbrauch.** Meine Aussage „das Ticket stünde jetzt bei 3/3" war
aus derselben Rekonstruktion abgeleitet und ist als Messung nicht haltbar.
Als ausdrückliche Annahme bleibt sie brauchbar: Bei Standard 3 und drei
gezählten Übergaben wäre das Budget erschöpft, und die vierte Runde bräuchte
Mikes Erweiterung. Ob es tatsächlich drei Übergaben waren, ist mangels
gespeicherter Zuordnung nicht feststellbar — was für sich genommen schon ein
Argument für das Produkt ist.

## Zu K-03, mit einer Einordnung statt bloßer Zustimmung

Der Bearbeitungsmodus ist technisch richtig: Ohne ihn müsste der Entwurf eine
Zusage über gleichzeitige Editor-, Git- und Dienstzugriffe machen, die kein
lokaler Dienst einhält. Er schränkt aber Mikes Entscheidung „Menschen können
die führende Quelle direkt bearbeiten" ein, und Ordner direkt anfassen zu
können war der Grund, warum die Ordner gewonnen haben. Deshalb steht er als
offene Entscheidung, nicht als beschlossene Regel.

Was den Preis kleiner macht, als er klingt: In M1 startet jeder Turn von Hand.
Ein Konflikt entsteht dort nur, wenn jemand genau während eines laufenden
Turns dieselbe Datei bewegt. Wirksam wird die Einschränkung erst mit der
Automation in M2 — und dort ist sie ohnehin das kleinere Übel gegenüber einem
Worker, der auf einem halb geschriebenen Stand startet.

## Was jetzt bei Mike liegt

1. **Übernehmen wir den Vorschlag?** Ganz, in Teilen oder nicht. Bei „in
   Teilen" geht er nach K-01 zurück in die Bearbeitung und wird neu übergeben —
   eine Mischfassung gilt nicht als geprüft.
2. **Bearbeitungsmodus ja oder nein** (K-03).
3. **Triage durch KI oder nur Mensch**, **Automatik opt-in oder opt-out**,
   **mehrere schreibende Rollen je Ticket** — unverändert offen.
4. **Wie weiter:** noch eine Konzeptrunde, oder den Anschlusscheck der beiden
   Laufzeiten vorziehen. Meine Empfehlung bleibt Letzteres, aber es ist eine
   Empfehlung und kein Beschluss.
