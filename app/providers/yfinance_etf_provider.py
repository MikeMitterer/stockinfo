"""ETF-Metadaten aus yfinance — für Papiere, die justETF nicht führt.

justETF ist eine Datenbank europäischer UCITS-Fonds. Wer die App aus den USA
oder Kanada benutzt, hat dort für keinen einzigen seiner ETFs einen Treffer, und
Anbieter, Kostenquote und Domizil blieben dauerhaft leer. Yahoo kennt diese
Papiere — allerdings längst nicht so sauber, weshalb hier bewusst nur ein
einziges Feld übernommen wird.
"""

from typing import Any

import structlog
import yfinance as yf

from app.providers.base import EtfDetails
from app.providers.justetf_provider import is_european_isin, is_european_listing

logger = structlog.get_logger()


class YFinanceEtfEnricher:
    """Liefert ETF-Zusatzdaten für nicht-europäische Papiere über Yahoo.

    **Übernommen wird nur der Anbieter.** Das ist keine Bequemlichkeit, sondern
    das Ergebnis einer Messung:

    * ``ter`` — Yahoo nennt die Kostenquote in zwei Feldern und zwei Einheiten:
      ``info['netExpenseRatio']`` gab für VTI ``0.03`` (Prozent), die Zeile
      „Annual Report Expense Ratio" aus ``funds_data`` ``0.0003`` (Anteil).
      Für XIC.TO stand dort ``0.0000``, obwohl der Fonds real rund 0,06 %
      kostet — ein stiller Nullwert, kein fehlender.
    * ``fund_size`` — ``info['totalAssets']`` steht in Landeswährung und
      absolut (VTI: 2,29 Bio USD), ``funds_data`` nannte für dasselbe Papier
      304.590,94. Das Modell erwartet Mio. **EUR** (`QuoteResponse.fund_size`).
    * ``fund_currency`` — Yahoo liefert die Handels-, nicht die Fondswährung.
      Zwei Begriffe, zwei Felder.
    * ``replication``, ``fund_domicile``, ``accumulating`` — kennt Yahoo nicht.

    Ein falscher Wert wäre hier schlimmer als gar keiner: `apply_overrides`
    füllt nur **Lücken**, ein gelieferter Wert verdeckt also einen von Hand
    nachgetragenen. Was Yahoo nicht verlässlich weiß, bleibt deshalb offen —
    dann trägt der Mensch es ein und behält es.
    """

    def is_responsible(
        self,
        isin: str | None,
        *,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> bool:
        """Ist diese Quelle für das Papier zuständig?

        Genau das Gegenstück zu `JustEtfProvider.is_responsible`: Wo justETF
        führt, hält sich Yahoo heraus. Zwei Quellen für dasselbe Feld wären eine
        zu viel, und die europäischen Daten sind bei justETF vollständiger.

        Ohne ISIN entscheiden Börse und Währung — mit einer Ausnahme vom
        einfachen Gegenteil: Weiß **niemand** etwas, ist auch diese Quelle
        nicht zuständig. Sonst spräche ein fehlender Hinweis für „nicht
        europäisch", und ein europäischer ETF ohne ISIN verlöre seine
        gepflegten Kennzahlen an eine Yahoo-Antwort, die sie nicht kennt.

        Args:
            isin: ISIN des Wertpapiers, sofern bekannt.
            exchange: Anzeigename des Handelsplatzes.
            currency: Handelswährung des Kurses.

        Returns:
            ``True`` bei außereuropäischem Domizil.
        """
        if isin:
            return not is_european_isin(isin)
        if not exchange and not currency:
            return False
        return not is_european_listing(exchange=exchange, currency=currency)

    def fetch_etf(
        self,
        isin: str | None,
        symbol: str | None = None,
        *,
        exchange: str | None = None,
        currency: str | None = None,
    ) -> EtfDetails | None:
        """Holt den Fondsanbieter zu einem Papier.

        Args:
            isin: ISIN des ETFs — hier nur fürs Protokoll, Yahoo kennt keine.
            symbol: Yahoo-Symbol. Ohne das ist nichts abzufragen.

        Returns:
            `EtfDetails` mit dem Anbieter, oder ``None``, wenn Yahoo nicht
            erreichbar war. Ein leeres Feld bei erreichbarer Quelle ist
            **kein** ``None``: „abgefragt, nichts gefunden" ist eine Aussage,
            „nicht erreichbar" ist keine — nur der Unterschied entscheidet, ob
            der gespeicherte Stand überschrieben werden darf.
        """
        if not symbol:
            logger.debug("yfinance_etf_ohne_symbol", isin=isin)
            return None

        try:
            info: Any = yf.Ticker(symbol).info
        except Exception as exc:
            logger.warning("yfinance_etf_failed", isin=isin, symbol=symbol, error=str(exc))
            return None

        return EtfDetails(provider=(info or {}).get("fundFamily"), source="yfinance")
