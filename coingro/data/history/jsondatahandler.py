import logging
import re
from pathlib import Path
from typing import List, Optional

import numpy as np
from pandas import DataFrame, read_json, to_datetime

from coingro import misc
from coingro.configuration import TimeRange
from coingro.constants import DEFAULT_DATAFRAME_COLUMNS, ListPairsWithTimeframes, TradeList
from coingro.data.converter import trades_dict_to_list
from coingro.enums import CandleType, TradingMode

from .idatahandler import IDataHandler

logger = logging.getLogger(__name__)


class JsonDataHandler(IDataHandler):

    _use_zip = False
    _columns = DEFAULT_DATAFRAME_COLUMNS

    @classmethod
    def ohlcv_get_available_data(
        cls, datadir: Path, trading_mode: TradingMode
    ) -> ListPairsWithTimeframes:
        """
        Returns a list of all pairs with ohlcv data available in this datadir
        :param datadir: Directory to search for ohlcv files
        :param trading_mode: trading-mode to be used
        :return: List of Tuples of (pair, timeframe)
        """
        if trading_mode == "futures":
            datadir = datadir.joinpath("futures")
        _tmp = [
            re.search(cls._OHLCV_REGEX, p.name)
            for p in datadir.glob(f"*.{cls._get_file_extension()}")
        ]
        return [
            (
                cls.rebuild_pair_from_filename(match[1]),
                cls.rebuild_timeframe_from_filename(match[2]),
                CandleType.from_string(match[3]),
            )
            for match in _tmp
            if match and len(match.groups()) > 1
        ]

    @classmethod
    def ohlcv_get_pairs(cls, datadir: Path, timeframe: str, candle_type: CandleType) -> List[str]:
        """
        Returns a list of all pairs with ohlcv data available in this datadir
        for the specified timeframe
        :param datadir: Directory to search for ohlcv files
        :param timeframe: Timeframe to search pairs for
        :param candle_type: Any of the enum CandleType (must match trading mode!)
        :return: List of Pairs
        """
        candle = ""
        if candle_type != CandleType.SPOT:
            datadir = datadir.joinpath("futures")
            candle = f"-{candle_type}"

        _tmp = [
            re.search(r"^(\S+)(?=\-" + timeframe + candle + ".json)", p.name)
            for p in datadir.glob(f"*{timeframe}{candle}.{cls._get_file_extension()}")
        ]
        # Check if regex found something and only return these results
        return [cls.rebuild_pair_from_filename(match[0]) for match in _tmp if match]

    def ohlcv_store(
        self, pair: str, timeframe: str, data: DataFrame, candle_type: CandleType
    ) -> None:
        """
        Store data in json format "values".
            format looks as follows:
            [[<date>,<open>,<high>,<low>,<close>]]
        :param pair: Pair - used to generate filename
        :param timeframe: Timeframe - used to generate filename
        :param data: Dataframe containing OHLCV data
        :param candle_type: Any of the enum CandleType (must match trading mode!)
        :return: None
        """
        filename = self._pair_data_filename(self._datadir, pair, timeframe, candle_type)
        self.create_dir_if_needed(filename)
        _data = data.copy()
        # Convert date to int
        _data["date"] = _data["date"].view(np.int64) // 1000 // 1000

        # Reset index, select only appropriate columns and save as json
        _data.reset_index(drop=True).loc[:, self._columns].to_json(
            filename, orient="values", compression="gzip" if self._use_zip else None
        )

    def _ohlcv_load(
        self, pair: str, timeframe: str, timerange: Optional[TimeRange], candle_type: CandleType
    ) -> DataFrame:
        """
        Internal method used to load data for one pair from disk.
        Implements the loading and conversion to a Pandas dataframe.
        Timerange trimming and dataframe validation happens outside of this method.
        :param pair: Pair to load data
        :param timeframe: Timeframe (e.g. "5m")
        :param timerange: Limit data to be loaded to this timerange.
                        Optionally implemented by subclasses to avoid loading
                        all data where possible.
        :param candle_type: Any of the enum CandleType (must match trading mode!)
        :return: DataFrame with ohlcv data, or empty DataFrame
        """
        filename = self._pair_data_filename(self._datadir, pair, timeframe, candle_type=candle_type)
        if not filename.exists():
            # Fallback mode for 1M files
            filename = self._pair_data_filename(
                self._datadir, pair, timeframe, candle_type=candle_type, no_timeframe_modify=True
            )
            if not filename.exists():
                return DataFrame(columns=self._columns)
        try:
            pairdata = read_json(filename, orient="values")
            pairdata.columns = self._columns
        except ValueError:
            logger.error(f"Could not load data for {pair}.")
            return DataFrame(columns=self._columns)
        pairdata = pairdata.astype(
            dtype={
                "open": "float",
                "high": "float",
                "low": "float",
                "close": "float",
                "volume": "float",
            }
        )
        pairdata["date"] = to_datetime(
            pairdata["date"], unit="ms", utc=True, infer_datetime_format=True
        )
        return pairdata

    def ohlcv_append(
        self, pair: str, timeframe: str, data: DataFrame, candle_type: CandleType
    ) -> None:
        """
        Append data to existing data structures
        :param pair: Pair
        :param timeframe: Timeframe this ohlcv data is for
        :param data: Data to append.
        :param candle_type: Any of the enum CandleType (must match trading mode!)
        """
        raise NotImplementedError()

    @classmethod
    def trades_get_pairs(cls, datadir: Path) -> List[str]:
        """
        Returns a list of all pairs for which trade data is available in this
        :param datadir: Directory to search for ohlcv files
        :return: List of Pairs
        """
        _tmp = [
            re.search(r"^(\S+)(?=\-trades.json)", p.name)
            for p in datadir.glob(f"*trades.{cls._get_file_extension()}")
        ]
        # Check if regex found something and only return these results to avoid exceptions.
        return [cls.rebuild_pair_from_filename(match[0]) for match in _tmp if match]

    def trades_store(self, pair: str, data: TradeList) -> None:
        """
        Store trades data (list of Dicts) to file
        :param pair: Pair - used for filename
        :param data: List of Lists containing trade data,
                     column sequence as in DEFAULT_TRADES_COLUMNS
        """
        filename = self._pair_trades_filename(self._datadir, pair)
        misc.file_dump_json(filename, data, is_zip=self._use_zip)

    def trades_append(self, pair: str, data: TradeList):
        """
        Append data to existing files
        :param pair: Pair - used for filename
        :param data: List of Lists containing trade data,
                     column sequence as in DEFAULT_TRADES_COLUMNS
        """
        raise NotImplementedError()

    def _trades_load(self, pair: str, timerange: Optional[TimeRange] = None) -> TradeList:
        """
        Load a pair from file, either .json.gz or .json
        # TODO: respect timerange ...
        :param pair: Load trades for this pair
        :param timerange: Timerange to load trades for - currently not implemented
        :return: List of trades
        """
        filename = self._pair_trades_filename(self._datadir, pair)
        tradesdata = misc.file_load_json(filename)

        if not tradesdata:
            return []

        if isinstance(tradesdata[0], dict):
            # Convert trades dict to list
            logger.info("Old trades format detected - converting")
            tradesdata = trades_dict_to_list(tradesdata)
            pass
        return tradesdata

    @classmethod
    def _get_file_extension(cls):
        return "json.gz" if cls._use_zip else "json"


class JsonGzDataHandler(JsonDataHandler):

    _use_zip = True
