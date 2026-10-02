"""SQLModel-Sessions auf die SQLite-Datei — eine Engine je Datenbankpfad.

**Kein Verbindungspool.** Jede Session öffnet eine eigene Verbindung und
schließt sie wieder, genau wie vorher jeder Repository-Aufruf. Ein Pool hielte
Verbindungen offen, während beim Start eine Sicherung die Datei ersetzt, und
die Tests legen je Test eine neue Datei an.

**Transaktionen setzt die Engine selbst.** pysqlite beginnt unter Python 3.11
eine Transaktion erst beim ersten Schreibbefehl und lässt keine Wahl der Art.
Das SQLAlchemy-Rezept für den SQLite-Dialekt schaltet das Eigenverhalten ab
und setzt `BEGIN` selbst — erst damit kann ein Schreiber `BEGIN IMMEDIATE`
verlangen (`immediate=True`), und Lesen und Schreiben einer Session liegen in
derselben Transaktion.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from sqlalchemy import URL, Engine, Executable, event
from sqlalchemy.pool import NullPool
from sqlmodel import Session, create_engine

from app.persistence.db import configure_connection


@lru_cache
def _engine(database_path: str) -> Engine:
    """Die Engine für eine Datenbankdatei, einmal je Pfad gebaut."""
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    # **Der Pfad als Feld, nicht im URL-Text.** In `sqlite:///{pfad}` läse
    # SQLAlchemy ein `?` im Dateinamen als Beginn der Optionen und öffnete eine
    # andere Datei als `sqlite3` in `init_db`.
    engine = create_engine(
        URL.create("sqlite", database=database_path),
        poolclass=NullPool,
        connect_args={"timeout": 10.0, "check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection, connection_record) -> None:  # noqa: ANN001
        dbapi_connection.isolation_level = None
        configure_connection(dbapi_connection)

    @event.listens_for(engine, "begin")
    def _on_begin(connection) -> None:  # noqa: ANN001
        immediate = connection.get_execution_options().get(_IMMEDIATE, False)
        connection.exec_driver_sql("BEGIN IMMEDIATE" if immediate else "BEGIN")

    return engine


_IMMEDIATE = "stockinfo_begin_immediate"


@contextmanager
def open_session(database_path: str, *, immediate: bool = False) -> Iterator[Session]:
    """Eine Session, die bei Erfolg committet und bei einem Fehler zurückrollt.

    Args:
        database_path: Pfad zur SQLite-Datei.
        immediate: Die Schreibsperre gleich zu Beginn nehmen (`BEGIN
            IMMEDIATE`). Für Lesen-Vergleichen-Schreiben, bei dem sich zwei
            Prozesse sonst denselben alten Stand ansehen.
    """
    with Session(_engine(str(database_path))) as session:
        if immediate:
            session.connection(execution_options={_IMMEDIATE: True})
        try:
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise


def fetch_all(session: Session, statement: Executable) -> list[dict]:
    """Führt eine Abfrage aus und gibt die Zeilen als `dict` zurück.

    **Spalten, keine Modellobjekte.** Geschrieben wird per Upsert direkt in die
    Datenbank; ein ORM-Objekt aus derselben Session wüsste davon nichts und
    zeigte den alten Stand. Und nach außen gehen ohnehin nur `dict`s.
    """
    return [dict(row) for row in session.execute(statement).mappings()]


def fetch_one(session: Session, statement: Executable) -> dict | None:
    """Wie `fetch_all`, für höchstens eine Zeile."""
    row = session.execute(statement).mappings().first()
    return dict(row) if row else None
