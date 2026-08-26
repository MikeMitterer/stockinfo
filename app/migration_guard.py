"""Die Verriegelung während eines ausstehenden Umzugs — **eine** Zustandsquelle.

Solange die Migration nicht bestätigt ist, darf nichts am Bestand geschrieben
werden. Den Scheduler abzuschalten genügt dafür nicht: Auch gewöhnliche
Requests schreiben. `/quote` legt Instrumente an und aktualisiert sie, dazu
kommen `/refresh` und mehrere `PUT`- und `DELETE`-Routen des Dashboards. Eine
eingeschränkte Oberfläche hindert weder ein `curl` noch einen alten offenen
Browser-Tab — und dann stimmt die vorgerechnete Auswirkung bei der
Bestätigung nicht mehr.

Deshalb sperrt ein zentraler Guard im Server, und die Ausnahmen stehen an
**einer** Stelle. Einzelprüfungen in den Routern wären eine parallele
Fachregel; ein Sonderweg für die Diagnose wäre eine zweite Ausnahmequelle.
"""

import os
import threading
from collections.abc import Callable
from enum import Enum

import structlog

logger = structlog.get_logger()

# Die stabile Kennung, mit der ein gesperrter Request abgewiesen wird.
#
# Eine Kennung, kein Satz: Der Text gehört ins UI und muss in DE und EN
# vorliegen. Wer darauf reagiert, prüft diesen Wert, nicht eine Formulierung.
REASON_MIGRATION_PENDING = "migration_pending"

# Die Kennung für „umgezogen, aber der Betrieb läuft nicht an".
#
# Eigene Kennung und nicht `migration_pending`: Die beiden verlangen
# Verschiedenes. Beim einen wartet der Dienst auf eine Bestätigung, beim
# anderen ist die längst erteilt und der Start scheitert — wer sie
# zusammenwirft, schickt den Benutzer in den falschen Ablauf.
REASON_STARTUP_FAILED = "startup_failed"

# Der Pfad, den der Docker-`HEALTHCHECK` abfragt.
#
# **Eine** Konstante, drei Verbraucher: der Guard hier, der Routentabellen-Test
# und der Dockerfile. Letzterer kann kein Python importieren — deshalb prüft
# ein Test, dass die dort stehende URL genau dieser Pfad ist. Ohne ihn driften
# die beiden beim nächsten Umbenennen auseinander, unbemerkt bis zum Deployment.
HEALTHCHECK_PATH = "/operational"

# Was im Pending-Zustand trotzdem beantwortet wird — als Paare aus Methode und
# Pfad, nicht als Faustregel.
#
# „Alles ohne Datenbankzugriff" wäre die naheliegende Regel und wäre falsch:
# `/ready` fasst die Datenbank selbst an und muss trotzdem antworten dürfen,
# sonst kann niemand den Zustand abfragen.
ALLOWED_ROUTES: frozenset[tuple[str, str]] = frozenset(
    {
        ("GET", "/health"),  # Liveness, hängt an nichts
        ("GET", HEALTHCHECK_PATH),  # der Zustand, an dem der Healthcheck hängt
        ("GET", "/ready"),  # liest die DB und muss trotzdem antworten
        ("GET", "/migration"),  # die Vorschau
        ("POST", "/migration/confirm"),  # die Bestätigung
        ("GET", "/migration/report"),  # der Bericht danach
    }
)


def static_allowlist(static_dir: str) -> frozenset[str]:
    """Die statischen Pfade, die im Pending-Zustand ausgeliefert werden dürfen.

    **Abgeleitet, nicht abgeschrieben.** Eine handgepflegte Liste ist eine
    zweite Wahrheit, die driftet — und sie war es schon beim ersten Versuch:
    Der frühere Entwurf nannte `/stockinfo-icon.png`, aber nicht die `.svg`,
    die `dashboard/index.html` als FavIcon anfordert. Im Pending-Zustand hätte
    der Guard einen realen Dashboard-Request abgewiesen.

    **Rekursiv**, weil `/assets` als Verzeichnis `404` liefert, seine Dateien
    aber `200`. Ein Inventar nur der obersten Ebene gäbe die Assets nicht frei.

    **Plus `/`**, denn das ist keine Datei: `StaticFiles(html=True)` stellt die
    Startadresse als URL-Alias auf `index.html` bereit, und im Dateiinventar
    taucht sie nicht auf. Eine rein aus Dateien abgeleitete Liste hätte
    ausgerechnet die Adresse gesperrt, über die das Dashboard geöffnet wird.
    Der Alias gilt als **exakter Pfad**, nie als Präfix — das Dashboard ist
    unter `/` gemountet, und ein Präfix gäbe jede Fach-API mit frei.

    Fehlt das Verzeichnis, ist nichts gemountet und die Menge leer. Das ist
    der lokale Entwicklungsfall: Die Vorgabe zeigt auf den Container-Pfad
    `/app/web`, den es außerhalb des Images nicht gibt.

    Args:
        static_dir: Das konfigurierte Verzeichnis mit dem gebauten Dashboard.

    Returns:
        Die erlaubten Pfade, jeweils mit führendem ``/``.
    """
    root = os.path.realpath(static_dir)
    if not os.path.isdir(root):
        return frozenset()

    paths = set()
    for directory, _, filenames in os.walk(root):
        for filename in filenames:
            absolute = os.path.realpath(os.path.join(directory, filename))
            # Kein Pfadausbruch: Ein Symlink, der aus `static_dir` hinauszeigt,
            # gehört nicht zur Oberfläche und wird nicht freigegeben.
            if os.path.commonpath((root, absolute)) != root:
                continue
            paths.add("/" + os.path.relpath(absolute, root))

    if "/index.html" in paths:
        paths.add("/")
    return frozenset(paths)


