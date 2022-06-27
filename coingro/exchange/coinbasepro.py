""" CoinbasePro exchange subclass """
import logging
from typing import Dict

from coingro.exchange import Exchange


logger = logging.getLogger(__name__)


class Coinbasepro(Exchange):
    """
    CoinbasePro exchange class. Contains adjustments needed for Coingro to work
    with this exchange.

    Please note that this exchange is not included in the list of exchanges
    officially supported by the Coingro development team. So some features
    may still not work as expected.
    """

    _cg_has: Dict = {
        "ohlcv_candle_limit": 300,
    }
