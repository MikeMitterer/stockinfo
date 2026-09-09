# T-11 · App an ux-standards angleichen (Epic)

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| frontend | backlog (Epic) | mehrphasig | UI-Architektur | — |

**Löst:** Die App an den Skill `ux-standards` angleichen. **Epic** — beim Angehen
in Einzel-Tickets (T-11a…e) zerlegen; der Skill nennt die Reihenfolge
„sichtbarer Gewinn zuerst, Risiko zuletzt". Nicht in einem Rutsch.

<!--
  Repo:   frontend (dashboard/)
  Scope:  UI-Architektur — mehrere Komponenten. Bewusst als Epic gehalten.
-->

---

## Gap-Analyse (Stand 2026-08-15, CC)

Bezug: `~/.claude/skills/ux-standards/SKILL.md`.

### 1. Navigation entrümpeln — *größte Wirkung, kleinster Eingriff*
- **Ist:** Hauptmenü hat **7** Punkte (Assets, Börsen, Environment, API & Links,
  Themes, Analyse, Devisen). Sprach-Umschalter (DE/EN) sitzt in der Kopfzeile.
- **Soll (Skill: 3–5 Punkte; Umschalter/Config nicht ins Menü/die Kopfzeile):**
  - Arbeitsbereiche im Menü: **Assets, Analyse, Devisen** (evtl. Börsen).
  - Nach **Einstellungen** verschieben: **Themes**, **Environment**,
    **API & Links**, **Sprache** (aus der Kopfzeile).
- Betroffen: `AppHeader.vue`, `App.vue` (Tab-Routing), `useHashTab.ts`.

### 2. Einstellungsseite mit adressierbaren Reitern
- **Ist:** keine. Themes/Environment/Links sind eigene Top-Tabs.
- **Soll:** eine Seite `#/settings?tab=…`, Reiter über die Adresse ansteuerbar
  (damit Hinweise gezielt auf eine Einstellung verweisen können). Reihenfolge:
  Verhalten/Rechnen → Darstellung/Daten → Sprache → Status/Diagnose ganz rechts.

### 3. Token-Aliase (nicht umbenennen)
- **Ist:** `--c-*` (base.scss) + `$color-*`/`$health-*` (\_variables.scss).
- **Soll:** Alias-Zeile auf die Skill-Namen legen — `--surface-page/-card/-sunken`,
  `--edge`, `--ink-primary/-secondary/-muted`, `--accent`,
  `--status-ok/-near/-out` → auf die bestehenden `--c-*`/`$health-*` mappen.
  Keine Umbenennungswelle. Macht Komponenten zwischen Apps portierbar.
- Nebenbei: hartkodierte Farben ersetzen (z.B. `#e5484d` in `.err` von
  `FxPanel.vue`/`AnalysisPanel.vue` → Token).

### 4. Mobil: Tabellen unter `md` (768px) zu Kartenliste
- **Ist:** Assets-Tabelle (`InstrumentsTable.vue`) hat **> 4** Spalten
  (Symbol, ISIN, Name, Typ, Kurs, TER, Vola, Thes, Pkt + Aktionen). Unter 768px
  bleibt es eine (scrollende) Tabelle.
- **Soll:** unter `md` je Zeile eine **Karte** mit den 2–3 wichtigsten Werten +
  Status; Umschaltung via Composable `useIsCompact` (matchMedia), nicht via
  verstreutem CSS. (Header ist mit T-05 schon mobil; die Tabelle noch nicht.)

### 5. Themes abgleichen
- **Ist:** viele Themes in `base.scss` (`[data-theme]`). Umschaltung/localStorage
  vorhanden.
- **Soll (Skill):** gleiche Theme-**Namen** ⇒ gleiche Farbe über Apps hinweg;
  bedeutungstragende Farben (Status/Kategorie) themeunabhängig; Kontrast prüfen
  (ΔE-Regeln). Prüfen/ggf. Namen vereinheitlichen.

### Weitere Punkte (kleiner)
- **Statuszeile** (`StatusBar.vue`): Skill will links App-Name + **aktiver
  Kontext** + Daten-Alter, rechts Version + **Service-Status-Punkt → Statusseite**.
  Aktiver Kontext fehlt (sobald es mehr als einen gibt).
- **Erklärungen:** „?"-Hinweise an unklaren Begriffen mit bis zu zwei Verweisen
  (links Vertiefung, rechts „Zur Einstellung →"). Teilweise vorhanden
  (strict_exchange, Config-Herkunft aus T-07).
- **Meldungen:** Zustände als **Toast**, nicht im Textfluss (aktuell z.T.
  Inline-`ErrorBanner`). Prüfen, ob das den Skill-Regeln genügt (verschwindet,
  wenn Ursache entfällt; Fehler bleiben bis Klick).

---

## Vorgeschlagene Zerlegung (je eigenes Ticket beim Angehen)

- **T-11a** Navigation entrümpeln + Einstellungsseite mit Reitern (Punkte 1+2).
- **T-11b** Token-Aliase + hartkodierte Farben ersetzen (Punkt 3).
- **T-11c** Assets-Tabelle mobil → Kartenliste (`useIsCompact`) (Punkt 4).
- **T-11d** Themes-Namen/Kontrast abgleichen (Punkt 5).
- **T-11e** Statuszeile + Toast-Meldungen + „?"-Hinweise (Rest).

Reihenfolge wie im Skill: 1 → 2 → 3 → 4 → 5.

## Verify

_(pro Teil-Ticket eigene Matrix — dieses Epic ist der Überblick.)_

## Details

### Side-Effects
Architektur-Umbau über mehrere Komponenten. Keine Backend-Änderung erwartet.
i18n für alle neuen Texte (Skill setzt code-standards/i18n voraus).

### Auflösung
_(offen — Epic; beim Start in T-11a…e zerlegen)_

---

## Abschluss (2026-08-16)

Epic geschlossen. Der Branch-Stapel `t-11a → t-11b → t-11c → t-11i → t-11d` ist
per Fast-Forward nach `master` geführt (147 Tests grün, `vue-tsc` sauber).

Die fünf noch offenen Teile (T-11d/e/f/g/h) werden **nicht einzeln** umgesetzt:
Seit dem 16.08.2026 gibt es `@mikemitterer/ux-foundation`, und jedes dieser
Tickets baut genau das nach, was das Paket mitbringt — Paletten, Schriften,
Leisten, Symbole, Marke. Sie gehen in **T-12** auf, das die App auf das
Fundament umstellt. Ihre inhaltlichen Anforderungen sind dort als
Abnahmekriterien übernommen.
