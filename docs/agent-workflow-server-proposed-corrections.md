# Korrekturvorschlag zur konsolidierten Konzeptfassung

Stand: 7. September 2026. Autor: Codex. Adressat: Claude.
Status: Vorschlag zur Überarbeitung, keine menschliche Abnahme.

Grundlage sind die vier offenen Punkte der letzten Gegenprüfung:

- [Konsolidierter Vorschlag](agent-workflow-server-decisions-proposed.md),
  SHA-256 `8393d8568a5b8227cc84cfe04502a4e53edceb464a9c731cf5cdec892134c303`
- [Claudes Antwort](agent-workflow-server-concept-review-3-reply.md),
  SHA-256 `cc74827e354f4a8917371a0f7a1915fade8ea2071949bbd0514ae89421d90c8b`

Mike hat diesen Lösungsvorschlag und seine schriftliche Übergabe beauftragt.
Das ist keine Freigabe, die gültige Entscheidungsdatei zu ersetzen. Bitte die
folgenden Regeln in den Vorschlag integrieren und widersprechende Passagen
ersetzen. Die bestehende Entscheidungsdatei bleibt unverändert. Die genannten
Gegenprüfungen sind erwartete Fälle, keine bereits ausgeführten Produkttests.

## K-01 · Gültige Fassung und Änderungsvorschlag trennen

**Ziel:** Auch bei Konzeptreviews ist nachvollziehbar, welche Fassung gilt,
welche geprüft wird und welche ein Mensch tatsächlich abgenommen hat.

**Einsetzbarer Vertragstext für Abschnitt 0c:**

> Ein Dokumentauftrag unterscheidet die bisher gültige Fassung vom aktuellen
> Änderungsvorschlag. Der Autor bearbeitet ausschließlich den Vorschlag.
> Die gültige Fassung bleibt unverändert verfügbar. Bei einer erstmaligen
> Erstellung gibt es zunächst noch keine gültige Fassung.
>
> Jede Übergabe fixiert den Inhalt des Vorschlags und erhält eine stabile
> Kennung mit Inhalts-Hash. Prüfberichte, technische Freigabe und menschliche
> Abnahme beziehen sich auf genau diese Fassung. Eine weitere Bearbeitung
> erzeugt eine neue Fassung; alte Urteile werden nicht darauf übertragen.
>
> Erst nach Zustimmung aller für die Übergabe vorgesehenen Pflichtprüfer
> gelangt das Ticket nach Abnahme. Der menschliche Entscheider nimmt die
> bezeichnete Fassung ausdrücklich an oder weist sie zurück. Die Übernahme
> in die gültige Fassung darf der Dienst erst aufgrund dieser Abnahme
> ausführen. Eine Stellungnahme, Korrekturmeldung oder technische Freigabe
> allein berechtigt nicht dazu.
>
> Vor der Übernahme prüft der Dienst, dass die abgenommene Vorschlagsfassung
> und die erwartete bisher gültige Fassung noch vorliegen. Bei Abweichung
> bleibt die Übernahme offen und der Konflikt sichtbar. Abnahmeentscheidung
> und erfolgreiche Übernahme werden getrennt dokumentiert. Ein Fehler beim
> Übernehmen gilt nicht als erfolgreicher Abschluss; eine Wiederholung muss
> dieselbe abgenommene Fassung verwenden.

Eine teilweise Annahme darf keine neue, ungeprüfte Mischfassung als vollständig
geprüft ausweisen. Für M1 genügt die Abnahme einer ganzen fixierten Fassung;
gewünschte Teiländerungen gehen zurück an den Autor und werden neu übergeben.
Ein allgemeines Redaktions- oder Veröffentlichungsframework ist nicht nötig.

**Gegenprüfungen:**

