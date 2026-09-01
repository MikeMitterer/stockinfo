# T-51 · Das Migrationsgate sperrt die Sicherung aus, zu der es rät

| Repo | Status | Time-box | Scope | GH-Issue |
|---|---|---|---|---|
| StockInfo (Backend + Dashboard) | offen | 1–2 h | entscheiden, ob Sicherungen vor dem Migrationsgate erreichbar sind — und den Gate-Text nachziehen | — |

- **Angelegt:** 2026-09-01, aus dem T-50-Browserlauf (dort V-1)
- **Hängt ab von:** nichts. T-47 ist freigegeben
- **Reihenfolge:** offen, **nicht** in der `priority_chain`

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
