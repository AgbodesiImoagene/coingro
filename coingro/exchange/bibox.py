""" Bibox exchange subclass """
import logging
from typing import Dict

from coingro.exchange import Exchange

logger = logging.getLogger(__name__)


class Bibox(Exchange):
    """
    Bibox exchange class. Contains adjustments needed for Coingro to work
    with this exchange.

    Please note that this exchange is not included in the list of exchanges
    officially supported by the Coingro development team. So some features
    may still not work as expected.
    """

    # fetchCurrencies API point requires authentication for Bibox,
    # so switch it off for Coingro load_markets()
    @property
    def _ccxt_config(self) -> Dict:
        # Parameters to add directly to ccxt sync/async initialization.
        config = {"has": {"fetchCurrencies": False}}
        config.update(super()._ccxt_config)
        return config
