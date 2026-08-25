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

import structlog

logger = structlog.get_logger()

# Die stabile Kennung, mit der ein gesperrter Request abgewiesen wird.
#
# Eine Kennung, kein Satz: Der Text gehört ins UI und muss in DE und EN
# vorliegen. Wer darauf reagiert, prüft diesen Wert, nicht eine Formulierung.
REASON_MIGRATION_PENDING = "migration_pending"

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
    """Der Zustand „Umzug steht aus" — und seine **einmalige** Freigabe.

    Ein einfaches Flag hätte zwei Löcher: Zwei gleichzeitige Bestätigungen
    liefen beide durch, und eine wiederholte gäbe den Betrieb ein zweites Mal
    frei. `confirm` liefert deshalb genau **einem** Aufrufer ``True`` —
    derjenige führt die Migration aus und startet den Scheduler; alle anderen
    bekommen ``False`` und wissen, dass sie nichts zu tun haben.
    """

    def __init__(self) -> None:
        self._pending = False
        self._lock = threading.Lock()

    @property
    def pending(self) -> bool:
        """Steht der Umzug noch aus?"""
        return self._pending

    def block(self) -> None:
        """Versetzt den Dienst in den Pending-Zustand."""
        with self._lock:
            self._pending = True
        logger.warning("migration_pending")

    def confirm(self) -> bool:
        """Gibt den Betrieb frei — **genau einmal**.

        Returns:
            ``True`` für den einen Aufrufer, der die Freigabe gewonnen hat;
            ``False`` für jeden weiteren und für den Fall, dass gar nichts
            ausstand.
        """
        with self._lock:
            if not self._pending:
                return False
            self._pending = False
            return True


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
