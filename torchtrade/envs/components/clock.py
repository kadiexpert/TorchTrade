import pandas as pd
from typing import Any

class Clock:
    def __init__(self, timestamp: pd.Timestamp = pd.Timestamp("now"), timeframe: str = "1m"):
        """
        Initialize the clock with a given timestamp and timeframe.

        Parameters:
        timestamp (pd.Timestamp, optional): The initial timestamp for the clock. Defaults to the current time.
        timeframe (str, optional): The time interval for the clock, in the format "1m" for 1 minute or "3h" for 3 hours. Defaults to "1m".
        """
        self.initial_timestamp = timestamp
        self.timestamp = timestamp
        self.timeframe = pd.Timedelta(timeframe)
        
    def configure(self,timestamp: pd.Timestamp,timeframe: str ):
        """
        Configure the clock with a given timestamp and timeframe. The clock is reset after configuration
        
        Parameters:
        timestamp (pd.Timestamp): The initial timestamp for the clock.
        timeframe (str): The time interval for the clock, in the format "1m" for 1 minute or "3h" for 3 hours.
        """
        self.initial_timestamp = timestamp
        self.timestamp = timestamp
        self.timeframe = pd.Timedelta(timeframe)

    def reset(self) -> None:
        """
        Reset the clock to its initial timestamp.
        """
        self.timestamp = self.initial_timestamp

    def next(self) ->  pd.Timestamp:
        """
        Increment the clock by its time interval.
        
        Returns:
        pd.Timestamp: The current time of the clock.
        """
        self.timestamp += self.timeframe
        return self.timestamp

    def currentTime(self) -> pd.Timestamp:
        """
        Get the current time of the clock.

        Returns:
        pd.Timestamp: The current time of the clock.
        """
        return self.timestamp