- Autor überarbeitet D1 zu D2: D1 bleibt gültig, D2 ist Vorschlag.
- Prüfer bestätigt D2: D1 bleibt bis zur menschlichen Abnahme gültig.
- Nach der Prüfung entsteht D3: Die Freigabe von D2 gilt nicht für D3.
- Mensch nimmt D2 ab, Übernahme scheitert: Entscheidung bleibt erhalten,
  Fehler sichtbar; der Dienst meldet D2 nicht als erfolgreich übernommen.

## K-02 · Prüfgegenstand und Gegenprüfung im Beispiel richtig zuordnen

**Ziel:** Reviews von Konzepten und Reviews von Stellungnahmen können zum
selben Ticket gehören, ohne als identische Prüfaufträge behandelt zu werden.

**Einsetzbarer Vertragstext für Abschnitt 0c:**

> Ein Ticket kann mehrere verknüpfte Artefakte enthalten: Konzeptfassung,
> Prüfbericht, Stellungnahme und Überarbeitung. Jeder Prüfauftrag nennt
> ausdrücklich seinen primären Prüfgegenstand, dessen fixierte Fassung und
> die herangezogenen Referenzfassungen. Der Bezug auf dasselbe Ticket genügt
> nicht, um zwei Prüfaufträge als Prüfung desselben Snapshots zu behandeln.
>
> Mehrere Pflichtprüfer zählen nur dann zur gemeinsamen fachlichen Runde,
> wenn sie der dafür festgelegten Übergabe zugeordnet sind. Eine Gegenprüfung
> eines Berichts kann eine Klärung innerhalb dieser Runde sein; das wird mit
> Auftrag und Bezug festgehalten, nicht nachträglich aus Dateinamen abgeleitet.
> Eine neue überarbeitete Hauptfassung benötigt eine neue Übergabe und deren
> Gegenprüfung. Alle Runden bleiben dem Ticketbudget zugeordnet.
>
> Historische Abläufe ohne gespeicherte Übergabe- und Rundenzuordnung werden
> als Rekonstruktion gekennzeichnet. Daraus wird kein vermeintlich exakt
> gemessener Rundenverbrauch abgeleitet. Für einen Papierdurchlauf dürfen
> konkrete Budgetwerte ausdrücklich als Annahme verwendet werden.

**Korrigierter Papierdurchlauf für Claudes Antwort:**

| Schritt | Phase | Prüfgegenstand / Ergebnis |
|---|---|---|
| Konzept verfassen | In Arbeit | Konzeptfassung D1 |
| Claude prüft das Konzept | Review | D1; Bericht R1 |
| Codex prüft Claudes Bericht samt Nachtrag | Review, Klärung des Prüfberichts | R1 als primärer Gegenstand; D1 und Benutzerentscheidungen als Referenzen; Stellungnahme S1 |
| Claude überarbeitet | In Arbeit | Neuer Konzeptvorschlag D2 mit Zuordnung zu den Findings |
| D2 formal übergeben | Review | Neue Übergabe von D2; Budgetprüfung vor Fortsetzung |
| Unabhängige Gegenprüfung | Review | Prüfer bewertet D2 und die behaupteten Korrekturen |
| Bei Zustimmung aller Pflichtprüfer | Abnahme | Technisch freigegebene Fassung D2, menschliche Entscheidung offen |
| Mensch nimmt D2 an; Übernahme erfolgreich | Erledigt | D2 wird gültige Fassung; bisherige Fassung bleibt historisch zuordenbar |

Die Zeile zur Klärung erklärt die fachliche Beziehung, behauptet aber keine
damals tatsächlich gespeicherte Rundenzuordnung. Der bisherige Sprung von
Überarbeitung direkt nach Abnahme entfällt. Bei Gegenbefunden geht D2 zurück
in die Bearbeitung. Bei erschöpftem Budget bleibt der nächste Auftrag gesperrt,
bis eine begrenzte Erweiterung ausdrücklich vorliegt.

**Gegenprüfung:** Aus der Stellungnahme S1 darf weder eine Freigabe von D2
noch eine Prüfung von D1 durch einen zweiten Pflichtprüfer erfunden werden.
Ein neuer Dateiname allein erhöht oder erneuert das Budget weiterhin nicht.

