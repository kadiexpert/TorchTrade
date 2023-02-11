import pandas as pd
from typing import Optional
from torchtrade.config.global_clock import clock

class DataFeed:
    """A class that provides data feed for multiple assets.

    Arguments:
        df (pandas.DataFrame): A multi-index dataframe indexed by asset symbol and timestamp and containing data columns.

    Attributes:
        df (pandas.DataFrame): The dataframe containing the data.
        clock (clock): A global clock object that contains the current time.
    """

    def __init__(self, df: pd.DataFrame):
        global clock
        self.df = df
        self.clock = clock

    def retrieve_data(self, lookback_period: int) -> pd.DataFrame:
        """Retrieve the historical data for all assets for a specified lookback period.

        Arguments:
            lookback_period (int): The number of timeframes to look back from the current clock timestamp.

        Returns:
            pandas.DataFrame: The data for all assets for the specified lookback period.

        Raises:
            ValueError: If the lookback period starts before the earliest available data or if the clock timestamp is out of the data range.
            ValueError: If there are missing timestamps in the lookback period for a symbol.
        """
        start_timestamp = self._calculate_start_timestamp(lookback_period)
        expected_timestamps = self._generate_expected_timestamps(start_timestamp)
        self._check_timestamp_range(start_timestamp)
        return self._get_data_for_lookback_period(expected_timestamps)

    def _calculate_start_timestamp(self, lookback_period: int) -> pd.Timestamp:
        """Calculate the start timestamp of the lookback period."""
        return self.clock.currentTime() - lookback_period * self.clock.timeframe

    def _generate_expected_timestamps(self, start_timestamp: pd.Timestamp) -> pd.DatetimeIndex:
        """Generate the expected timestamps for the lookback period."""
        end_timestamp = self.clock.currentTime()
        return pd.date_range(start=start_timestamp, end=end_timestamp, freq=self.clock.timeframe)

    def _check_timestamp_range(self, start_timestamp: pd.Timestamp):
        """Check if the lookback period is within the dataframe's date range."""
        if start_timestamp < self.df.index.get_level_values(1).min():
            raise ValueError(f"Not enough data: the lookback period starts before the earliest available data")
        if self.clock.currentTime() > self.df.index.get_level_values(1).max():
            raise ValueError(f"Clock timestamp is out of the data range")

    def _get_data_for_lookback_period(self, expected_timestamps: pd.DatetimeIndex) -> pd.DataFrame:
        """Retrieve the historical data for a lookback period for all assets."""
        data = pd.DataFrame()
        for symbol in self.df.index.get_level_values(0).unique():
            # Get the data for the lookback period
            index = pd.MultiIndex.from_product(([symbol],expected_timestamps))
            symbol_data = self.df.loc[index]
            # Check if there are missing timestamps in the lookback period
            missing_timestamps = set(expected_timestamps) - set(symbol_data.index.get_level_values(1))
            if missing_timestamps:
                raise ValueError(f"Missing timestamps in the period for symbol '{symbol}': {missing_timestamps}")
            data = pd.concat([data, symbol_data])
        return data