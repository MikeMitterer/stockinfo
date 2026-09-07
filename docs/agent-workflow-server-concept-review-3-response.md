# Stellungnahme zu Konzeptreview 3 · Übergabe an Claude

Stand: 7. September 2026. Autor: Codex. Status: Änderungen erforderlich;
keine Konzeptfreigabe und kein Umsetzungsauftrag.

Grundlagen:

- [Konzeptreview 3 einschließlich Nachtrag](agent-workflow-server-concept-review-3.md)
- [Konzeptentscheidungen](agent-workflow-server-decisions.md), insbesondere 0b
- Mikes Ergänzung im Anschluss an die Gegenprüfung: „genau solche
  Review-Prozesse wie dieser sollten auch abgebildet werden können“.

Geprüfte Dokumentfassungen, SHA-256:

```text
agent-workflow-server-concept-review-3.md
cc5e2b1c9fdd03c3859d7e5868e06f70b41e8e137114b38a46118b23114eca61

agent-workflow-server-decisions.md
e61b32de9f217962d935b6ab8e13adc2c82b6d3232f0ccd6a91472876108035c
```

Die Hashes identifizieren die gelesenen Fassungen; sie sind kein Nachweis
eines ausgeführten Produktablaufs. Diese Gegenprüfung ist eine Prüfung der
Konzeptkonsistenz, kein Laufzeit-, GitHub-Integrations- oder Berechtigungstest.

## Auftrag an Claude

Prüfe die folgenden Befunde an den benannten Abschnitten. Überarbeite die
Konzeptentscheidungen zu einer konsistenten aktuellen Fassung; Review 3 und
diese Stellungnahme bleiben als historische Prüfbelege erhalten. Halte je
Befund die Änderung mit Abschnittsverweis oder einen begründeten Widerspruch
fest. Eine gemeldete Korrektur ist noch keine unabhängige Gegenprüfung.

Arbeite auch die neue Produktanforderung zu Konzeptreviews unten ein.
Technische Widersprüche selbst auflösen; nur tatsächlich offene
Produktentscheidungen an Mike geben. Empfehlungen aus Review 3 sind nicht
automatisch Benutzerentscheidungen. Keine Produktimplementierung beginnen.

## R3-01 · Wiedereröffnung und Budgeterweiterung trennen

Status: offen. Priorität: hoch. Bezug: Review 3, D, insbesondere Regeln 1–2.

**Beobachtung:** Ein neuer Arbeitszyklus wird einer dokumentierten
menschlichen Budgeterweiterung gleichgesetzt. Das bisherige Konzept verlangt
dagegen, den Verbrauch zu erhalten und zusätzliche Runden ausdrücklich zu
genehmigen. Die Budgetfrage steht in Review 3 zugleich noch als offene
Produktentscheidung.

**Gegenfall:** Ein Ticket steht nach drei erfolglosen Reviews bei 3/3. Mike
stellt es zurück und plant es später erneut ein. Ein neuer Zyklus darf daraus
nicht ohne gesonderte Budgetentscheidung weitere drei Reviews ableiten.

**Korrekturvorschlag:** Wiedereröffnung erhält den Verbrauch. Eine begrenzte
Erhöhung wird mit bisherigem/neuem Limit, Akteur und Begründung festgehalten.
Eine organisatorische `cycle_id` erneuert das Budget nicht. Falls Mike ein
anderes Modell ausdrücklich wählt, muss dessen Abweichung vom bisherigen
Vertrag konsistent eingearbeitet werden.

**Gegenprüfung:** Zurückstellen und Wiedereröffnen bei 3/3 bleibt gesperrt;
erst eine ausdrückliche Erweiterung auf 4 erlaubt die zusätzliche Runde.

## R3-02 · Die führende Ablage verhindert keine Git-Rücknahme

Status: offen. Priorität: hoch. Bezug: Nachtrag zu A, Regeln 1–2 und Variante 1.

**Beobachtung:** Genau ein konfigurierter Quellpfad löst die Mehrdeutigkeit
zwischen Worktree-Kopien. Daraus folgt aber nicht, dass ein Produkt-Revert
keine Tickets bewegen kann. Variante 1 sieht ausdrücklich vor, Ticketzüge
gemeinsam mit sonstigen Änderungen zu committen.

**Gegenfall:** Ein Commit enthält Produktcode und den Zug eines Tickets nach
`review/`. Wird dieser gemischte Commit zurückgenommen, betrifft das auch
den Ticketzug, unabhängig davon, wer ihn ursprünglich ausgeführt hat.

**Korrekturvorschlag:** Variante 1 darf diese Garantie nicht behaupten.
Entweder die Verflechtung ausdrücklich zulassen und daraus entstehende
Quellenänderungen erkennen oder eine getrennte Historie festlegen. Der
Benutzerentscheid „Ordner bestimmen den Status“ entscheidet nicht zugleich
den Ablageort. Die Aussagen „Punkt 1 entschieden“ und „Ort offen“ bereinigen.
Bei Nutzung des menschlichen Checkouts auch die bisherige Zusage prüfen,
dass dieser unverändert bleibt.

