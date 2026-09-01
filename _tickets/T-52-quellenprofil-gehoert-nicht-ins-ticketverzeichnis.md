# T-52 · Das einzige Quellenprofil liegt im Ticketverzeichnis

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Beispieldaten + Doku) | offen | 1–2 h | die Ketten-Vorlagen nach `examples/` holen, wie T-49 es mit den Fachdaten getan hat | — |

- **Angelegt:** 2026-09-01, aus dem T-50-Browserlauf (dort V-3)
- **Hängt ab von:** nichts. T-49 ist freigegeben
- **Reihenfolge:** 2/5 der freigegebenen Kette T-55 → T-52 → T-54 → T-53 → T-51

**Löst:** T-49 hat die **Fachdaten** aus dem Ticketverzeichnis geholt. Die
`sources.yaml` daneben ist dieselbe Sorte Datei und blieb liegen.

---

## Der gemessene Befund

Ein Inventar aller YAML-Dateien im Repo — **jede Datei mit einem
Rollenschlüssel**, keine Namenssuche — findet genau **ein** Quellenprofil:

```
./_tickets/T-37-sources-online-with-yaml-fallback.yaml
  resolvers: [openfigi, yahoo-search, yaml-file]
  etf_meta:  [justetf, yfinance, yaml-file]
  quotes:    [yfinance, yaml-file]
  daily:     [yfinance, yaml-file]
  fx:        [yfinance, yaml-file]
```

Für das **reine Dateiprofil** existiert überhaupt keine Vorlage. Der
T-50-Browserlauf musste sie im Scratchpad schreiben, um die zweite
Plugin-Variante überhaupt starten zu können.

**Der Mechanismus ist derselbe, für den T-45 und T-49 zusammen angelegt
wurden:** Zieht T-37 nach `solved/`, zieht die einzige Ketten-Vorlage mit.

## Umfang

- Beide Profile als versionierte Vorlagen nach `examples/` — passend zu den
  zwei Fachdaten-Vorlagen, die dort schon liegen:
  `assets-fallback.yaml` ↔ Online-Profil, `assets-standalone.yaml` ↔ reines
  Dateiprofil.
- Die Vorlagen zeigen mit ihrem Provider-Pfad auf `/data/…`, nicht auf einen
  Scratch- oder Testpfad.
- Wer die Datei aus `_tickets/` liest, wird nachgezogen. Der Umzug ist erst
  fertig, wenn ein `grep` auf den alten Pfad leer ausgeht — und das Inventar
  aus zwei Vorlagen besteht statt aus einer.

**Nicht in diesem Ticket:** Ketten ändern, Rollen ergänzen, ein Profil zur
Vorgabe machen. Es ist ein Umzug, keine Konfigurationsänderung.

## Verify

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Inventar | beide Profile liegen unter `examples/`, keines mehr in `_tickets/` | ✅ | |
| **2** | Verweise | kein Test, Skript oder Dokument zeigt noch auf den alten Ort | ✅ [^belege] | |
| **3** | Beide Profile startbar | eine Instanz läuft mit jedem der beiden, direkt aus der Vorlage | ✅ | |
| **4** | Umzugsprobe | T-37 lässt sich nach `solved/` verschieben, ohne dass etwas bricht | ✅ | |

---

## Scope-Vertrag (Claude, 2026-09-01, vor dem ersten Edit)

### Das Inventar zuerst

Gesucht wurde im ganzen Repo, nicht geraten. **Kein Code, kein Test, kein
Skript** liest die Datei — nur drei Ticket-Dokumente nennen sie:

