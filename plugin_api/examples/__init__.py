"""Beispiel-Plugins zum Plugin-Vertrag.

Sie sind **nicht** Teil des Vertrags, sondern seine Nutzer: Ein Vertrag, den
niemand erfüllt, ist eine Behauptung. Deshalb werden sie mitinstalliert — unter
dem Namen `stockinfo_plugin_examples`, damit ein so allgemeines Wort wie
`examples` nicht im Suchpfad jedes Projekts landet, das dieses Paket benutzt.

`yaml_file` ist zusätzlich als Entry-Point der Gruppe `stockinfo.sources`
angemeldet. Damit gibt es einen **echten** installierten Ladeweg, den die App
findet, ohne dass jemand eine Datei ins Volume legt.
"""
