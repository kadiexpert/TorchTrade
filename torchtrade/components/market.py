import pandas as pd
import numpy as np
from tabulate import tabulate
from datetime import datetime
from typing import List, Optional, Tuple
from torchtrade.components.trade import Trade, TradeStatus
from torchtrade.data_processors.binance_fetcher import BinanceFetcher

class Market:
    """
    A class that provides data feed for multiple assets.

    Args:
        symbols (List[str]): A list of symbols for the assets to track.
        timeframe (str): A string representation of the time frame for each candle, e.g. "1D" for daily candles.
        since (Optional[datetime], optional): The earliest timestamp to consider when loading data. Defaults to datetime(2015,1,1).
        until (Optional[datetime], optional): The latest timestamp to consider when loading data. Defaults to None, which loads data up to the current time.
        include_technical_indicators (Optional[bool], optional): Whether to include technical indicators in the data. Defaults to True.

    Attributes:
        symbols (List[str]): A list of symbols for the assets being tracked.
        timeframe (str): A string representation of the time frame for each candle.
        timedelta (pd.Timedelta): A timedelta representing the duration of each candle.
        include_technical_indicators (bool): Whether to include technical indicators in the data.
        data (pd.DataFrame): The prepared data.
        since (datetime): The earliest timestamp to consider when loading data.
        until (Optional[datetime]): The latest timestamp to consider when loading data.
        timestamp (Optional[pd.Timestamp]): The current timestamp of the market.
        observers (List[Observer]): A list of observers.
    """
    
    def __init__(
        self, 
        symbols: List[str],
        timeframe: str,
        since: Optional[datetime] = datetime(2015, 1, 1),
        until: Optional[datetime] = None,
        include_technical_indicators: Optional[bool] = True,
    ):
        """Initialize a Market object."""
        self.symbols = symbols
        self.timeframe = timeframe
        self.__timedelta = pd.Timedelta(timeframe)
        self.include_technical_indicators = include_technical_indicators
        # Prepared data
        self.__prepared = False
        self.data = None
        self.last_market_data = None
        # Time range
        self.since = since
        self.until = until
        # Current timestamp and observers
        self.timestamp = None
        self.observers = []
        
    def prepare(self):
        """Fetches data and sets up the `Market` object for use.

        The method fetches data from a data fetcher object, checks the data for completeness and sets up the `Market`
        object with the fetched data. This method needs to be called before using the `Market` object.

        Raises:
            RuntimeError: If the method is called when the `Market` object is already prepared.

        """
        if self.__prepared:
            raise RuntimeError("Market object is already prepared.")
        
        # Fetch data using the BinanceFetcher object
        dataFetcher = BinanceFetcher(self.symbols, self.timeframe, self.since, self.until, self.include_technical_indicators)
        data = dataFetcher.fetch_data()

        # Check that the data is not empty and contains all the symbols and timestamps specified
        self.__check_data(data)

        # Set the prepared flag and store the fetched data in the `Market` object
        self.__prepared = True
        self.data = data
        self.symbols = data.index.get_level_values(0).unique()
        
        # Set the since and until timestamps to the minimum and maximum timestamps in the data
        self.since = data.index.get_level_values(1).min()
        self.until = data.index.get_level_values(1).max()

        # Set the current timestamp to the since timestamp
        self.timestamp = self.since
        
        # Print
        print(self)

        
    def reset(self, rollback_periods: int = 0, random: bool = False) -> Tuple[pd.Timestamp,pd.DataFrame]:
        """
        Resets the `Market` object to its initial state while keeping the data intact.

        The method resets the clock to the start time of the data or to a random time within the specified time range.
        It also clears the list of observers and updates the market data.

        Parameters:
        rollback_periods (int, optional): The number of time intervals to roll back the market. Defaults to 0.
        random (bool, optional): If True, sets the timestamp to a random time within the given range. 
            If False, sets the timestamp to the start time plus `rollback_periods` intervals. Defaults to False.
        returns:
        Tuple[pd.Timestamp, pd.DataFrame]: A tuple that includes the new timestamp and the updated market data for the given window.

        """
        # Check if the Market object has been prepared
        self.__check_preparation()

         # Generate a list of all timestamps within the specified rang
        timestamps = pd.date_range(start=self.since, end=self.until, freq=self.__timedelta)
        
        if rollback_periods >= len(timestamps): 
            raise ValueError(f"Rollback_periods exceeds the timestamps count")
        
        # Set the timestamp to the start time plus `window_size` intervals or a random time within the given range
        if random:
            # Set the timestamp to a random time within the specified range
            self.timestamp = self.since + np.random.randint(rollback_periods, len(timestamps)) * self.__timedelta
        else:
            # Set the timestamp to the start time plus `window_size` intervals
            self.timestamp = self.since + (rollback_periods) * self.__timedelta

        # Clear the list of observers and update the market data
        self.observers = []
        self.__update_mktData()
        return (self.timestamp, self.get_market_data(self.timestamp,rollback_periods))
    
    
    def get_market_data(self, timestamp: pd.Timestamp, rollback_periods: int = 0) -> pd.DataFrame:
        """
        Get market data for a given timestamp and rollback period.

        Parameters:
        timestamp (pd.Timestamp): The timestamp to get market data for.
        rollback_periods (int): The number of periods to roll back.

        Returns:
        pd.DataFrame: A DataFrame containing market data for the given timestamp and rollback period.
        """

        end_timestamp = timestamp
        start_timestamp = end_timestamp - rollback_periods*self.__timedelta

        # Check if timestamps are within the valid range
        if end_timestamp > self.until:
            raise ValueError(f"end_timestamp {end_timestamp} is after the valid range {self.until}")
        if start_timestamp < self.since:
            raise ValueError(f"start_timestamp {start_timestamp} is before the valid range {self.since}")

        market_data = self.data.loc[(self.data.index.get_level_values('timestamp') >= start_timestamp) & (self.data.index.get_level_values('timestamp') <= end_timestamp)]

        return market_data

    def __update_mktData(self):
        """Update the market data for the current timestamp."""
        index = pd.MultiIndex.from_product((self.symbols,[self.timestamp]))
        self.last_market_data = self.data.loc[index]
        
    def __notify_observers(self):
        """
        Notify all registered observers with the updated market data.
        """
        # Remove any closed or rejected trades from the observers list
        self.observers = [observer for observer in self.observers 
                        if not (isinstance(observer, Trade) and observer.status in [TradeStatus.CLOSED, TradeStatus.REJECTED])]
        
        # Update the remaining observers with the new data
        for observer in self.observers:
            observer.update(self.last_market_data)
            
        
    def __check_data(self,data:pd.DataFrame):
        """Check if the data meets the specified conditions."""
        if data.empty:
            raise ValueError("Data is empty.")
        if not isinstance(data.index, pd.MultiIndex) or data.index.names != ["symbol", "timestamp"]:
            raise ValueError("Data index is not a MultiIndex with names 'symbol' and 'timestamp'.")
        if any(col not in data.columns for col in ["open", "high", "low", "close", "volume"]):
            raise ValueError("Data is missing required columns: open, high, low, close, volume.")
        if data.isnull().values.any():
            raise ValueError("Data contains NaN values.")
        if not data.index.is_unique:
            raise ValueError("Data contains non-unique index.")
        print("/ Market data check completed successfully")
    
    def next(self,  rollback_periods :int = 0) ->  Tuple[pd.Timestamp,pd.DataFrame]:
        """
        Increment the clock by its time interval.
        
        Returns:
        pd.Timestamp: The current time of the clock.
        """
        self.__check_preparation()
        next_timestamp = self.timestamp + self.__timedelta
        if next_timestamp > self.until:
             ValueError("Current time has passed the end timestamp.")
             
        self.timestamp = next_timestamp
        self.__update_mktData()
        self.__notify_observers()
        return (self.timestamp, self.get_market_data(self.timestamp,rollback_periods))
    
    def __check_preparation(self):
        if not self.__prepared:
            raise ValueError("Please run the method Market.prepare before using it")

    def register_observer(self, observer):
        """Register a new observer for the market.

        Parameters:
            observer (object): The observer to be registered.
        """
        self.__check_preparation()
        self.observers.append(observer)
        observer.update(self.last_market_data)
        
    def unregister_observer(self, observer):
        """Unregister an observer from the market."""
        self.__check_preparation()
        if observer in self.observers:
            self.observers.remove(observer)
            
    def market_ended(self) ->  bool :
        return self.timestamp >= self.until
    
    
    def info(self) -> dict :
        """Returns a dictionnary of market information

        Returns:
            dict: Market information
        """
        info = {
            "TimeFrame": self.timeframe,
            "Symbols": ', '.join(self.symbols),
            "Since": self.since,
            "Until":self.until,
            "Timestamps Count" : self.data.index.get_level_values(1).unique().shape[0]           
        }
        return info
        
    def __str__(self) -> str:
        """Return a string of market information
        """
        info = self.info()
        headers = ["Key", "Value"]
        rows = [[k, v] for k, v in info.items()]
        return tabulate(rows, headers=headers)
            
    