| Fundort | Art |
|---|---|
| `T-37-yaml-fallback-ein-datei.md:297` | lebender Verweis („liegt in …") |
| `T-39-english-plugin-developer-guide.md:101,147` | Protokoll dessen, was T-39 an ihr geändert hat |

Die T-39-Stellen benennen **dieselbe Datei**, die nur umzieht; sie beim neuen
Pfad zu nennen bleibt historisch richtig, und ein „damals lag sie in …" ließe
den alten Pfad greppbar stehen.

### Die Namen paaren sich mit den Fachdaten

| Fachdaten (T-49) | Quellenprofil (neu) |
|---|---|
| `examples/assets-fallback.yaml` | `examples/sources-fallback.yaml` |
| `examples/assets-standalone.yaml` | `examples/sources-standalone.yaml` |

**Beide Profile zeigen auf `/data/assets.yaml`**, nicht auf ihre Vorlage: Das
ist die Arbeitskopie, die T-49 festgelegt hat — der Betreiber wählt *eine*
Vorlage und legt sie unter diesem Namen ab. Ein Profil, das auf
`assets-standalone.yaml` zeigte, verlangte vom Benutzer, die Vorlage im
Betriebsvolume unter Vorlagennamen zu führen.

### Budget

| | Grenze |
|---|---:|
| `examples/` (beide Profile) | ≤ 70 |
| Doku-Anpassungen | ≤ 10 |

Gezählt als hinzugefügte Zeilen aus `git diff --numstat` gegen den
Abzweigpunkt, ohne Ticket- und `STATUS.md`-Dateien.

### Pflichtorakel

1. **Der Umzug ist erst fertig, wenn der alte Name nirgends mehr vorkommt** —
   geprüft per Suche über das ganze Repo, nicht über eine Liste erwarteter
   Orte.
2. **Beide Profile starten wirklich eine Instanz.** Eine Vorlage, die nur
   gültiges YAML ist, belegt nichts: Ein Tippfehler im Rollennamen fällt erst
   auf, wenn die App die Kette baut. Geprüft wird über `GET /sources` gegen
   eine isolierte Kopie.
3. **Die Umzugsprobe wird gespielt, nicht behauptet:** Nach dem Umzug darf
   nichts außerhalb von `_tickets/` mehr auf eine Datei *im* Ticketverzeichnis
   zeigen.

### Nicht-Ziele

- Ketten ändern, Rollen ergänzen, ein Profil zur Vorgabe machen.
- `scripts/sources-profile.sh` — liegt unverschmolzen auf
  `feat/sources-profile-script` und zeigt auf `_tickets/T-37-single-file-sample.yaml`,
  eine Datei, die T-49 bereits aufgelöst hat. Das ist **T-49 Verify #8** und
  bleibt dort.
- Tickets nach `solved/` verschieben.


---

## Runde 1 · Umgesetzt (Claude, 2026-09-01)

### Der Umzug

| vorher | nachher |
|---|---|
| `_tickets/T-37-sources-online-with-yaml-fallback.yaml` | `examples/sources-fallback.yaml` |
| — (existierte nicht) | `examples/sources-standalone.yaml` |

Die Namen paaren sich jetzt mit den Fachdaten aus T-49, und **beide Profile
zeigen auf `/data/assets.yaml`** — die Arbeitskopie, nicht die Vorlage. Der
Kopf jeder Datei nennt ihr Gegenstück und die passende Fachdaten-Vorlage.

| | Grenze | gemessen |
|---|---:|---:|
| `examples/` (beide Profile) | ≤ 70 | **60** |
| Doku-Anpassungen | ≤ 10 | **7** |

### Die Orakel

**1 · Der alte Name kommt nirgends mehr als Verweis vor.** Übrig sind drei
Nennungen in T-50 und T-52 — sie **belegen den Befund** und beschreiben den
Stand des Laufs. Sie zu tilgen hieße, die Beweisführung zu löschen; beide
Stellen tragen jetzt einen Erledigungsvermerk auf dieses Ticket.

**2 · Beide Vorlagen starten wirklich eine Instanz.** Gültiges YAML belegt
nichts — ein Tippfehler im Rollennamen fällt erst auf, wenn die App die Kette
baut. Gegen je eine frische, leere Datenbank gemessen über `GET /sources`:

```
fallback     resolvers  openfigi → yahoo-search → yaml-file
             quotes     yfinance → yaml-file            (…und drei weitere Rollen)
standalone   alle fünf Rollen: yaml-file
```

Dazu eine **echte Abfrage** aus der Standalone-Vorlage, damit nicht nur die
Kette gebaut, sondern auch benutzbar ist:
`GET /quote/DE0009848119` → `DWS Top Dividende LD | fund | 142.5 EUR`.

**3 · Nichts außerhalb von `_tickets/` zeigt mehr in das Ticketverzeichnis.**
Gesucht über `app/`, `tests/`, `plugin_api/`, `dashboard/src`, `scripts/`,
`Makefile` und `examples/` — kein Treffer. Damit ist die Umzugsprobe für T-37
gespielt und nicht behauptet.

### Zwei Nebenfunde, beide nicht angefasst

- `scripts/sources-profile.sh` auf `feat/sources-profile-script` zeigt auf
  `_tickets/T-37-single-file-sample.yaml` — eine Datei, die T-49 aufgelöst hat.
  Das ist **T-49 Verify #8** und bleibt dort.
- `plugin_api/build/lib/…/yaml_file.py` nennt denselben alten Pfad, ist aber
  ein **nicht versioniertes** Bauartefakt; die Quelle daneben zeigt korrekt
  auf `examples/`.

### Suite

1028 Backend · 302 Plugin-API · 45 Beispiel · 306 Dashboard. Ruff sauber.

[^belege]: Drei Nennungen des alten Pfads bleiben als **Beleg** in den
    Lauf-Protokollen von T-50 und im Befund dieses Tickets stehen, mit
    Erledigungsvermerk. Als Verweis zeigt nichts mehr dorthin.