class GateState(Enum):
    """Die Lagen des Riegels — **eine** Zustandsgröße, nicht drei Flags.

    Bis Runde 32 hielten `_pending`, `_running` und `_startup_failed` den
    Zustand gemeinsam, und jede Lage war ihre eigene Kombination. Genau daran
    sind die beiden Befunde aus Runde 32 gescheitert: Eine Kombination war gar
    nicht benannt (Umzug durch, Start läuft noch), und zwei Übergänge setzten
    die Flags **nacheinander** — dazwischen war eine Lage sichtbar, die es
    fachlich nicht gibt.

    Ein `Enum` kann nicht halb umgeschaltet sein. Jede Lage hat genau einen
    Wert, jeder Übergang ist genau eine Zuweisung unter derselben Sperre.
    """

    SERVING = "serving"
    """Normalbetrieb — Fachwege offen, Scheduler läuft."""

    PENDING = "pending"
    """Der Umzug wartet auf die Bestätigung; Fachwege gesperrt."""

    MIGRATING = "migrating"
    """Der Umzug läuft gerade; Fachwege **weiter** gesperrt."""

    STARTING = "starting"
    """Der Umzug ist festgeschrieben, der Betrieb läuft an."""

    STARTUP_FAILED = "startup_failed"
    """Der Umzug ist festgeschrieben, der Start ist gescheitert."""


