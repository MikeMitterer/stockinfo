"""Eigene /docs-Route — Swagger-UI mit festem Dark-Styling.

Die FastAPI-Default-Routen (/docs, /redoc) sind deaktiviert; diese Route
liefert das Standard-Swagger-UI-Bundle mit einem eingebetteten Dark-Theme.
Der Invert-Filter-Ansatz ist bewusst gewählt: wenige Zeilen CSS, robust
gegenüber Swagger-UI-Versionswechseln (kein Klassen-für-Klassen-Styling).
"""

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html
from fastapi.responses import HTMLResponse

_DARK_CSS = """
body { background-color: #0f1115; }
.swagger-ui { filter: invert(88%) hue-rotate(180deg); }
/* Code-Blöcke und Bilder zurückinvertieren — sie sind bereits dunkel/farbecht. */
.swagger-ui .microlight,
.swagger-ui img { filter: invert(100%) hue-rotate(180deg); }
"""


def register_docs(app: FastAPI) -> None:
    """Registriert die dunkle /docs-Route an der übergebenen App.

    Args:
        app: Die FastAPI-Instanz (mit ``docs_url=None`` erzeugt).
    """

    @app.get("/docs", include_in_schema=False)
    async def swagger_docs() -> HTMLResponse:
        base = get_swagger_ui_html(
            openapi_url=app.openapi_url or "/openapi.json",
            title=f"{app.title} — Docs",
        )
        html = base.body.decode("utf-8")
        dark = html.replace("</head>", f"<style>{_DARK_CSS}</style></head>")
        if dark == html:
            # Template-Änderung in FastAPI — lieber helle Docs als gar keine.
            return base
        return HTMLResponse(dark)
