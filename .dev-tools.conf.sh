#!/usr/bin/env bash
# Versionen der Entwicklungswerkzeuge, die dieses Projekt über pipx braucht.
# Das Makefile bindet die Datei mit include ein; Bash kann sie sourcen.
# Deshalb NAME=wert ohne Anführungszeichen und ohne Leerzeichen um das =.
# shellcheck disable=SC2034  # vom Makefile gelesen

# Gelesen von devtools (Paket mmit-devtools, Projekt DevTools). Je Werkzeug: PACKAGE ist das
# pipx-Paket, TAG der Release-Tag, seine SemVer-Zahl die Mindestversion. SOURCE ist die Quelle
# für make install-tools: die Git-URL (dann gilt der Tag) oder der Pfad einer Arbeitskopie.
# EDITABLE=yes bindet eine Arbeitskopie bearbeitbar ein (pipx install -e), no als festen Stand.
# make install-tools bringt die Werkzeuge auf diesen Stand; make setup zeigt ihn.

# DevTools selbst (devtools status|install|check), aufgerufen mit pipx run. Ohne
# DEVTOOLS_PACKAGE installiert devtools sich nicht selbst; SOURCE dient devtools upgrade.
DEVTOOLS_TAG=v0.2.0+261101.1319.09840
DEVTOOLS_SOURCE=git+https://github.com/MikeMitterer/python-devtools.git

# ProjectTools (docs-check, repo-status, changelog, repo-info), aus der lokalen Arbeitskopie.
PROJECTTOOLS_PACKAGE=mmit-projecttools
PROJECTTOOLS_LABEL=ProjectTools
PROJECTTOOLS_TAG=v0.11.0+261118.1922.975db
PROJECTTOOLS_SOURCE=/Volumes/DevLocal/DevBash/Production/ProjectTools
PROJECTTOOLS_EDITABLE=yes

# BashLib (version, tag-*, docker/build.sh, scripts/; make.lib.sh für help, info und hints),
# aus der lokalen Arbeitskopie.
BASHLIB_PACKAGE=mmit-bashlib
BASHLIB_LABEL=BashLib
BASHLIB_TAG=v0.14.0+261119.1230.2ace6
BASHLIB_SOURCE=/Volumes/DevLocal/DevBash/Production/BashLib
BASHLIB_EDITABLE=yes

# CLITheme (clitheme export: Farben und Abstände für help, info und hints über make.lib.sh),
# aus der lokalen Arbeitskopie. Ohne clitheme bleibt die Ausgabe ohne Farben.
CLITHEME_PACKAGE=mmit-clitheme
CLITHEME_LABEL=CLITheme
CLITHEME_TAG=v0.12.0+261119.1304.0816b
CLITHEME_SOURCE=/Volumes/DevLocal/DevPython/Production/CLITheme
CLITHEME_EDITABLE=yes
