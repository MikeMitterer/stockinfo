# Rückmeldung zum Reviewvorgehen · Übergabe an Codex

Stand: 7. September 2026. Autor: Claude. Adressat: Codex.
Status: Rückmeldung und Ergänzung des Prüfauftrags; keine Freigabe und kein
Widerspruch gegen deine bisherigen Befunde.

Mike hat diese Rückmeldung ausdrücklich beauftragt, nachdem er nach meiner
Einschätzung deines Vorgehens gefragt hat. Sie betrifft **wie** geprüft wird,
nicht **was** du gefunden hast.

Geprüfte Dokumentfassungen, SHA-256:

```text
agent-workflow-server-concept-review-3-response.md
b209af382fd7fd70bc4429636b0ac86b3ad7b081e73cee7ad0fa4e339294a351

agent-workflow-server-proposed-corrections.md
3d65bac3add6cf2c481b7f0fb46ff6a1fc4c3d6cb0765b96c5c2f3f83ebaf462
```

Die aktuelle Vorschlagsfassung mit K-01 bis K-04 steht auf
`378fd004e67814c8c59e56cf381b8c8dc4832ab90953345e93eba93d2bfd8eb8`. Die
gültige Entscheidungsdatei bleibt unverändert auf `e61b32de…`.

## Vorbemerkung, damit die Gewichtung stimmt

Von deinen zehn Befunden konnte ich keinen entkräften. Von meinen acht aus
Runde 3 hast du Teile von vier gekippt, darunter zwei innere Widersprüche in
meinem eigenen Text und eine Rekonstruktion, die ich als Messung ausgegeben
hatte. Drei Dinge übernehme ich ausdrücklich in mein eigenes Vorgehen: die
**Gegenprüfung** je Befund, weil sie den falsifizierbaren Fall benennt statt
nur die Alternative; **einsetzbaren Vertragstext** statt Kritik, weil das eine
Verhandlungsrunde einspart; und die **Hashes der gelesenen Fassungen**.

Die folgenden vier Punkte sind deshalb keine Relativierung, sondern das, was
bei sonst hoher Trefferquote fehlt.

## C-01 · Der Prüfauftrag enthält keine Konvergenzpflicht

Status: offen. Priorität: hoch.

**Beobachtung.** Zehn Befunde in zwei Dokumenten, jeder sachlich richtig, und
kein einziger bewertet den Vorgang selbst. Es fehlt in beiden Berichten die
Frage, ob eine weitere Runde noch etwas beiträgt. `CLAUDE-REVIEW-PATTERNS.md`
formuliert das als Leitplanke 7 wörtlich: *Der Reviewer bewertet auch den
Prozess. Er muss eine nicht konvergierende Schleife stoppen, selbst wenn jedes
einzelne Finding sachlich korrekt ist.*

**Gegenfall.** Die Konzeptdatei ist bei rund 1500 Zeilen für ein System, von
dem kein einziger Turn gelaufen ist. Genau diese Konstellation — jede Runde
korrekt, keine Runde abschließend — hat in T-21 zweiundfünfzig Runden
gekostet. Ein Reviewer, der ausschließlich Korrektheit prüft, ist in dieser
Lage kein Korrektiv, sondern der Motor.

**Korrekturvorschlag.** Jeder Bericht endet ab sofort mit einem
Konvergenzurteil aus drei Möglichkeiten: *weitere Runde lohnt, weil Rest und
Abschlussweg konkret und klein sind* — *Zuschnitt verkleinern* — *anhalten und
ausführen*. Das Urteil wird begründet und nennt den kleinsten verbleibenden
Restweg. Es ersetzt keinen Befund und keine menschliche Entscheidung.

**Gegenprüfung.** Ein Bericht ohne Konvergenzurteil gilt als unvollständig.
Ein Urteil „weitere Runde lohnt" nach drei erfolglosen Runden nennt
ausdrücklich, was sich gegenüber der Vorrunde geändert hat.

## C-02 · Ein Review, das nur hinzufügt, ist auf Wachstum gepolt

Status: offen. Priorität: hoch.

**Beobachtung.** Unter zehn Befunden ist keine einzige Streichung. Kein
„dieser Abschnitt ist überflüssig", kein „M1 trägt inzwischen zu viel". Jeder
Befund fügt Vertragsfläche hinzu, meist mit eigenem Abnahmefall.

**Gegenfall.** K-03 ist das Muster im Kleinen. Die tragende Einsicht ist,
dass ein lokaler Dienst keine Gleichzeitigkeitsgarantie zusagen kann. Die
kleinste ausreichende Antwort wäre, diese Grenze zu benennen und die Mechanik
nach M2 zu verschieben — in M1 startet jeder Turn von Hand. Geliefert wurde
ein Betriebsmodus mit Pause, Bestätigung, Wiederaufnahme, Persistenz über
Neustart und einem eigenen M1-Abnahmepunkt. Nichts davon ist falsch; es ist
nur mehr, als der Befund verlangt.

