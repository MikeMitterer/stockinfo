"""Handelsplätze der mitgelieferten Online-Anbindungen.

Die Liste beschreibt deren bekannte Symbol-/MIC-Anbindung. Neue Handelsplätze
fremder Plugins erweitern diese Zusage nicht automatisch. Gattung, Fondsdomizil
und vorhandene Anbieter-Daten begrenzen weiterhin den einzelnen Treffer.
"""

from app.exchanges import CORE_MICS

# Die mitgelieferten Anbindungen kennen genau die Handelsplätze des Core; bis
# T-140 stand hier eine Kopie derselben 38 MICs.
ONLINE_MICS = CORE_MICS
