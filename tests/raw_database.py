"""Rohe SQLite-Verbindung für Testaufbau und Nachsehen.

Manche Tests legen Zustände an, die die App selbst nie schreibt — ein
Instrument ohne Währung, zwei Listings mit demselben Symbol — oder sehen
direkt in eine Tabelle. Bis T-91 holten sie sich dafür die rohe Verbindung
des Repositorys; seit es über SQLModel-Sessions arbeitet, öffnet dieser
Helfer dieselbe temporäre Datei.
"""

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager

from app.persistence.db import get_connection
from app.persistence.repository import QuoteRepository


@contextmanager
def raw_database(repository: QuoteRepository) -> Iterator[sqlite3.Connection]:
    """Eine Verbindung auf die Datei des Repositorys; committet bei Erfolg."""
    connection = get_connection(repository._database_path)
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()