**Gegenprüfung:** Einen gemischten Commit samt Rücknahme als konkreten
Abgleichfall beschreiben. Es darf weder eine falsche Git-Garantie noch eine
unbemerkte Freigabe durch den zurückgenommenen Ticketzug verbleiben.

## R3-03 · Inhaltsfassung und vollständigen Quellstand unterscheiden

Status: offen. Priorität: hoch. Bezug: B, Schreibprotokoll; E, Revision.

**Beobachtung:** Ein Inhalts-Hash ohne Status ändert sich beim Verschieben
nicht. Eine erneute Leseprüfung vor dem Schreiben verhindert außerdem nicht
allein, dass der Mensch zwischen Prüfung und Schreibzugriff eingreift.
Eine dauerhaft gespeicherte Schreibabsicht löst die Wiederanlaufreihenfolge,
aber noch nicht diese Konkurrenz beim Schreiben.

**Gegenfall:** Der Dienst liest ein Ticket in `ready/`. Der Mensch verschiebt
es danach nach `deferred/` oder ändert den Inhalt. Der Dienst darf seine
ältere Absicht nicht ungeprüft auf den neuen Stand anwenden.

**Korrekturvorschlag:** Fixierte Inhaltsfassung für das Review und erwarteten
Quellstand für Schreiboperationen getrennt definieren. Letzterer umfasst
mindestens Identität, Inhalt und fachlichen Status beziehungsweise Pfad.
Pro Adapter festlegen, wie konkurrierende Änderungen erkannt werden und
welche Garantien gegenüber direkten menschlichen Schreibzugriffen bestehen.
Unklare Zwischenstände sperren Folgeaufträge; keine stille Überschreibung.

**Gegenprüfung:** Änderung zwischen Abgleich und Schreiben sowie Absturz nach
dem Quellschreiben vor DB-Bestätigung behandeln. Eine Wiederholung darf keine
neuere menschliche Änderung überschreiben oder einen Auftrag doppelt starten.

## R3-04 · Nach dem Rundenlimit den fachlich nötigen Schritt fortsetzen

Status: offen. Priorität: hoch. Bezug: C, Entfernen des Blockadeflags.

**Beobachtung:** Am Limit bleibt das Ticket laut Vorschlag in Review. Nach
einer Erweiterung soll lediglich das Flag entfernt werden. Bei einem bereits
abgeschlossenen Urteil `changes_requested` fehlt damit der Korrekturauftrag.

**Gegenfall:** Runde 3 meldet einen Fehler. Mike erlaubt Runde 4. Ein erneuter
Verifierstart auf demselben unkorrigierten Stand würde das neue Budget
verbrauchen, ohne die nötige Developer-Arbeit auszuführen.

**Korrekturvorschlag:** Urteil und nächster notwendiger Arbeitsschritt bleiben
gespeichert. Nach Erweiterung führt `changes_requested` zunächst zurück in
die Bearbeitung, danach folgen neue Übergabe und Gegenprüfung. Nicht einfach
den letzten aktiven Ausführungszustand wieder starten.

**Gegenprüfung:** 3/3 mit Änderungsbedarf → ausdrückliche Erweiterung →
Developer-Korrektur → neue Übergabe → Review 4. Kein unmittelbares Review
des alten Standes und kein verlorener Korrekturauftrag.

## R3-05 · GitHub-Abschlusszustände eindeutig abbilden

Status: offen. Priorität: mittel. Bezug: E, GitHub-Tabelle und führendes Label.

**Beobachtung:** Die Tabelle definiert Erledigt und Verworfen nur über
Schließzustand und Schließgrund. Der Folgetext verlangt dagegen genau ein
führendes Statuslabel für jedes Ticket.

**Korrekturvorschlag:** Entweder alle neun Zustände einschließlich der beiden
Abschlüsse mit genau einem Label abbilden oder die Ausnahmen und deren
Vorrangregel ausdrücklich definieren. Widersprüche zwischen Label und
Schließzustand brauchen eine festgelegte Behandlung.

**Gegenprüfung:** Für jeden der neun Zustände eine eindeutige Darstellung
angeben; fehlende, doppelte und zum Schließzustand widersprüchliche Labels
einbeziehen. Das ist zunächst Vertragsprüfung, kein GitHub-Ausführungsnachweis.

## R3-06 · Rollenrechte am Auftrag festmachen

Status: offen. Priorität: mittel. Bezug: Nachtrag „Rollen sind offen“.

**Beobachtung:** Die Trennung zwischen Rollenname und Pflichtenklasse ist
sinnvoll. „Code-Optimizer“ erzwingt aber keine Schreibrechte: Die Rolle kann
auch nur Empfehlungen liefern. Ebenso erfordert eine zweite sequenzielle
Bearbeitungsphase nicht automatisch eine zusätzliche Kanban-Spalte.

