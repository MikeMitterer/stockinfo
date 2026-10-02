"""Einträge in `meta` lesen und schreiben — für Laufzeitwege mit Session.

`meta` hält, was die Datenbank über sich selbst weiß: Generationskennung,
Profilschema samt Version, Übernahmemarken. Schema, Backup und
Plugin-Migration schreiben `meta` weiterhin mit eigener roher Verbindung;
siehe dort.
"""

from sqlalchemy import select
from sqlalchemy.dialects.sqlite import insert
from sqlmodel import Session, col

from app.persistence.tables import MetaRecord


def get_meta(session: Session, key: str) -> str | None:
    """Der Wert zu `key`, oder ``None``, wenn es keinen gibt."""
    return session.scalar(select(col(MetaRecord.value)).where(col(MetaRecord.key) == key))


def put_meta(session: Session, key: str, value: str) -> None:
    """Schreibt `value` unter `key`; ein vorhandener Wert wird ersetzt."""
    statement = insert(MetaRecord).values(key=key, value=value)
    session.execute(statement.on_conflict_do_update(
        index_elements=["key"], set_={"value": statement.excluded.value}
    ))


def put_meta_if_missing(session: Session, key: str, value: str) -> None:
    """Schreibt `value` unter `key` — nur, wenn dort noch keiner steht."""
    session.execute(
        insert(MetaRecord).values(key=key, value=value).on_conflict_do_nothing(index_elements=["key"])
    )
