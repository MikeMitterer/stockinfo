# Design: Navigation entrümpeln + Einstellungsseite (T-11a)

**Datum:** 2026-08-15
**Ticket:** `_tickets/T-11-ux-standards-angleichen.md` (Epic) → Teil-Ticket `T-11a`
**Scope:** Frontend (Dashboard). Kein Backend-Change.
**Bezug:** Skill `ux-standards` (Navigation, Einstellungen), Gap-Analyse Punkte 1+2.

## Problem

Das Hauptmenü hat **7** Top-Tabs (Assets, Börsen, Environment, API & Links,
Themes, Analyse, Devisen) — der Skill will drei bis fünf **Arbeitsbereiche**.
Vier davon sind keine Arbeitsbereiche, sondern Konfiguration/Nachschlagen
(Themes, Environment, API & Links) bzw. sitzen am falschen Ort (Sprach-Umschalter
in der Kopfzeile). Es gibt keine Einstellungsseite; jede Config ist ein eigener
Top-Tab. Adressierbare Reiter (`#/settings?tab=…`) fehlen, weil `useHashTab` nur
`#/<tab>` kennt und alles nach `?` verwirft.

## Lösung

Hauptmenü auf **vier Arbeitsbereiche** reduzieren, alle Config/Diagnose unter
**eine Einstellungsseite mit adressierbaren Reitern** ziehen, Zugang über ein
**Zahnrad rechts** in der Kopfzeile (kein Menüpunkt).

### 1. Hauptmenü (AppHeader)

- Neue Reihenfolge (Arbeitsbereiche): **Assets · Börsen · Devisen · Analyse**
  (`assets`, `exchanges`, `fx`, `analysis`). Analyse bewusst als letzter Punkt.
- `themes`, `environment`, `links` verschwinden als Top-Tabs → in Settings.
- **Sprach-Umschalter (DE/EN) raus aus der Kopfzeile** → Settings-Reiter „Sprache".
- Rechts in der Kopfzeile: ein **Zahnrad-Symbol (⚙)** als Settings-Zugang statt
  des DE/EN-Umschalters. Aktiv-Zustand am Zahnrad, wenn Settings offen.
  Begründung Skill: „Das Menü gehört dem Nutzer, nicht der Funktionsliste" —
  Einstellungen sind kein Arbeitsbereich.
