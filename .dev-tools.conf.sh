#!/usr/bin/env bash
# Entwicklungswerkzeuge, die dieses Projekt über pipx braucht, im Format von devtools
# (README, Abschnitt Config file): je Werkzeug NAME_PACKAGE, NAME_TAG, NAME_SOURCE und
# optional NAME_LABEL. Das Makefile bindet die Datei mit include ein; Bash kann sie sourcen.
# Deshalb NAME=wert ohne Anführungszeichen und ohne Leerzeichen um das =.
# shellcheck disable=SC2034  # vom Makefile gelesen

# make setup installiert die Werkzeuge mit devtools --project install nach .tools/ dieses
# Checkouts; make info zeigt ihren Stand. Der SemVer-Teil eines Tags ist die Mindestversion.
# SOURCE nennt immer die GitHub-Quelle; auf dem Entwicklungsrechner setzt die rechnerlokale
# Zuordnung von DevTools die lokalen Repos dafür ein, auch mit ungepushtem Tag.

# DevTools selbst: Das Makefile ruft das einmal je Rechner installierte devtools auf (Starter);
# ist es älter als DEVTOOLS_TAG, gibt es an diesen Tag aus DEVTOOLS_SOURCE weiter.
DEVTOOLS_TAG=v0.7.0+261119.1249.b3946
DEVTOOLS_SOURCE=git+https://github.com/MikeMitterer/python-devtools.git

# ProjectTools (docs-check, repo-status, changelog, repo-info, dev-ports).
PROJECTTOOLS_PACKAGE=mmit-projecttools
PROJECTTOOLS_LABEL=ProjectTools
PROJECTTOOLS_TAG=v0.12.0+261121.2308.3755c
PROJECTTOOLS_SOURCE=git+https://github.com/MikeMitterer/bash-ProjectTools.git

# BashLib (Daten, keine Ausgabe: readProjectVersion für den Kopf von make help, Releases
# über tag-*; Docker-Build und -Push in docker/build.sh; Palette und logFileStatus in
# scripts/sources-profile.sh). Ab v0.20 setzt BashLib CLITheme voraus.
BASHLIB_PACKAGE=mmit-bashlib
BASHLIB_LABEL=BashLib
BASHLIB_TAG=v0.21.0+261128.1332.05ce66
BASHLIB_SOURCE=git+https://github.com/MikeMitterer/bash-lib.git

# CLITheme (Ausgabe: cli.lib.sh und make.lib.sh über clilib-path für help, info, hints,
# Statuszeilen und die Hilfe der Skripte; clitheme export für Farben und Abstände).
CLITHEME_PACKAGE=mmit-clitheme
CLITHEME_LABEL=CLITheme
CLITHEME_TAG=v0.14.0+261127.2030.9d8f4
CLITHEME_SOURCE=git+https://github.com/MikeMitterer/python-clitheme.git
