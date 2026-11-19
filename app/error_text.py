"""Eine Ausnahme als kurzer Text für Logs und Diagnosen."""


def error_text(error: BaseException) -> str:
    """``Typ: Meldung`` einer Ausnahme, etwa ``ValueError: kein Kurs``.

    Der Typ steht mit dabei, weil viele Meldungen allein nichts sagen (ein
    ``KeyError`` meldet nur den Schlüssel). Logs, `/sources` und die Absichts-
    datei einer Wiederherstellung nutzen dieselbe Form.

    Args:
        error: Die abgefangene Ausnahme.
    """
    return f"{type(error).__name__}: {error}"