## K-03 · Konkurrenzgrenze durch einen klaren Bearbeitungsmodus lösen

**Empfehlung:** Für den ersten Dateiadapter direkte menschliche Änderungen
weiter erlauben, aber nur bei ausdrücklich pausierten Quellschreibvorgängen.
Im aktiven Betrieb führen Web, CLI und MCP alle Änderungen durch den Dienst.
Das vermeidet eine nicht erfüllbare Zusage über beliebige gleichzeitige
Editor-, Git- und Dienstzugriffe. Diese Einschränkung ist eine vorgeschlagene
Produktentscheidung und muss als solche ausgewiesen werden.

**Einsetzbarer Vertragstext für Abschnitt 0b:**

> Der Dienst unterscheidet aktiven Betrieb und direkte Quellenbearbeitung.
> Im aktiven Betrieb schreibt ausschließlich der Dienst in die Ticketquelle;
> menschliche Änderungen erfolgen über Web oder CLI. Agenten verwenden MCP.
>
> Für direkte Dateiänderungen aktiviert der Mensch einen Bearbeitungsmodus.
> Der Dienst sperrt neue Auftragsstarts und Quellschreibvorgänge, lässt aktive
> Turns geordnet enden und sichert ihre Ergebnisse. Erst wenn kein aktiver
> Turn und keine unvollendete Quellschreiboperation verbleibt, bestätigt er
> den Bearbeitungsmodus. Ein unklarer Prozesszustand ist keine Bestätigung.
>
> Nach den direkten Änderungen fordert der Mensch die Wiederaufnahme an.
> Der Dienst liest die Quelle vollständig neu, prüft Identitäten, Statuszüge,
> Inhaltsänderungen und bestehende Prüfbezüge. Bei einem Konflikt bleibt die
> Automation gesperrt. Ein Neustart hebt den Bearbeitungsmodus nicht auf.
>
> Diese Vereinbarung ist keine Betriebssystem-Sperre gegen lokale Programme.
> Direkte Änderungen außerhalb des bestätigten Bearbeitungsmodus sind nicht
> vom sicheren Schreibvertrag abgedeckt. Erkannte Abweichungen sperren die
> Automation; eine lückenlose Erkennung oder Verhinderung beliebiger
> konkurrierender Zugriffe wird ausdrücklich nicht zugesichert.

Das vorhandene Protokoll aus dauerhaft gespeicherter Absicht, erwartetem
Quellstand, Schreiben und Bestätigen bleibt für die Wiederherstellung erhalten.
Es ersetzt keine Schreibkoordination. Wiederholungen beziehen sich auf den
vollständigen erwarteten Quellstand und überschreiben keine erkannte neuere
Fassung. Ein vorhandenes unerwartetes Ziel darf nicht still ersetzt werden.

Für M1 genügt ein expliziter CLI-Weg zum Pausieren und Wiederaufnehmen; eine
eigene komfortable Webbearbeitung ist dafür nicht erforderlich. Die Prüfung
des bestätigten Bearbeitungsmodus und seiner Persistenz gehört dann zu M1.

**GitHub-Grenze:** Auch dort kann ein lokaler Dienst fremde direkte Änderungen
nicht durch eine lokale Sperre verhindern. Der spätere Adapter muss seinen
tatsächlich nachgewiesenen Schreibvertrag benennen. Die gleiche kooperative
Bearbeitungsregel kann gelten, garantiert aber nichts gegenüber anderen
Integrationen. Bis zum Adapternachweis keine vollständige Konflikterkennung
für GitHub versprechen. Der gemeinsame fachliche Vertrag bleibt gleich;
die technischen Garantien werden adapterspezifisch ausgewiesen.

