import pandas as pd

class DataFeed:
    """A class that provides data feed for multiple assets.

    Arguments:
        df (pandas.DataFrame): A multi-index dataframe indexed by asset symbol and timestamp and containing data columns.
        timeframe (str): The frequency of the data, e.g. '1D' for daily data.

    Attributes:
        df (pandas.DataFrame): The dataframe containing the data.
        timeframe (pandas.Timedelta): The frequency of the data as a Timedelta object.
    """

    def __init__(self, df, timeframe):
        self.df = df
        self.timeframe = pd.Timedelta(timeframe)
        
    def next(self, timestamp, lookback_period):
        """Retrieve the historical data for all assets for a specified lookback period.

        Arguments:
            timestamp (pandas.Timestamp): The end timestamp for the data.
            lookback_period (int): The number of timeframes to look back from the end timestamp.

        Returns:
            pandas.DataFrame: The data for all assets for the specified lookback period.

        Raises:
            ValueError: If the lookback period starts before the earliest available data or if the timestamp is out of the data range.
            ValueError: If there are missing timestamps in the lookback period for a symbol.
        """

        # Calculate the start timestamp of the lookback period
        end_timestamp = timestamp - lookback_period * self.timeframe
        
        # Generate the expected timestamps for the lookback period
        expected_timestamps = pd.date_range(start=end_timestamp, end=timestamp, freq=self.timeframe)
        
        # Check if the lookback period is within the dataframe's date range
        if end_timestamp < self.df.index.get_level_values(1).min():
            raise ValueError(f"Not enough data: the lookback period starts before the earliest available data")
        
        if timestamp > self.df.index.get_level_values(1).max():
            raise ValueError(f"Timestamp is out of the data range")
        
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
