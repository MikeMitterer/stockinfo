# Markdown schnell erfassen

Diese Seite zeigt die Wirkung von Orange Compact. **Wichtige Aussagen fallen
durch Fettschrift auf.** Die Erklärungen bleiben in normaler Schrift lesbar.

## Kurzfassung

- **Die Kernaussage steht in der ersten Zeile.**  
  Hier folgt die Erklärung. Sie gehört zum selben Eintrag und sollte deshalb
  näher an der Kernaussage stehen als am nächsten Bullet-Point.

- **Vor dem nächsten Eintrag ist deutlich mehr Abstand.**  
  So lassen sich die Punkte schnell voneinander unterscheiden. Auch längere
  Ergänzungen sollen ruhig lesbar bleiben, wenn sie mehrere Zeilen umfassen.

- **Verweise und technische Begriffe bleiben erkennbar.**  
  Ein [Link zur Anleitung](README.md) ist unterstrichen.
  Ein Wert wie `--md-item-gap` wird als Inline-Code dargestellt.

## Ablauf

1. **Eine CSS-Datei auswählen.**  
   Lade `orange-compact.css` in die Markdown-Vorschau.

2. **Überschriften und Listen vergleichen.**  
   Prüfe die Darstellung auch bei schmalem Vorschaufenster.

### Untergeordnete Punkte

- **Ein Hauptpunkt kann weitere Details enthalten.**
  - Erster Unterpunkt mit etwas Erklärung.
  - Zweiter Unterpunkt mit geringerem Abstand.
- **Hier beginnt wieder ein Hauptpunkt.**  
  Der Abstand soll ihn vom vorherigen Block abheben.

#### Überschrift der vierten Ebene

Auch kleinere Überschriften bleiben orange und fett.

##### Überschrift der fünften Ebene

Die Abstufung betrifft Farbe und Schriftgröße.

###### Überschrift der sechsten Ebene

Diese Ebene ist klein, bleibt aber als Überschrift erkennbar.

## Weitere Elemente

> **Eine wichtige Einschränkung gehört zur Erklärung.**
> Auch im Zitatblock bleibt der Originalhintergrund erhalten.

| Element | Darstellung |
|---|---|
| Überschrift | Orange, fett und mit Abstand zum vorherigen Abschnitt |
| Kernaussage | **Fett hervorgehoben** |
| Ergänzung | Normaler Text unter der Kernaussage |

```css
:root {
  --md-h1: #9a3900;
  --md-item-gap: 1.05em;
}
```

- [ ] Oberen Abstand des Dokumenttitels prüfen
- [ ] Blaue Fettschrift auf dunklem Hintergrund beurteilen
- [ ] Abstände zwischen Listeneinträgen prüfen

---

Normaler Text nach einer Trennlinie. *Kursive Ergänzungen* sollen ebenfalls
gut lesbar bleiben.
