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


class MigrationGate:
    """Der Zustand „Umzug steht aus" — mit **drei** Lagen, nicht zwei.

    | Lage | `pending` | was gilt |
    |---|---|---|
    | wartet auf Bestätigung | ``True`` | Fachwege gesperrt |
    | **Umzug läuft gerade** | ``True`` | Fachwege **weiter** gesperrt |
    | freigegeben | ``False`` | Normalbetrieb |

    **Die mittlere Lage fehlte bis Runde 30**, und das war ein
    betriebsgefährdender Fehler: `confirm()` setzte den Riegel zurück und
    startete den Scheduler, *bevor* der Umzug überhaupt begann. Währenddessen
    meldete `/ready` schon `ok`, normale Requests durften auf den **alten**
    Bestand, und der Scheduler schrieb hinein. Scheiterte der Umzug danach,
    lief der bereits gestartete Scheduler weiter; scheiterte der Rückruf,
    blieb der Riegel sogar dauerhaft offen.

    Deshalb sind Anspruch und Freigabe getrennt: `claim` nimmt den Umzug an
    sich, **ohne** etwas freizugeben; `release` gibt frei, und zwar erst nach
    einem erfolgreichen Commit. `abandon` gibt den Anspruch zurück, wenn der
    Umzug scheitert — der Riegel bleibt dann geschlossen, ein neuer Versuch
    ist möglich.
    """

    def __init__(self) -> None:
        self._pending = False
        self._running = False
        self._startup_failed = False
        self._lock = threading.Lock()
        self._on_release: Callable[[], None] | None = None

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
        return self._startup_failed

    @property
    def pending(self) -> bool:
        """Sind die Fachwege gesperrt?

        Auch **während** der Umzug läuft. Der Bestand ist in dieser Zeit noch
        der alte, teilweise umgebaute — ihn zu bedienen wäre schlimmer als zu
        warten.
        """
        return self._pending

    @property
    def running(self) -> bool:
        """Läuft gerade ein Umzug?"""
        return self._running

    def block(self) -> None:
        """Versetzt den Dienst in den Pending-Zustand."""
        with self._lock:
            self._pending = True
            self._running = False
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

        Args:
            callback: Wird beim erfolgreichen `confirm` **einmal** gerufen;
                ``None`` löst die Registrierung.
        """
        with self._lock:
            self._on_release = callback

    def claim(self) -> bool:
        """Nimmt den Umzug an sich — **ohne** irgendetwas freizugeben.

        Genau ein Aufrufer gewinnt. Ein zweiter, gleichzeitiger bekommt
        ``False``, und zwar auch dann, wenn der erste noch mitten im Umzug
        steckt: `running` ist der Grund, warum ein einfaches Flag hier nicht
        genügt.

        Returns:
            ``True`` für den einen Aufrufer, der den Umzug ausführen darf.
        """
        with self._lock:
            if not self._pending or self._running:
                return False
            self._running = True
            return True

    def release(self) -> bool:
        """Gibt den Betrieb frei — **nach** dem erfolgreichen Commit.

        Erst hier fallen die Fachwege auf, und erst hier läuft der Rückruf.

        **Der Rückgabewert ist neu und der Kern des Befunds aus Runde 31.**
        Vorher schluckte diese Funktion jeden Rückruffehler und meldete nichts;
        die Bestätigung antwortete `200`, `/ready` sagte `ok`, und kein
        Scheduler lief. Jetzt sagt sie, ob der Betrieb wirklich angelaufen ist
        — und wer sie ruft, muss die Antwort verwenden.

        Returns:
            ``True``, wenn auch der Betrieb steht; ``False``, wenn der Umzug
            zwar festgeschrieben ist, der Start aber scheiterte.
        """
        with self._lock:
            self._pending = False
            self._running = False
        return self._run_release()

    def retry_release(self) -> bool:
        """Startet den Betrieb erneut — nach einem gescheiterten Anlauf.

        Damit ist der Fehlerzustand **anstoßbar** und nicht nur beobachtbar:
        Wer den Grund behoben hat, bestätigt einfach noch einmal. Ohne diesen
        Weg bliebe nur ein Neustart des Dienstes.

        Returns:
            ``True``, wenn der Betrieb jetzt steht.
        """
        return self._run_release()

    def _run_release(self) -> bool:
        """Führt den Rückruf aus und merkt sich, ob er getragen hat."""
        with self._lock:
            callback = self._on_release

        if callback is None:
            with self._lock:
                self._startup_failed = False
            return True

        try:
            callback()
        except Exception:
            with self._lock:
                self._startup_failed = True
            logger.exception("migration_release_callback_failed")
            return False

        with self._lock:
            self._startup_failed = False
        return True

    def abandon(self) -> None:
        """Gibt den Anspruch zurück — der Umzug ist gescheitert.

        Der Riegel bleibt geschlossen; ein neuer Versuch ist möglich. Ohne
        diesen Weg bliebe der Umzug für immer „läuft gerade", und niemand
        käme mehr an ihn heran.
        """
        with self._lock:
            self._running = False
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
