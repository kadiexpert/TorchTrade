import pandas as pd
from typing import Any

class Clock:
    
    def __init__(self, start_timestamp: pd.Timestamp, end_timestamp: pd.Timestamp, timeframe: str = "1m"):
        """
        Initialize the clock with a given start and end timestamp and timeframe.

        Parameters:
        start_timestamp (pd.Timestamp): The start timestamp for the clock.
        end_timestamp (pd.Timestamp): The end timestamp for the clock.
        timeframe (str, optional): The time interval for the clock, in the format "1m" for 1 minute or "3h" for 3 hours. Defaults to "1m".
        """
        self.start_timestamp = start_timestamp
        self.end_timestamp = end_timestamp
        self.timestamp = start_timestamp
        self.timeframe = pd.Timedelta(timeframe)
        self.observers = []
        

    def reset(self) -> None:
        """
        Reset the clock to its start timestamp.
        """
        self.timestamp = self.start_timestamp
        self.reset_observers()
        self.notify_observers()

    def next(self) -> pd.Timestamp:
        """
        Increment the clock by its time interval.
        
        Returns:
        pd.Timestamp: The current time of the clock.
        """
        next_timestamp = self.timestamp + self.timeframe
        if next_timestamp > self.end_timestamp:
             ValueError("Current time has passed the end timestamp.")
             
        self.timestamp = next_timestamp
        self.notify_observers()
        return self.timestamp


    def currentTime(self) -> pd.Timestamp:
        """
        Get the current time of the clock.

        Returns:
        pd.Timestamp: The current time of the clock.
        """
        return self.timestamp
    
    def register_observer(self, observer):
        """
        Register an observer to receive notifications from the clock.

        Parameters:
        observer: The observer to register.
        """
        self.observers.append(observer)
        observer.update_timestamp(self.timestamp)
    
    def notify_observers(self):
        """
        Notify all registered observers that the clock has advanced.
        """
        for observer in self.observers:
            observer.update_timestamp(self.timestamp)
            
    def reset_observers(self):
        """
        Reset all registered observers 
        """
        for observer in self.observers:
            observer.reset()
    
    def has_reached_end(self) -> bool:
        """
        Check if the current timestamp has reached the end timestamp.

        Returns:
        bool: True if the current timestamp has reached the end timestamp, False otherwise.
        """
        return self.timestamp >= self.end_timestamp