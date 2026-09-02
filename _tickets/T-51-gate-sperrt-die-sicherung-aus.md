# T-51 · Das Migrationsgate sperrt die Sicherung aus, zu der es rät

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | offen | 1–2 h | entscheiden, ob Sicherungen vor dem Migrationsgate erreichbar sind — und den Gate-Text nachziehen | — |

- **Angelegt:** 2026-09-01, aus dem T-50-Browserlauf (dort V-1)
- **Hängt ab von:** nichts. T-47 ist freigegeben
- **Reihenfolge:** 5/5 der freigegebenen Kette T-55 → T-52 → T-54 → T-53 →
  T-51; vor dem Produktedit ist Mikes Variantenentscheidung nötig

**Löst:** Ein Benutzer mit offener Identitätsmigration wird zu einer Handarbeit
aufgefordert, für die das Produkt seit T-47 ein Werkzeug hat — das in genau
diesem Moment unerreichbar ist.

---

## Der gemessene Befund

Bei offener Migration antwortet die App auf **jedem** Fachweg mit
`503 migration_pending`. Gemessen an einer isolierten Kopie:

```
GET  /sources               503
GET  /instruments           503
GET  /analyze?isin=US0378331005  503
GET  /env                   503
GET  /backups               503
POST /backups               503
```

Der Gate-Bildschirm sagt dabei:

> *„Der Umzug lässt sich nicht rückgängig machen. Legen Sie eine Kopie der
> Datenbankdatei an, bevor Sie bestätigen."*

**Das Gate ist älter als T-47** und deshalb kein Regress. Dass ein *Schreibweg*
vor einer offenen Migration gesperrt ist, ist vertretbar. Zwei Dinge sind es
nicht:

1. `GET /backups` ist ein reiner **Leseweg** und trägt dieselbe Sperre.
2. Die Empfehlung im Gate beschreibt einen Handgriff aus der Zeit vor T-47.

## Zu entscheiden, bevor jemand etwas ändert

Es gibt mindestens drei tragfähige Antworten, und die Wahl ist eine
Produktentscheidung über Gate und API, keine Anzeigekorrektur:

- **A** — `GET /backups` und `POST /backups` vor dem Gate freigeben. Kürzeste
  Änderung; macht das Gate aber löchrig und wirft die Frage auf, welcher Weg
  als Nächstes eine Ausnahme verdient.
- **B** — Nur den **Leseweg** freigeben und den Gate-Text auf „vorhandene
  Sicherungen sehen Sie unter Einstellungen" ändern. Hilft dem, der schon
  gesichert hat, nicht dem, der es noch will.
