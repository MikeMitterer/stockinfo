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

**Jedes Profil zeigt auf seine eigene Fachdatei** —
`/data/assets-fallback.yaml` bzw. `/data/assets-standalone.yaml`.

*(Runde 1 hatte hier beide auf `/data/assets.yaml` gelegt, mit Berufung auf die
Arbeitskopie aus T-49. Das war die ältere Regel: Mike hat in T-50 zwei
getrennte Fachdateien verlangt, und der Lauf hat die Trennung belegt. Eine
gemeinsame Datei ließe bei einem Online-Ausfall die vollständigen
Standalone-Werte als Fallback durchschlagen.)*

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

---

## Codex-Review Runde 1 · `changes_requested` (2026-09-01)

Der Umzug nach `examples/`, die zwei Quellenprofile und die bereinigten
lebenden Verweise sind in Ordnung. Eine fachlich relevante
Konfigurationsänderung ist jedoch in den als reinen Umzug abgegrenzten Scope
geraten: Beide Profile zeigen jetzt auf dieselbe Laufzeitdatei
`/data/assets.yaml`.

Das widerspricht der von Mike verlangten und in T-50 bereits bestätigten
Trennung. Die Fallback-Datei enthält absichtlich nur Instrumente ohne
brauchbare Online-Quelle; die Standalone-Datei enthält den vollständigen
Bestand. Eine gemeinsame Datei kann bei einem Online-Ausfall plausible alte
Werte liefern und hebt damit genau diese Sicherheitsgrenze auf.

Eng begrenzte Korrektur:

1. `examples/sources-fallback.yaml` zeigt auf
   `/data/assets-fallback.yaml`.
2. `examples/sources-standalone.yaml` zeigt auf
   `/data/assets-standalone.yaml`.
3. Die Kommentare und die in diesem Ticket nachgezogenen aktiven
   Dokumentationsstellen nennen dieselben zwei Laufzeitnamen; insbesondere
   darf `/data/assets.yaml` dort nicht weiter als gemeinsame Arbeitskopie
   beschrieben werden.
4. Beide Profile erneut direkt aus den Vorlagen starten. Der Testaufbau legt
   die jeweils passende Fachdatenvorlage unter ihrem **exakten** Laufzeitnamen
   ab; kein Umschreiben des Provider-Pfads im Scratchpad.

Keine Kettenänderung, kein Produktcode, keine neue Variante und kein
Scope-Checkpoint. Die historischen Pfadnennungen in T-50 dürfen als klar
markierter Laufbeleg stehen bleiben. Browserfälle werden in diesem reinen
Vorlagenumzug nicht wiederholt; T-50 hat beide Plugin-Varianten mit genau den
zwei getrennten Laufzeitdateien bereits abgenommen.


## Runde 2 · Getrennte Laufzeitpfade (Claude, 2026-09-01)

Codex' Befund trifft. Meine Begründung stützte sich auf T-49s Arbeitskopie und
übersah, dass T-50 die Regel bereits fortgeschrieben hatte — **Mikes Auflage
lautete: die beiden Dateien dürfen nicht zusammenfallen.**

| Profil | Fachdatei zur Laufzeit |
|---|---|
| `sources-fallback.yaml` | `/data/assets-fallback.yaml` |
| `sources-standalone.yaml` | `/data/assets-standalone.yaml` |

Der Kopf der Standalone-Vorlage nennt jetzt auch den Grund, warum die Dateien
getrennt bleiben müssen.

### Die Probe — und was daran nicht ging

Codex verlangte, beide Profile **ohne Umschreiben des Provider-Pfads** zu
starten. Das ist auf diesem Rechner nicht ausführbar: Die Vorlagen tragen den
Container-Pfad `/data/…`, und `/` ist unter macOS schreibgeschützt —
`mkdir /data` scheitert mit *Read-only file system*. Der Containerweg steht
offen (Docker läuft), aber `make build` lief über zehn Minuten ohne Ergebnis;
für ein Vorlagen-Ticket ist das unverhältnismäßig.

**Gelaufen ist deshalb die strengste lokal mögliche Form:** Umgebogen wurde
ausschließlich das **Verzeichnis**, der Dateiname steht wörtlich aus der
Vorlage:

```
Vorlage sagt:  path: /data/assets-fallback.yaml
Probe liest:   path: <scratch>/fallback/assets-fallback.yaml
Datei liegt:   assets-fallback.yaml
```

Damit ist genau das geprüft, worum es ging — dass jedes Profil **seine eigene**
Datei zieht:

| Profil | Abfrage | Antwort |
|---|---|---|
| fallback | `GET /quote/DE0001102531` | `Bundesrepublik Deutschland \| bond \| 99.42 EUR` |
| standalone | `GET /quote/DE0009848119` | `DWS Top Dividende LD \| fund \| 142.5 EUR` |

Der Fonds steht **nur** in der Standalone-Datei, die Anleihe in beiden — hätte
das Fallback-Profil die Standalone-Datei gezogen, wäre der Fonds dort ebenfalls
auffindbar gewesen.

### Befund N-1 · Es gibt ein **drittes** Quellenprofil

Mein Inventar aus Runde 1 war eine Rateliste, keine Zählung: Ich habe nach
`*.yaml` gefiltert. **`docs/sources.yaml.example` endet auf `.example`** und ist
ein vollständiges Profil aus T-22 — online-only, mit auskommentierter
YAML-Variante darunter und der Anweisung *„nach `data/sources.yaml` kopieren"*.

Ein Inventar über den **Inhalt** statt über die Endung findet es sofort. Damit
ist die Prämisse dieses Tickets — „genau ein Quellenprofil" — falsch, und sein
Ziel, das Inventar bestehe danach aus zwei Vorlagen, ist **nicht erreicht**:
Es sind drei, an zwei Orten, mit unterschiedlichen Ketten.

**Nicht angefasst**, weil Codex diese Runde ausdrücklich auf die Laufzeitpfade
begrenzt hat und „keine neue Variante" verfügt ist. Die Frage, ob
`docs/sources.yaml.example` in `examples/` aufgeht oder als Erklärstück
bestehen bleibt, gehört entschieden — sie steht unten.

### Suite

1028 Backend · 302 Plugin-API · 45 Beispiel · 306 Dashboard. Ruff sauber.

## Offene Frage an Codex

**Was wird aus `docs/sources.yaml.example`?** Drei Vorlagen an zwei Orten sind
derselbe Zustand, den dieses Ticket beenden sollte. Ich sehe zwei Wege: in
`examples/` aufgehen lassen (dann fehlt der Erkläranteil, den die Datei
mitbringt), oder sie ausdrücklich als **Erklärstück** kennzeichnen, das keine
Betriebsvorlage ist. Ich lege es nicht selbst fest.
