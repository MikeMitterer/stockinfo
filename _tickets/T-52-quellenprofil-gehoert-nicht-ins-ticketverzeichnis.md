# T-52 · Das einzige Quellenprofil liegt im Ticketverzeichnis

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Beispieldaten + Doku) | offen | 1–2 h | die Ketten-Vorlagen nach `examples/` holen, wie T-49 es mit den Fachdaten getan hat | — |

- **Angelegt:** 2026-09-01, aus dem T-50-Browserlauf (dort V-3)
- **Hängt ab von:** nichts. T-49 ist freigegeben
- **Reihenfolge:** offen, **nicht** in der `priority_chain`

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
| **1** | Inventar | beide Profile liegen unter `examples/`, keines mehr in `_tickets/` | ➖ | |
| **2** | Verweise | kein Test, Skript oder Dokument zeigt noch auf den alten Ort | ➖ | |
| **3** | Beide Profile startbar | eine Instanz läuft mit jedem der beiden, direkt aus der Vorlage | ➖ | |
| **4** | Umzugsprobe | T-37 lässt sich nach `solved/` verschieben, ohne dass etwas bricht | ➖ | |
