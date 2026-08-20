# T-25 · Quellenprofil wechseln — Sicherung und frische Datenbank

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | offen | 1 Tag | Profilbegriff, Sicherung, Rotation, Wiederherstellung | — |

**Löst:** Ein **Quellenprofil** ist die Gesamtheit der aktiven Quellen einer
Instanz. Profil A durch B zu ersetzen ist etwas anderes, als innerhalb von A
eine Quelle zu ergänzen — und dieser Unterschied fehlt im Entwurf bisher ganz.

**Design:** [`docs/superpowers/specs/2026-08-19-plugin-system-design.md`](../docs/superpowers/specs/2026-08-19-plugin-system-design.md)

> **Herkunft:** von Mike entschieden (2026-08-20), hier aus Codex' Wiedergabe
> übernommen. Vor der Umsetzung mit Mike gegenzulesen — die Formulierung stammt
> nicht aus erster Hand.

**Hängt an:** T-22 (ohne Profil in der Konfiguration gibt es nichts zu wechseln).
**Nicht zu verwechseln mit T-19**, das ein einzelnes Papier neu auflöst.

---

## Verify

Legende: ✅ live bestätigt · ⚠️ mit Einschränkung · ◑ teilweise · ➖ keine Live-Verifikation.

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| 1 | Quelle **innerhalb** desselben Profils ergänzen, Neustart | bestehende Instrumente unverändert, **dieselbe** Datenbank | | |
| 2 | Paketversion im selben Profil anheben, Neustart | dito — kein Datenbankwechsel | | |
| 3 | Profil A durch B ersetzen | A wird gesichert **bevor** B startet | | |
| 4 | nach #3 | B läuft auf einer **frischen** Datenbank | | |
| 5 | Sicherungsverzeichnis | fortlaufend nummeriert, mit Manifest: Profil, Stand, Zeitpunkt | | |
| 6 | Wiederherstellung | ordnet Sicherung und Profil einander zu; ein unpassendes Paar wird abgelehnt | | |
| 7 | `GET /sources` oder `/env` | nennt das aktive Profil und dessen Generation | | |
| 8 | Konsument (Dashboard) nach Profilwechsel | bemerkt den Wechsel, statt alte Werte weiterzuzeigen | | |

---

## Details

### Zwei Vorgänge, die man nicht verwechseln darf

| Vorgang | Bestehende Instrumente | Datenbank |
|---|---|---|
| Quelle ergänzen/aktualisieren (in A) | unverändert | bleibt |
| Profil A → B | — | **frisch**, A wird gesichert |

Erst diese Trennung bringt zwei Invarianten widerspruchsfrei zusammen:

- „Eine Installation verändert nichts von selbst" (Voraussetzung dafür, dass
  T-19 nachrangig sein darf)
- „B ersetzt A mit frischer Datenbank"

### Was ein belastbares Backup braucht

Nicht nur die Datei kopieren:

- **Fortlaufende Nummer** statt Zeitstempel allein — sonst ist die Reihenfolge
  bei gleichzeitigen Läufen unklar
- **Manifest**: welches Profil, welcher Schema-Stand, wann, wie viele Instrumente
- **Konsistenz**: die Sicherung entsteht, während nichts schreibt — der
  Scheduler muss dafür stehen
- **Zuordnung beim Zurückholen**: Eine Sicherung aus Profil A in Profil B
  einzuspielen ist ein Fehler, kein Sonderfall

### Warum Konsumenten das mitbekommen müssen

Ein Cache über den Profilwechsel hinweg zeigt Werte aus einer Datenbank, die es
nicht mehr gibt. Deshalb gehört eine **Generation** in die API — ändert sie
sich, verwirft der Konsument seinen Cache. Das ist der Punkt, an dem dieses
Ticket den REST-Vertrag aus T-24 berührt.

---

## Auflösung

_(offen)_