class MigrationGate:
    """Der Zustand „Umzug steht aus" — **fünf** Lagen, eine Zustandsgröße.

    | Lage | `pending` | `/ready` | `/operational` |
    |---|---|---|---|
    | wartet auf Bestätigung | ``True`` | `503 migration_pending` | `200 migration_pending` |
    | Umzug läuft gerade | ``True`` | `503 migration_pending` | `200 migration_pending` |
    | **Betrieb läuft an** | ``False`` | `503 starting` | `200 starting` |
    | Start gescheitert | ``False`` | `503 degraded` | `503 degraded` |
    | freigegeben | ``False`` | `200 ok` | `200 serving` |

    **Die Lage „Umzug läuft" fehlte bis Runde 30**, und das war ein
    betriebsgefährdender Fehler: `confirm()` setzte den Riegel zurück und
    startete den Scheduler, *bevor* der Umzug überhaupt begann. Währenddessen
    meldete `/ready` schon `ok`, normale Requests durften auf den **alten**
    Bestand, und der Scheduler schrieb hinein.

    Deshalb sind Anspruch und Freigabe getrennt: `claim` nimmt den Umzug an
    sich, **ohne** etwas freizugeben; `release` gibt frei, und zwar erst nach
    einem erfolgreichen Commit. `abandon` gibt den Anspruch zurück, wenn der
    Umzug scheitert — der Riegel bleibt dann geschlossen, ein neuer Versuch
    ist möglich.

    **Die Lage „Betrieb läuft an" fehlte bis Runde 32**, und der Fehler hatte
    dieselbe Form eine Stufe später: `release` setzte den Riegel auf offen und
    rief *danach* den Scheduler. Zwischen beidem stand „Umzug nicht mehr
    ausstehend, Start nicht gescheitert" — also `ok` und `serving`, obwohl
    `RefreshScheduler.start()` noch gar nicht zurückgekehrt war. Bei einem
    hängenden Start blieb diese Falschaussage unbegrenzt stehen.

    **Der Wiederholungsweg war nicht verriegelt** — der zweite Befund aus
    Runde 32. `retry_release` rief den Rückruf ohne Zustandswechsel, also
    liefen acht gleichzeitige Bestätigungen in acht Scheduler-Starts.
    Anspruch und Ausführung liegen deshalb jetzt **in derselben** Methode:
    Wer den Rückruf ausführen darf, entscheidet der Übergang nach `STARTING`,
    und den gewinnt genau einer.
    """

    def __init__(self) -> None:
        self._state = GateState.SERVING
        self._lock = threading.Lock()
        self._on_release: Callable[[], None] | None = None

    @property
    def starting(self) -> bool:
        """Läuft der Betrieb gerade an?

        Die Lage zwischen festgeschriebenem Umzug und zurückgekehrtem
        `RefreshScheduler.start()`. Sie ist kurz und auf dem Papier
        unscheinbar — bis der Start hängt. Dann ist sie der einzige Zustand,
        der noch die Wahrheit sagt: Die Daten stimmen, der Dienst arbeitet
        noch nicht.

        `/ready` antwortet darauf `503`, denn der Fachbetrieb ist nicht
        freigegeben. `/operational` antwortet `200`, denn der Prozess tut
        genau das, was er tun soll — dieselbe Unterscheidung wie beim Warten
        auf die Bestätigung.
        """
        return self._state is GateState.STARTING

    @property
    def startup_failed(self) -> bool:
        """Ist der Umzug durch, der **Betrieb** aber nicht angelaufen?

        Der ehrliche vierte Zustand. Er entsteht, wenn der Umzug festgeschrieben
        ist, der Scheduler aber nicht startet: Die Daten stimmen, der Dienst
        holt trotzdem keine Kurse.

        **Ein Logeintrag genügt dafür nicht** (Codex, Runde 31). Bis dahin
        schluckte `release` den Fehler und meldete Erfolg — der Dienst stand
        auf `ready/serving`, und seine Kurse veralteten unbemerkt. Genau der
        betriebliche Fehler, den Runde 30 abstellen sollte, war damit wieder
        da, nur eine Ebene höher.

        Den Umzug deswegen als „nicht geschehen" auszugeben wäre die andere
        Lüge — er *ist* geschehen. Also sagt dieser Zustand, was gilt: Migration
        fertig, Betrieb nicht bereit.
        """
        return self._state is GateState.STARTUP_FAILED

    @property
    def pending(self) -> bool:
        """Sind die Fachwege gesperrt?

        Auch **während** der Umzug läuft. Der Bestand ist in dieser Zeit noch
        der alte, teilweise umgebaute — ihn zu bedienen wäre schlimmer als zu
        warten.
        """
        return self._state in (GateState.PENDING, GateState.MIGRATING)

    @property
    def running(self) -> bool:
        """Läuft gerade ein Umzug?"""
        return self._state is GateState.MIGRATING

    def block(self) -> None:
        """Versetzt den Dienst in den Pending-Zustand."""
        with self._lock:
            self._state = GateState.PENDING
        logger.warning("migration_pending")

    def on_release(self, callback: Callable[[], None] | None) -> None:
        """Was beim Übergang in den Normalbetrieb noch geschehen muss.

        **Der Grund ist der Scheduler.** Er läuft im Lifespan an, und der ist
        längst durch, wenn der Benutzer bestätigt. Ohne diesen Rückruf liefe
        der Hintergrund-Refresh nach einem bestätigten Umzug bis zum nächsten
        Neustart nicht — der Dienst sähe gesund aus und holte keine Kurse.

        Ein Rückruf statt eines Imports, weil die Richtung sonst falsch
        stünde: Der Bestätigungs-Endpunkt müsste `app.main` importieren, das
        ihn selbst einbindet.

        **Einmal heißt einmal gleichzeitig, nicht einmal überhaupt.** Der
        Rückruf läuft beim ersten erfolgreichen `release` und danach bei
        jedem `retry_release`, das einen gescheiterten Start wiederholt. Der
        Riegel sichert zu, dass immer nur **ein** Aufrufer darin ist; dass ein
        bereits laufender Scheduler nicht ein zweites Mal gestartet wird, ist
        Sache des Rückrufs selbst.

        Args:
            callback: Wird bei jedem Übergang in den Normalbetrieb gerufen,
                nie nebenläufig zu sich selbst; ``None`` löst die
                Registrierung.
        """
        with self._lock:
            self._on_release = callback

    def claim(self) -> bool:
        """Nimmt den Umzug an sich — **ohne** irgendetwas freizugeben.

        Genau ein Aufrufer gewinnt. Ein zweiter, gleichzeitiger bekommt
        ``False``, und zwar auch dann, wenn der erste noch mitten im Umzug
        steckt — `MIGRATING` ist eine eigene Lage und nicht die Abwesenheit
        von `PENDING`.

        Returns:
            ``True`` für den einen Aufrufer, der den Umzug ausführen darf.
        """
        with self._lock:
            if self._state is not GateState.PENDING:
                return False
            self._state = GateState.MIGRATING
            return True

    def release(self) -> bool:
        """Gibt den Betrieb frei — **nach** dem erfolgreichen Commit.

        Erst hier fallen die Fachwege auf, und erst hier läuft der Rückruf.

        **Der Rückgabewert ist neu und der Kern des Befunds aus Runde 31.**
        Vorher schluckte diese Funktion jeden Rückruffehler und meldete nichts;
        die Bestätigung antwortete `200`, `/ready` sagte `ok`, und kein
        Scheduler lief. Jetzt sagt sie, ob der Betrieb wirklich angelaufen ist
        — und wer sie ruft, muss die Antwort verwenden.

        **Die Zwischenlage ist der Befund aus Runde 32.** Vorher setzte diese
        Methode den Riegel auf offen und rief *danach* den Rückruf. Dazwischen
        war der Zustand „nicht ausstehend, nicht gescheitert" — also `ok` und
        `serving`, während `RefreshScheduler.start()` noch lief. Jetzt geht
        der Übergang nach `STARTING`, und erst der Rückruf entscheidet, ob
        daraus `SERVING` oder `STARTUP_FAILED` wird.

        Returns:
            ``True``, wenn auch der Betrieb steht; ``False``, wenn der Umzug
            zwar festgeschrieben ist, der Start aber scheiterte.
        """
        with self._lock:
            self._state = GateState.STARTING
        return self._run_release()

    def retry_release(self) -> bool | None:
        """Startet den Betrieb erneut — nach einem gescheiterten Anlauf.

        Damit ist der Fehlerzustand **anstoßbar** und nicht nur beobachtbar:
        Wer den Grund behoben hat, bestätigt einfach noch einmal. Ohne diesen
        Weg bliebe nur ein Neustart des Dienstes.

        **Anspruch und Ausführung stehen hier zusammen**, und das ist der
        zweite Befund aus Runde 32. Vorher rief diese Methode den Rückruf ohne
        jeden Zustandswechsel: Acht gleichzeitige Wiederholungen sahen alle
        `startup_failed`, liefen alle in denselben Rückruf und starteten acht
        Scheduler. Ein getrenntes `claim_retry()` hätte dieselbe Falle nur
        verschoben — wer die Ausführung von der Verriegelung trennen kann,
        vergisst sie irgendwo.

        Returns:
            ``True``, wenn der Betrieb jetzt steht; ``False``, wenn auch
            dieser Versuch scheiterte; ``None``, wenn es nichts zu wiederholen
            gibt — der Start ist nicht gescheitert, oder ein anderer Aufrufer
            versucht es gerade.
        """
        with self._lock:
            if self._state is not GateState.STARTUP_FAILED:
                return None
            self._state = GateState.STARTING
        return self._run_release()

    def _run_release(self) -> bool:
        """Führt den Rückruf aus und schaltet danach in die Ziel-Lage.

        Aufgerufen wird sie ausschließlich aus `release` und `retry_release`,
        und beide betreten sie nur über den Übergang nach `STARTING`. Genau
        das ist die Einmal-Verriegelung: Solange hier jemand arbeitet, findet
        kein zweiter Aufrufer eine Lage vor, aus der er sie betreten dürfte.

        Der Rückruf läuft **ohne** die Sperre. Er startet den Scheduler und
        darf beliebig lange brauchen; die Sperre so lange zu halten hieße,
        dass `pending` und `starting` in dieser Zeit nicht mehr beantwortbar
        wären — und das sind genau die Fragen, die dann gestellt werden.

        Returns:
            ``True``, wenn der Betrieb steht.
        """
        with self._lock:
            callback = self._on_release

        if callback is not None:
            try:
                callback()
            except Exception:
                with self._lock:
                    self._state = GateState.STARTUP_FAILED
                logger.exception("migration_release_callback_failed")
                return False

        with self._lock:
            self._state = GateState.SERVING
        return True

    def abandon(self) -> None:
        """Gibt den Anspruch zurück — der Umzug ist gescheitert.

        Der Riegel bleibt geschlossen; ein neuer Versuch ist möglich. Ohne
        diesen Weg bliebe der Umzug für immer „läuft gerade", und niemand
        käme mehr an ihn heran.
        """
        with self._lock:
            if self._state is GateState.MIGRATING:
                self._state = GateState.PENDING
        logger.warning("migration_abandoned")


def is_allowed(
    method: str, path: str, static_paths: frozenset[str]
) -> bool:
    """Darf dieser Request im Pending-Zustand durch?

    Args:
        method: Die HTTP-Methode.
        path: Der angefragte Pfad.
        static_paths: Das Ergebnis von `static_allowlist`.

    Returns:
        ``True``, wenn der Request beantwortet werden darf.
    """
    if (method.upper(), path) in ALLOWED_ROUTES:
        return True
    return method.upper() == "GET" and path in static_paths
