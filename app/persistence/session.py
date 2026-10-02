"""SQLModel-Sessions auf die SQLite-Datei — eine Engine je Datenbankpfad.

**Kein Verbindungspool.** Jede Session öffnet eine eigene Verbindung und
schließt sie wieder, genau wie vorher jeder Repository-Aufruf. Ein Pool hielte
Verbindungen offen, während beim Start eine Sicherung die Datei ersetzt, und
die Tests legen je Test eine neue Datei an.

**Echte Transaktionen.** pysqlite beginnt unter Python 3.11 eine Transaktion
erst beim ersten Schreibbefehl und kennt keine verlässlichen SAVEPOINTs. Das
SQLAlchemy-Rezept für den SQLite-Dialekt schaltet das Eigenverhalten ab und
setzt `BEGIN` selbst; erst damit trägt `begin_nested()` beim abgefangenen
UNIQUE-Rennen.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from functools import lru_cache
from pathlib import Path

from sqlalchemy import Engine, event
from sqlalchemy.pool import NullPool
from sqlmodel import Session, create_engine

from app.persistence.db import configure_connection


@lru_cache
def _engine(database_path: str) -> Engine:
    """Die Engine für eine Datenbankdatei, einmal je Pfad gebaut."""
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{database_path}",
        poolclass=NullPool,
        connect_args={"timeout": 10.0, "check_same_thread": False},
    )

    @event.listens_for(engine, "connect")
    def _on_connect(dbapi_connection, connection_record) -> None:  # noqa: ANN001
        dbapi_connection.isolation_level = None
        configure_connection(dbapi_connection)

    @event.listens_for(engine, "begin")
    def _on_begin(connection) -> None:  # noqa: ANN001
        connection.exec_driver_sql("BEGIN")

    return engine


@contextmanager
def open_session(database_path: str) -> Iterator[Session]:
    """Eine Session, die bei Erfolg committet und bei einem Fehler zurückrollt.

    Args:
        database_path: Pfad zur SQLite-Datei.
    """
    with Session(_engine(str(database_path))) as session:
        try:
            yield session
            session.commit()
        except BaseException:
            session.rollback()
            raise