**Korrekturvorschlag:** Den konkreten Auftrag und seine Rechte maßgeblich
machen. Beratende Optimierungsprüfung und schreibende Optimierung
unterscheiden. Mehrere sequenzielle Arbeitsschritte können in „In Arbeit“
bleiben; ob und wann mehrere schreibende Rollen unterstützt werden, ist eine
separate Umfangsentscheidung. Die Regel gegen gleichzeitig aktive
Produktschreiber bleibt erhalten.

**Gegenprüfung:** Ein beratender Optimierer verändert keinen Produktcode.
Eine spätere schreibende Rolle benötigt eine geregelte Übergabe; weder ihr
Name noch eine zusätzliche Spalte ersetzt Claim- und Snapshot-Regeln.

## Neue Benutzeranforderung · Auch diesen Konzeptreview abbilden

**Verbindliches Produktziel:** Das System muss auch dokumentbasierte
Konzeptreviews wie diesen unterstützen. Der Prüfgegenstand kann ein Konzept,
eine Spezifikation oder eine Entscheidungsvorlage sein. Ein Produktcode-Diff
und ein ausgeführter Softwaretest sind dafür keine sinnvollen generellen
Pflichtvoraussetzungen.

Der vorliegende Ablauf ist der konkrete Anwendungsfall:

1. Mike formuliert beziehungsweise präzisiert die Anforderungen.
2. Eine KI erstellt oder überarbeitet das Konzept.
3. Eine andere KI prüft eine eindeutig bezeichnete Dokumentfassung und
   liefert Findings mit Begründung und Gegenfällen.
4. Eine Stellungnahme nimmt Findings an, widerspricht ihnen begründet oder
   benennt eine erforderliche menschliche Produktentscheidung.
5. Die überarbeitete Fassung wird gezielt gegengeprüft. Alte Befunde und
   Entscheidungen bleiben nachvollziehbar.
6. Technische beziehungsweise fachliche Review-Freigabe und menschliche
   Konzeptabnahme bleiben getrennt.

**Für die Konsolidierung abzuleitender Vertrag:**

- Das Ticket verknüpft den aktuellen Prüfgegenstand, die fixierte
  Dokumentfassung, Reviews, Stellungnahmen und menschliche Entscheidungen.
  Ein Dateiname allein identifiziert keine unveränderliche Prüffassung.
- Git-Snapshots bleiben für Codeaufträge gültig. Für Dokumentaufträge eine
  geeignete feste Fassung definieren, etwa gespeicherter Inhalt mit Hash;
  ein Produktcode-Commit darf dafür nicht zwingend erforderlich sein.
- Die Prüfbelege richten sich nach der Aufgabe: Bei einem Konzept sind
  Widerspruch, betroffene Regel, Gegenfall und Quellenbezug geeignete Belege.
  Eine Textprüfung wird nicht als bestandener Laufzeittest ausgewiesen.
- Ersteller, Reviewer und menschlicher Entscheider bleiben unterscheidbar.
  Das Rollenmodell muss das Überarbeiten eines Konzeptdokuments erlauben;
  „plan darf nur vorschlagen“ und „implement schreibt Produktcode“ dürfen
  diesen tatsächlichen Arbeitsauftrag nicht zwischen sich ausschließen.
- Findings erhalten stabile IDs. Stellungnahme, Korrekturmeldung und
  unabhängige Bestätigung werden auseinandergehalten. Eine neue
  Produktentscheidung macht betroffene alte Urteile nicht automatisch gültig.
- Derselbe Kanban-Lebenszyklus gilt. „In Arbeit“ kann Konzeptüberarbeitung,
  „Review“ Dokumentprüfung und „Abnahme“ menschliche Konzeptentscheidung
  bedeuten. Dafür ist kein separates Board pro Artefaktart erforderlich.
- Reviewbudget und seine ausdrücklich genehmigten Erweiterungen bleiben
  auch bei Dokumentreviews nachvollziehbar. Stellungnahmen und Dateinamen
  erzeugen nicht automatisch neue Tickets oder frische Budgets.

Das Produktziel ist beauftragt. Die genaue Einordnung in M1/M2 und der
kleinste Abnahmenachweis sind im Konzept festzulegen; dieser Auftrag führt
kein allgemeines konfigurierbares Workflow-Framework als Voraussetzung ein.

## Erwartete Rückgabe

Eine konsolidierte Konzeptfassung und eine kurze Antwort mit Zuordnung
R3-01 bis R3-06 → geändert / begründet widersprochen / Produktentscheidung
offen. Zusätzlich den oben beschriebenen Konzeptreview einmal durch die
vorgesehenen Zustände und Artefakte führen und seine Abnahmebedingungen
benennen. Dabei dokumentierte Beispiele von tatsächlich ausgeführten
Nachweisen unterscheiden.

Quellenabgleich, Sperren bei doppelten IDs, nachvollziehbare menschliche
Entscheidungen und ein zunächst kleiner Dateiadapter werden grundsätzlich
unterstützt. Die Befunde verlangen eine konsistente Konkretisierung dieser
Ansätze. Die Produktentscheidungen „Ordnerstatus“ und „entweder Dateien oder
GitHub Issues, keine Spiegelung“ bleiben bestehen.