- **C** — Dem Gate eine **eigene Handlung** geben („Jetzt sichern, dann
  umziehen"). Die ehrlichste Antwort auf die Aufforderung, die dort steht —
  und die größte Änderung.

## Verify

| # | Where | Look for | AI | Human |
|---|---|---|:--:|---|
| **1** | Entscheidung | eine der Varianten ist gewählt und begründet; die anderen sind als verworfen vermerkt | ➖ | |
| **2** | Gate mit offener Migration | der Text nennt nur Handgriffe, die von dort aus erreichbar sind | ➖ | |
| **3** | Statuscodes | die Sperre gilt weiterhin für alles, was den Bestand ändert | ➖ | |
| **4** | Regression | `make test` und Ruff grün | ➖ | |

---

## Produktentscheidung Codex · Variante C, eng geschnitten (2026-09-02)

Mike hat Codex die Entscheidung über die nächsten kleinen, nicht ausufernden
Schritte übertragen. Gewählt ist **C**: Die Sicherung wird dort ausführbar,
wo das Gate zu ihr rät. A und B sind verworfen, weil ein bloß erreichbarer
API-Weg beziehungsweise eine sichtbare Liste dem Benutzer auf dem gesperrten
Gate-Bildschirm noch keine Handlung gibt.

### Der Ablauf

1. Im Backup-Hinweis steht ein sekundärer, aus beiden Katalogen übersetzter
   Knopf **„Jetzt sichern" / „Create backup now"**.
2. Der Knopf meldet ein eigenes `backup`-Event. `MigrationGate` bleibt damit
   frei von Store, Composable und HTTP; `AppGate` verbindet das Event mit dem
   vorhandenen `useBackups()`-Composable.
3. Während die Sicherung läuft, können Sicherung und Migration nicht parallel
   gestartet werden. Ein Fehler und der Erfolg stehen lokal beim Hinweis;
   die Migration startet **nie automatisch** nach einer Sicherung.
4. Der bestehende Migrationsknopf bleibt eine getrennte, bewusste Bestätigung.
   Die Sicherung wird empfohlen, nicht zu einer neuen Pflichtbedingung gemacht.

### Die enge Gate-Ausnahme

Nur diese beiden bereits vorhandenen Routen kommen als exakte Methode/Pfad-
Paare in die Allowlist:

```
GET  /backups
POST /backups
```

`GET` ist nötig, weil `useBackups.create()` nach erfolgreichem `POST` seinen
Stand über den vorhandenen Leseweg aktualisiert. Insbesondere bleiben
`POST /backups/{name}/restore`, Instrumente, Kurse und alle übrigen
Schreibwege gesperrt. Keine Präfixregel und keine allgemeine Ausnahme für
„Backup-Routen".

### Erwartete Flächen

| Datei/Fläche | Änderung |
|---|---|
| `app/migration_guard.py` | genau die zwei Allowlist-Paare |
| vorhandene Guard-/Endpoint-Tests | erlaubte Methoden und weiterhin gesperrter Restore-/Fachweg |
| `dashboard/src/components/MigrationGate.vue` | Props für Zustand/Fehler/Erfolg, `backup`-Event und sekundärer Naive-Button |
| `dashboard/src/components/AppGate.vue` | vorhandenes `useBackups()` verdrahten; kein zweiter HTTP-Weg |
| `dashboard/src/i18n/{de,en}.ts` | Handlung, Erfolg und Fehlerkontext in beiden Sprachen |
| vorhandene Gate-Tests | Klick, gegenseitige Sperre, Erfolg/Fehler und DE/EN |

### Nicht-Ziele

- Keine Backup-Liste, Restore-Auswahl oder Einstellungsansicht im Gate.
- Kein automatisches Backup und kein automatisches Weiterlaufen zur Migration.
- Keine Änderung an Rotation, Fingerprint, Restore oder Migrationsfachlogik.
- Keine neue Komponente im UX-Fundament; der Identitätsumzug bleibt ein
  StockInfo-Fachthema.

### Pflichtorakel

1. Bei offener Migration liefern nur `GET /backups` und `POST /backups` aus
   dieser Fachgruppe Erfolg; Restore und ein anderer Schreibweg bleiben 503.
2. Entfernt man eines der zwei Allowlist-Paare oder ersetzt man die exakten
   Paare durch eine zu breite Backup-Präfixregel, wird ein Test rot.
3. Ein Klick erzeugt genau eine Sicherung und keinen Confirm-Request; während
   des Laufs sind beide Handlungen gegeneinander verriegelt.
4. Erfolg und Fehler stehen im Gate in DE und EN; kein sichtbarer Satz ist im
   Template hartkodiert.
5. Claudes Browserlauf benutzt eine isolierte Datenbank, legt über den
   sichtbaren Knopf tatsächlich eine Sicherung an und prüft die Oberfläche in
   beiden Sprachen. Die Migration muss für diese Abnahme nicht ausgeführt
   werden.

Der Umfang bleibt bei der vorhandenen Time-box von 1–2 Stunden. Falls die
Verdrahtung eine neue API, ein neues Backup-Composable oder eine neue
Zustandsmaschine verlangen würde, ist das ein Scope-Checkpoint statt ein
Nachtrag.