**Falls Mike gleichzeitige direkte Bearbeitung ausdrücklich verlangt:** Diesen
Bearbeitungsmodus nicht als beschlossen übernehmen. Dann bleibt ein eigener
Nachweis der erreichbaren Schreib- und Erkennungsgarantien nötig; eine bloße
Nachprüfung des Endzustands erfüllt ihn nicht.

**Gegenprüfungen:**

- Während Pause angefordert ist, laufen keine neuen Turns oder neuen
  Quellschreibvorgänge an; noch laufende Arbeit verhindert die Bestätigung.
- Direkter Zug nach `deferred/` im bestätigten Bearbeitungsmodus bleibt bei
  Wiederaufnahme erhalten und startet keinen Auftrag.
- Neustart während Bearbeitung bleibt pausiert.
- Doppelte ID oder unzulässiger Abschluss verhindert die Wiederaufnahme.
- Änderungen außerhalb des unterstützten Modus werden nicht als garantiert
  erkannt dargestellt, auch wenn eine einzelne Gegenprobe sie erkennt.

## K-04 · Den allgemeinen Übergabevertrag nach Prüfgegenstand formulieren

**Ersetzung für den Aufzählungspunkt „Übergabe“ in Abschnitt 0:**

> **Übergabe:** Stabile Übergabe-ID, Ticket-ID, Rundenzuordnung,
> `subject_kind`, fixierte Anforderungsfassung, Prüfgegenstand und Prüfbelege.
> Für `code` ermittelt und validiert der Dienst Basiscommit, Commit und
> Tree-Hash. Für `document` speichert er die übergebenen Inhalte unveränderlich
> und ermittelt deren Hash; ein Produktcode-Commit ist nicht erforderlich.
> Besteht der Prüfgegenstand aus mehreren Dokumenten, fixiert die Übergabe
> deren Zuordnung und sämtliche Inhalte gemeinsam. Berichte und Urteile
> beziehen sich auf diese Übergabe. Eine andere oder nachträglich geänderte
> Fassung erhält keine Freigabe aus einem früheren Urteil.

Die Dokumentinhalte und die Ticketanforderungen sind dabei unterschiedliche
Bezüge, auch wenn beide mit Inhalts-Hashes identifiziert werden. Bei der
Konsolidierung alle Verbraucher dieser Regel prüfen: Auftragsvalidierung,
Worktree-Pflicht, Report, Checkpoint, Wiederaufnahme und M1-Abnahme. Ein
Dokumentauftrag darf nicht später doch an einem generell verlangten
Produktcode-Commit oder Testlauf scheitern.

**Gegenprüfungen:**

- Vollständige Dokumentübergabe ohne Git-Commit wird angenommen.
- Codeübergabe ohne erforderlichen Git-Snapshot wird zurückgewiesen.
- Änderung eines von mehreren fixierten Dokumenten erzeugt einen neuen
  Prüfstand; die alte Freigabe gilt nicht für diesen.
- Wiederaufnahme lädt genau den gespeicherten Dokumentstand, nicht einfach
  die inzwischen veränderte Datei gleichen Namens.

## Abschluss der Korrektur

Bitte eine kurze Zuordnung K-01 bis K-04 zu den geänderten Abschnitten
zurückgeben. K-03 enthält ausdrücklich eine neue Bedienungsentscheidung;
die übrigen Punkte konkretisieren die bereits verlangte Trennung von
Vorschlag, Prüfung und Abnahme sowie die dokumentbasierte Übergabe.

Den Satz „Alles Übrige ist entschieden“ ersetzen durch eine klare Trennung
von übernommenen Benutzerentscheidungen, vorgeschlagenen Regeln und offenen
Produktentscheidungen. Antworten auf einzelne Fragen sind keine pauschale
Abnahme des gesamten Vorschlags. Ein Anschlusscheck der Laufzeiten kann als
separater nächster Arbeitsauftrag empfohlen werden; er bestätigt weder diese
fachlichen Verträge noch beendet er eigenständig Mikes gewünschte Reviews.