- Das Hauptmenü ist **linksbündig** (schließt an die Wortmarke an); die rechte
  Seite trägt nur Nicht-Navigation: das **Zahnrad** (Settings) und künftig
  **User/Login**. (ux-standards: „Alles, was zur Navigation gehört, steht
  links … rechts steht nur, was nicht Navigation ist.")

### 2. `TabKey` & Routing-Struktur

- `TabKey` (types.ts:91): `themes`/`environment`/`links` entfallen als eigene
  Werte im Menü; neu hinzu **`settings`**. `NavIconName` (types.ts:94) analog:
  neues Icon `settings`; `themes`/`environment`/`links` als Menü-Icons entfernt
  (bleiben aber ggf. als Reiter-Icons in Settings, siehe §3).
- Die drei Sync-Stellen (`tabs`-Array AppHeader, `TABS`-Whitelist useHashTab,
  `v-if`-Kette App.vue) werden gemeinsam umgestellt: Arbeitsbereiche + `settings`.

### 3. Einstellungsseite (neue Komponente `SettingsPanel.vue`)

- Container mit Reiter-Leiste. Reihenfolge nach Skill (Nähe zur Arbeit; Diagnose
  ganz rechts, abgesetzt):
  **Darstellung → Sprache → API & Links → Environment**.
- **Inhalt wird wiederverwendet, nicht neu gebaut:** bestehende `ThemesPanel`,
  `LinksPanel`, `EnvironmentPanel` werden als Reiter-Inhalt eingehängt.
  `EnvironmentPanel` behält seine `env`-Prop — App.vue reicht `env` an
  `SettingsPanel` durch, das es an den Environment-Reiter weitergibt.
- Nur **„Sprache"** ist ein kleiner neuer Block: DE/EN-Auswahl, ruft das
  vorhandene `setLanguage` (dieselbe Logik wie der bisherige Kopfzeilen-Umschalter,
  nur an neuem Ort). Der Block zeigt die **aktuell wirksame** Sprache als aktiv.
- **Erst-Besuch-Default = Browser-Sprache (unverändert).** Ohne gespeicherte
  Wahl gilt weiter `detectLocale()` (i18n/index.ts:24): localStorage → Browser
  (`navigator.language` `de*` → Deutsch, sonst Englisch-Fallback). T-11a **darf
  dieses Verhalten nicht ändern** — der Umschalter wandert nur an einen neuen
  Ort, die Erkennung bleibt. Eine Wahl im Sprach-Block persistiert wie bisher
  über `setLanguage` und gewinnt ab dann gegen die Browser-Sprache.
- Environment-Reiter sichtbar abgesetzt (Trenner/Abstand), da Diagnose.

**Aktiv-Markierung sprachwechselfest (Skill: „Fremdkomponenten messen beim
Einhängen").** Der Sprachwechsel passiert **im Sprach-Reiter selbst** und ändert
alle Reiter-Label-Breiten — ein einmal aus Positionen berechneter Schiebebalken
bliebe dann stehen und die Markierung wäre falsch. Vermeidung by construction:
Die Aktiv-Markierung der Settings-Reiter ist **messungsfrei** — ein
per-Reiter-CSS-Unterstrich am aktiven Element (`tab === settingsTab`), wie in der
Hauptnav (AppHeader), **kein** positionsberechneter Slider. Damit folgt die
Markierung dem aktiven Reiter automatisch, ohne Neuberechnung bei Relabel.
Sollte (jetzt oder später) doch eine messende Fremdkomponente eingesetzt werden,
gilt die Skill-Regel `:key="localeStore.current"`-Remount bei Sprachwechsel.
Dasselbe gilt für die Hauptnav: deren Aktiv-Unterstrich ist bereits per-Item-CSS
und damit relabel-fest — T-11a darf das nicht auf einen gemessenen Slider
umstellen.

### 4. Adressierbare Reiter (`useHashTab` erweitern)

- Hash-Format: `#/settings?tab=appearance|language|links|environment`. Andere
  Tabs unverändert `#/<tab>`.
- `useHashTab` bleibt **die eine Stelle, die die URL-Struktur besitzt** — kein
  zweites Composable, das konkurrierend in den Hash schreibt. Rückgabe wird von
  `Ref<TabKey>` auf ein Objekt `{ tab, settingsTab }` erweitert:
  - `tab: Ref<TabKey>` — wie bisher.
  - `settingsTab: Ref<SettingsTab>` — nur relevant, wenn `tab === 'settings'`.
  - Parsing: Hash am `?` splitten, linker Teil gegen `TABS` validieren, aus dem
    rechten Teil `tab=`-Query lesen und gegen die Settings-Reiter-Liste
    validieren (Default `appearance`).
  - Schreiben: `tab === 'settings'` → `#/settings?tab=<settingsTab>`, sonst
    `#/<tab>` (unverändert). Beim Wechsel **auf** `settings` wird der zuletzt
    gewählte Reiter beibehalten (Default `appearance`).
- Einziger Consumer ist App.vue:53 (`const activeTab = useHashTab()`) → kleiner
  Umbau auf Destructuring `{ tab, settingsTab }`; AppHeader bekommt weiter nur
  `tab` als `:active`.

### 5. i18n

Neue Keys in **beiden** Katalogen (de.ts = Schema-Quelle, sonst brechen die
Typen — `MessageSchema = typeof de`):

- `nav.settings` — aria-label/Titel des Zahnrads („Einstellungen" / „Settings").
- `settings.title` — Überschrift der Seite.
- `settings.tab.appearance` — „Darstellung" / „Appearance".
- `settings.tab.language` — „Sprache" / „Language".
- `settings.tab.links` — „API & Links" (bestehende `nav.links`-Formulierung
  übernehmen, aber eigener Key unter `settings.*`).
- `settings.tab.environment` — „Environment".
- `settings.language.*` — Beschriftung des Sprach-Blocks, soweit nötig; die
  DE/EN-Optionslabels nutzen die bestehenden `language.*`-Keys.

`nav.themes`/`nav.environment`/`nav.links` werden nicht mehr fürs Hauptmenü
gebraucht, bleiben aber als Keys bestehen (Panels tragen eigene Titel); keine
Löschwelle in T-11a.

## Betroffene Einheiten

| Datei | Änderung |
|---|---|
| `src/types.ts` | `TabKey`: `themes/environment/links` raus, `settings` rein; `NavIconName` analog (+ `settings`-Icon); neuer Typ `SettingsTab = 'appearance' \| 'language' \| 'links' \| 'environment'` |
| `src/components/AppHeader.vue` | `tabs`-Array auf 4 Arbeitsbereiche; DE/EN-Umschalter raus; Zahnrad-Button rechts (emittiert `navigate('settings')`), Aktiv-Zustand |
| `src/components/NavIcon.vue` | `settings`-Icon (Zahnrad) ergänzen |
| `src/components/SettingsPanel.vue` | **neu** — Reiter-Container, hängt ThemesPanel/LinksPanel/EnvironmentPanel + Sprach-Block ein; `env`-Prop durchreichen; `settingsTab` v-model |
| `src/composables/useHashTab.ts` | Query-Parsing; Rückgabe `{ tab, settingsTab }`; `settings` in `TABS` |
| `src/App.vue` | Destructuring `{ tab, settingsTab }`; `v-if`-Kette: Config-Tabs raus, `settings`-Zweig rein (rendert `SettingsPanel`, reicht `env` + `settingsTab`) |
| `src/i18n/de.ts`, `src/i18n/en.ts` | neue `nav.settings` + `settings.*`-Keys |
| `tests/composables/useHashTab.spec.ts` | erweitern: Query-Parsing, `settingsTab`, Schreib-Format |
| `tests/components/AppHeader.spec.ts` | anpassen: 4 Tabs, Zahnrad statt DE/EN, `navigate('settings')` |
| `tests/components/SettingsPanel.spec.ts` | **neu** — Reiter-Wechsel, Default-Reiter, Sprach-Block ruft `setLanguage` |

Kein Backend-Change.

## Teststrategie (TDD)

Test zuerst, dann Implementierung — je Einheit.

- **`useHashTab.spec.ts`:** `#/settings?tab=language` → `tab='settings'`,
  `settingsTab='language'`; unbekannter `tab=`-Wert → Default `appearance`;
  Setzen von `settingsTab` schreibt `#/settings?tab=…`; Wechsel auf einen
  Arbeitsbereich schreibt wieder `#/<tab>` (kein `?`-Rest); bestehende
  Tab-Tests bleiben grün.
- **`AppHeader.spec.ts`:** genau 4 Menüpunkte; kein DE/EN-Umschalter mehr;
  Zahnrad vorhanden (`aria-label` aus `nav.settings`), Klick emittiert
  `navigate('settings')`.
- **`SettingsPanel.spec.ts`:** Default-Reiter `appearance`; Klick auf „Sprache"
  zeigt den Sprach-Block; DE/EN-Auswahl ruft `setLanguage`; Reihenfolge der
  Reiter Darstellung→Sprache→Links→Environment; Environment ganz rechts.
- **`SettingsPanel.spec.ts` (Sprachwechsel-Marker):** aktiver Reiter =
  „Sprache", `setLanguage` wechselt Locale → Reiter-Labels ändern sich, aber
  `settingsTab` bleibt `language` und die Aktiv-Markierung bleibt am
  Sprach-Reiter (per-Item-CSS, kein Positions-Reset).
- **Browser-Verifikation (eigener Task, Teil der Verify-Matrix):** Hauptmenü 4
  Punkte; Zahnrad öffnet Settings; Reiter direkt per URL ansteuerbar
  (`#/settings?tab=environment` lädt den Environment-Reiter); Sprachwechsel wirkt
  app-weit; **Sprache im Sprach-Reiter umschalten → Aktiv-Markierung bleibt auf
  „Sprache" (kein verrutschter Balken), Hauptnav-Markierung stimmt ebenfalls
  nach Sprachwechsel**; unter 768px keine Überlappung; Desktop unverändert.

## Bewusst NICHT im Scope (YAGNI — eigene Teil-Tickets)

- Token-Aliase / hartkodierte Farben ersetzen → **T-11b**.
- Assets-Tabelle mobil → Kartenliste (`useIsCompact`) → **T-11c**.
- Theme-Namen/Paletten/Kontrast abgleichen → **T-11d**.
- Statuszeile, Toast-Meldungen, „?"-Hinweise → **T-11e**.
- Keine visuelle Neugestaltung der eingehängten Panels — sie werden nur
  verschoben, nicht umgebaut. Feinschliff der Settings-Optik läuft mit T-11b/d.
- Kein neues Responsive-Verhalten außer der Vereinfachung durch die 4-Punkte-Nav
  (Header ist mit T-05 bereits mobil).
