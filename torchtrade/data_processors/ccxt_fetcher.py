""""
    Module for fetching crypto data from a given exchange source
"""

from typing import Optional
from datetime import datetime,timezone
import pandas as pd
import ccxt

class CcxtFetcher:
    """
    Class for fetching financial data from a given exchange source, symbols, and timeframe.
    
    Parameters:
    source (str): The exchange source to fetch data from.
    symbols (list): List of symbols to fetch data for.
    timeframe (str): Timeframe of data to fetch.
    since (datetime, optional): The start date of the data to fetch. Defaults to 2015/01/01.
    until (datetime, optional): The end date of the data to fetch. Defaults to None.
    """
    def __init__(
            self,
            source: str,
            symbols: list,
            timeframe: str,
            since: Optional[datetime]=datetime(2015,1,1),
            until: Optional[datetime]=None
        ):
        self.source = source
        self.symbols = symbols
        self.timeframe = timeframe
        self.since = since
        self.until = until
        self.first_timestamp=None
        self.last_timestamp = None
        self.step = None
        self.exchange = None

    def _get_first_candle_timestamp(self):
        """
        Returns the earliest candle timestamp in milliseconds
        """
        start_timestamp = int(self.since.replace(tzinfo=timezone.utc).timestamp()*1000)
        listing_dt = []
        for symbol in self.symbols:
            ohlcv = self.exchange.fetch_ohlcv(symbol, self.timeframe, start_timestamp, limit=1)
            listing_dt += [ohlcv[0][0]]
        return min(listing_dt)

    def _check_fetch_ohlcv(self):
        """
        Checks if the exchange source allows fetching of OHLCV data.
        """
        if not self.exchange.has["fetchOHLCV"]:
            raise ValueError(f"{self.source} doesn't allow OHLCV fetching")

    def _check_timeframe_supported(self):
        """
        Checks if the specified timeframe is supported by the exchange source.
        """
        supported_timeframes = self.exchange.timeframes
        if  not self.timeframe.lower() in [k.lower() for k in supported_timeframes.keys()]:
            raise ValueError(f"{self.timeframe} timeframe not supported by {self.source}")

    def _check_symbols_supported(self):
        """
        Checks if all symbols in `symbols` are supported by the exchange source.
        """
        for symbol in self.symbols:
            if not symbol  in self.exchange.symbols:
                raise ValueError(f"{symbol} not supported by {self.source}")

    def _set_timestamps(self):
        """
        Sets the start and end timestamps of the data to fetch.
        """
        self.first_timestamp = self._get_first_candle_timestamp()

        if self.until is None:
            self.last_timestamp = int(datetime(datetime.today().year,datetime.today().month,datetime.today().day,tzinfo=timezone.utc).timestamp()*1000)
        else:
            self.last_timestamp = int(self.until.replace(tzinfo=timezone.utc).timestamp()*1000)

    def _calculate_step(self):
        """
        Calculate the number of milliseconds represented by the given time string
        """
        units = {
            's': 1*1000,
            'm': 60*1000,
            'h': 60*60*1000,
            'd': 24*60*60*1000,
        }
        number = int(self.timeframe[:-1])
        unit = self.timeframe[-1].lower()
        if unit not in units:
            raise ValueError("Invalid timeframe")

        self.step =number * units[unit]

    def fetch_data(self):
        """
        This method is used to fetch the OHLCV data for the specified symbols and time frame.
        
        Returns:
            DataFrame : A multi-indexed dataframe containing the fetched data with the following columns:
                - isTraded
                - open
                - high
                - low
                - close
                - volume
        """
        self.exchange = getattr(ccxt, self.source)()
        self.exchange.loadMarkets()
        self._check_fetch_ohlcv()
        self._check_timeframe_supported()
        self._check_symbols_supported()
        self._set_timestamps()
        self._calculate_step()

        print(f"Fetching {self.timeframe} timeframe data since {datetime.utcfromtimestamp(self.first_timestamp/1000)} until {datetime.utcfromtimestamp(self.last_timestamp/1000)}")
        index_names = pd.MultiIndex.from_product(
            [self.symbols, range(self.first_timestamp, self.last_timestamp + self.step, self.step)]
        )
        column_names = ["isTraded", "open", "high", "low", "close", "volume"]

        data = pd.DataFrame(index=index_names, columns=column_names)
        data.rename_axis(["symbol","timestamp"], axis=0, inplace=True)

        for index, symbol in enumerate(self.symbols):
            ohlcv = []
            timestamp = self.first_timestamp
            while timestamp <= self.last_timestamp:
                ohlcv += self.exchange.fetch_ohlcv(
                    self.symbols[index],
                    self.timeframe,
                    timestamp,
                    limit=300000
                    )
                timestamp = ohlcv[-1][0] + 1000
            for candle in ohlcv:
                key = (symbol, candle[0])
                if key in data.index:
                    data.loc[key] = [1] + candle[1:]

        data.loc[data.isnull().any(axis=1), :] = 0
        data.index = data.index.set_levels(pd.to_datetime(data.index.levels[1], unit='ms'), level=1)

        return data