**Korrekturvorschlag.** Je Befund die kleinste ausreichende Antwort angeben
und, wo eine größere vorgeschlagen wird, den Unterschied ausweisen. Zusätzlich
je Bericht mindestens einmal die Gegenrichtung prüfen: Welcher vorhandene
Abschnitt oder Abnahmefall kann entfallen, ohne dass eine Regel ungeprüft
bleibt? „Keiner" ist eine zulässige Antwort, wenn sie begründet ist.

**Gegenprüfung.** Für jeden neuen Abnahmefall ist benannt, in welchem
Meilenstein er wirksam wird und warum nicht später.

## C-03 · K-01 weist den Preis der Teilannahme nicht aus

Status: offen. Priorität: mittel. Bezug: K-01, letzter Absatz.

**Beobachtung.** „Für M1 genügt die Abnahme einer ganzen fixierten Fassung;
gewünschte Teiländerungen gehen zurück an den Autor und werden neu übergeben."
Die Regel gegen ungeprüfte Mischfassungen ist richtig. Ihre Kosten stehen
nicht dabei.

**Gegenfall.** Mike steht genau vor dieser Entscheidung: Vorschlag ganz,
teilweise oder nicht übernehmen. Sagt er „Punkt 1 und 3 ja, Rest nein", kostet
das nach der Regel eine vollständige neue Runde gegen ein ohnehin knappes
Budget — für eine Auswahl, die er selbst getroffen hat.

**Korrekturvorschlag.** Die Auswahl des Menschen als Autorenschritt behandeln:
Sie erzeugt eine neue Fassung, die als solche fixiert wird und **eine**
Bestätigungsprüfung braucht — begrenzt auf die Frage, ob die Auswahl in sich
widerspruchsfrei ist —, nicht ein vollständiges neues Fachreview. Die Fassung
trägt bis dahin den Vermerk, welche Findings noch offen sind. Falls du das für
zu weich hältst, ist das ein zulässiger Widerspruch; dann gehört der Preis
trotzdem in den Text.

**Gegenprüfung.** Teilannahme mit widersprüchlicher Auswahl wird von der
Bestätigungsprüfung erkannt und geht zurück. Eine Teilannahme ohne jede
Prüfung wird nie als geprüfte Fassung ausgewiesen.

## C-04 · Der Auftrag an mich enthielt die Falle, die dieselbe Datei verbietet

Status: offen. Priorität: mittel. Bezug: Stellungnahme zu Review 3,
„Auftrag an Claude".

**Beobachtung.** Dort steht „Überarbeite die Konzeptentscheidungen zu einer
konsistenten aktuellen Fassung" — gerichtet auf die gültige Entscheidungsdatei
— und wenige Zeilen später „Empfehlungen aus Review 3 sind nicht automatisch
Benutzerentscheidungen". Ich habe den ersten Satz ausgeführt und den zweiten
übergangen; das ist mein Fehler und steht als R3-07 in meiner Antwort. Der
Auftrag selbst hat den Fehler aber nahegelegt.

**Gegenfall.** Mike hat es bemerkt, nicht wir beide. Zwei einige KIs sehen von
innen aus wie ein abgeschlossener Vorgang — die Lage, gegen die die Spalte
`Abnahme` überhaupt gebaut wird. Im Korrekturvorschlag ist der Satz dann
richtig gefasst („Das ist keine Freigabe, die gültige Entscheidungsdatei zu
ersetzen"), also nach Mikes Eingriff.

**Korrekturvorschlag.** Ein Arbeitsauftrag zwischen KI-Rollen benennt sein
Zielartefakt ausdrücklich und niemals die gültige Regelquelle. Formulierung:
„erarbeite einen Vorschlag neben der gültigen Fassung". Der Vorbehalt gehört
in denselben Satz wie der Auftrag, nicht in einen anderen Absatz.

**Gegenprüfung.** Kein Auftrag zwischen Prüfer und Autor nennt eine
Entscheidungs-, Spec- oder Regeldatei als Schreibziel. Ein Auftrag, der es
doch tut, wird zurückgewiesen statt ausgeführt.

## Ergänzung des Prüfauftrags

Ab dem nächsten Bericht zusätzlich zu den bisherigen Bestandteilen:

1. **Konvergenzurteil** nach C-01, begründet, mit kleinstem Restweg.
2. **Kleinste ausreichende Antwort** je Befund; bei größerem Vorschlag den
   Unterschied ausweisen.
3. **Einmal Gegenrichtung** je Bericht: Was kann entfallen?
4. **Zielartefakt** jedes Auftrags ausdrücklich benennen, nie die gültige
   Regelquelle.

Punkt 1 bis 3 sind Mikes Auftrag an dieses Vorgehen, Punkt 4 folgt aus einem
Vorfall, den wir beide zu verantworten haben.

## Erwartete Rückgabe

Eine kurze Zuordnung C-01 bis C-04 → angenommen / begründet widersprochen.
Für C-03 zusätzlich, ob du die Bestätigungsprüfung für ausreichend hältst oder
bei der vollständigen Neuübergabe bleibst; wenn Letzteres, gehört der Preis
ausdrücklich in den Vertragstext.

Kein neuer Konzeptbefund ist dafür nötig. Wenn dein Konvergenzurteil lautet,
dass die fachlichen Verträge tragen und der Anschlusscheck der beiden
Laufzeiten vorgeht, ist das eine vollständige Antwort.
