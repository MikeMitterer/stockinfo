# Orange Compact für IntelliJ

**Compact ist der ausgewählte Stil.** Er verwendet die verfügbare Breite,
eine serifenlose Systemschrift und den Originalhintergrund der Vorschau.
Überschriften sind orange abgestuft und haben keine Zierlinien.
Die ersten drei Überschriftenebenen unterscheiden sich jetzt deutlicher:
`#` im ursprünglichen Orange (`#ffa321`), `##` in kräftigem Orange (`#f58a24`),
`###` in gedämpftem Orange (`#dca052`).

Fettschrift bleibt blau (`#70acff`). Mint und Rosé wurden verworfen;
[orange-compact.css](orange-compact.css) ist die einzige aktuelle Variante.

## Laden und ausprobieren

Wähle unter **Settings → Languages & Frameworks → Markdown → Custom CSS →
Load from** die Datei [orange-compact.css](orange-compact.css).

Die [Testseite](preview.md) zeigt Überschriften, Listen, Tabellen und Code.
Zum Lesen eines echten Dokuments eignet sich das
[Ticket T-56](../../_tickets/40-done/T-56-was-mike-im-ui-pruefen-soll.md).

## Farben und Abstände anpassen

Alle einstellbaren Werte stehen oben im CSS im Block `:root`:

- **`--md-h1` bis `--md-h6` bestimmen die Überschriftenfarben.**  
  `--md-strong` steuert die Fettschrift. Der aktuelle Wert `#70acff`
  ist ein für dunkle Flächen aufgehelltes Komplementärblau zum Orange.

- **`--md-first-heading-gap` steuert den oberen Abstand des Dokumenttitels.**  
  Er steht auf `0`. Auch der obere Außen- und Innenabstand der
  Vorschaucontainer wird auf `0` gesetzt.
  Spätere Überschriften behalten den Abstand aus `--md-heading-gap`.

- **Tabellenzellen haben einen eigenen Innenabstand.**  
  `--md-table-cell-padding-y` steht auf `0.6em` für oben und unten,
  `--md-table-cell-padding-x` auf `0.9em` für links und rechts.

- **`--md-item-gap` steuert den Abstand zwischen Listeneinträgen.**  
  `--md-nested-item-gap` gilt für Unterpunkte.
  `--md-paragraph-gap` trennt normale Absätze.

- **Schrift und Zeilenhöhe sind separat einstellbar.**  
  Dafür stehen `--md-font-family`, `--md-font-size` und
  `--md-line-height` bereit. Code behält seine Monospace-Darstellung.

- **Codeblöcke und Chat-Aufträge erhalten eine dunkelgraue Fläche.**  
  `--md-code-background`, `--md-code-border` und `--md-code-text` bestimmen
  die Farben. Innenabstand, Rundung und Schrift stehen in `--md-code-padding`,
  `--md-code-radius` und `--md-code-font-family`. Als `text` markierte Blöcke
  dürfen lange Zeilen visuell umbrechen; der kopierbare Inhalt bleibt erhalten.

Die CSS-Datei ist für die IntelliJ-Vorschau vorbereitet. Für Obsidian wird
keine Kompatibilität mit deinem bislang unbekannten Styling-Plugin behauptet.
Eine visuelle Prüfung der aktuellen Anpassung in IntelliJ steht aus.
