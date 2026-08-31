# T-47 · Sicherung und Wiederherstellung als YAML-Datei

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | Entwurf, **offene Entscheidungen** | 1 Tag | Export und Import des Bestands als eine lesbare Datei | — |

- **Angelegt:** 2026-08-31, aus Mikes Frage nach einer Sicherung aus dem UI
- **Reihenfolge:** nicht eingeplant. Erst nach Mikes Entscheidungen unten
- **Nicht zu verwechseln mit T-25:** Dort geht es um die **Rotation** eines
  Quellenprofils samt frischer Datenbank, nummerierter Sicherung und
  `generation_id`. Hier geht es um **eine portable Datei**. T-25 könnte sie als
  seine Sicherung verwenden — erledigt ist es damit nicht

**Löst:** Das Datenverzeichnis lässt sich kopieren, aber die Kopie ist ein
undurchsichtiger Abzug: an das Schema gebunden, nicht lesbar, nicht
zusammenführbar. Und **im laufenden Betrieb ist sie nicht einmal verlässlich**
— die Datenbank läuft im WAL-Modus (`app/db.py:151`), ein `cp` erwischt dort
einen zerrissenen Stand. Eine Sicherung braucht `VACUUM INTO` oder die
Backup-API, nicht den Dateimanager.

---

## Was überhaupt schützenswert ist

Gemessen am realen Bestand (`data/stockinfo.db`, 2026-08-31):

| Klasse | Tabellen | Zeilen | Ersetzbar? |
|---|---|---|---|
| **Unwiederbringlich** | `instruments`, `instrument_overrides` | 6 + 2 | **Nein.** Die Papiere hat Mike aufgenommen, die Überschreibungen von Hand eingetragen |
| Nachladbar | `quotes`, `daily_closes`, `fx_rates`, `daily_meta` | 48 + 3265 + 4 | Ja, aus den Quellen — solange sie liefern |
| Ableitbar | Metadaten in `instruments` (Name, Gattung, TER …) | — | Ja, über `etf_meta` |

**Das Wertvolle ist klein.** Acht Zeilen tragen alles, was niemand
wiederherstellen kann; 3.265 Zeilen Tagesreihe sind Zwischenspeicher.

## Der Vorschlag — das Format gibt es schon

Der Export schreibt **genau das Format, das `yaml-file` liest**. Damit ist eine
Datei dreierlei zugleich:

1. eine **Sicherung** — lesbar, versionierbar, im Diff nachvollziehbar,
2. ein **Umzug** zwischen zwei Installationen,
3. ein **lauffähiges Offline-Profil** — `sources-profile.sh --yaml` darauf
   zeigen lassen, und die Instanz läuft ohne Netz mit dem gesicherten Stand.

Das ist der eigentliche Grund für YAML statt eines eigenen Formats: Es entsteht
kein zweites Schema, das niemand pflegt. Der Vertrag der Datei steht schon in
`docs/plugin-authors.md`, und `version: 1` darin ist bereits die
Formatversion.

## Was eine YAML-Datei **nicht** kann

Das gehört vor die Entscheidung, nicht in die Auflösung:

- **Kein bitgenauer Abzug.** `id`, `first_seen`, `fetched_at` gehen verloren
  oder werden neu gestempelt. Für einen Bestand richtig, für eine forensische
  Frage („was wusste die App am 12. August?") falsch.
- **Der Zeitpunkt der Kurse muss ehrlich bleiben.** Ein Rückspielen darf den
  Zwischenspeicher nicht frisch aussehen lassen: `as_of` ist der alte
  Zeitpunkt, nicht der des Imports.
- **Die Tagesreihe bestimmt die Größe.** 3.265 Zeilen sind als YAML rund
  150 KB; bei zwanzig Papieren über Jahre wird daraus ein Vielfaches.

---

## Offen — vier Entscheidungen für Mike

1. **Umfang.** Nur der Bestand (Papiere + Überschreibungen, acht Zeilen), oder
   zusätzlich die Tagesreihen? Der erste ist eine Sicherung, der zweite
   zusätzlich ein Offline-Profil.
2. **Rückspielen in eine nicht leere Datenbank.** Zusammenführen (vorhandene
   Papiere bleiben, neue kommen dazu) oder ersetzen? Zusammenführen braucht
   eine Regel, wer bei einem Konflikt gewinnt — die Datei oder der Bestand.
3. **Kurse beim Rückspielen.** Übernehmen (der alte Stand ist sofort sichtbar)
   oder verwerfen und die Kette neu fragen (nichts Altes wird als aktuell
   ausgegeben)?
4. **Auslöser.** Nur ein Knopf in den Einstellungen, oder zusätzlich ein
   zeitgesteuerter Export ins Datenverzeichnis?

---

## Verify

Legende: ✅ live bestätigt · ➖ nicht geprüft.
`AI` = nur KI · `Human` = nur Mensch (nie überschreiben).

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Export, Einstellungen | eine Datei, die ein Mensch lesen kann; Papiere und Überschreibungen vollständig | ➖ | |
| **2** | dieselbe Datei als `yaml-file`-Quelle | die Instanz läuft damit ohne Netz und zeigt denselben Bestand | ➖ | |
| **3** | Import in eine leere Datenbank | derselbe Bestand wie vor dem Export | ➖ | |
| **4** | Import in eine gefüllte Datenbank | die entschiedene Regel greift sichtbar, nichts verschwindet still | ➖ | |
| **5** | Zeitstempel nach dem Import | kein alter Kurs behauptet, frisch zu sein | ➖ | |
| **6** | Export während eines Schreibzugriffs | die Datei ist in sich stimmig | ➖ | |

## Nicht-Ziele

- Keine Rotation, keine `generation_id`, keine nummerierten Generationen — das
  ist T-25.
- Kein zweites Dateiformat neben dem Plugin-Vertrag.
- Keine Sicherung an einen entfernten Ort.

## Auflösung

_(offen — zuerst Mikes vier Entscheidungen)_
