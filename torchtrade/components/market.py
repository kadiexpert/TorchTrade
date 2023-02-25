import pandas as pd
from typing import Optional
from torchtrade.components.trade import Trade, TradeStatus

class Market:
    """A class that provides data feed for multiple assets.

    Arguments:
        df (pandas.DataFrame): A multi-index dataframe indexed by asset symbol and timestamp and containing data columns.

    Attributes:
        df (pandas.DataFrame): The dataframe containing the data.
        timestamp (Optional[pandas.Timestamp]): The current timestamp of the market.
        data (Optional[pandas.DataFrame]): The data for the current timestamp.
        observers (list): A list of observers.
    """

    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.timestamp = None
        self.data = None
        self.observers = []

    def update_timestamp(self, timestamp: pd.Timestamp):
        """Update the current timestamp of the market and notify the observers.

        Parameters:
            timestamp (pandas.Timestamp): The new timestamp for the market.
        """
        self.timestamp = timestamp
        self.update_mktData() 
        self.notify_observers()
    
    def update_mktData(self):
        """Update the market data for the current timestamp."""
        symbols = self.df.index.get_level_values(0).unique()
        index = pd.MultiIndex.from_product((symbols,[self.timestamp]))
        self.data = self.df.loc[index]
        
    def register_observer(self, observer):
        """Register a new observer for the market.

        Parameters:
            observer (object): The observer to be registered.
        """
        self.observers.append(observer)
        observer.update(self.data)
        
    def unregister_observer(self, observer):
        """Unregister an observer from the market."""
        if observer in self.observers:
            self.observers.remove(observer)
            
    def notify_observers(self):
        """
        Notify all registered observers with the updated market data.
        """
        # Remove any closed or rejected trades from the observers list
        self.observers = [observer for observer in self.observers 
                        if not (isinstance(observer, Trade) and observer.status in [TradeStatus.CLOSED, TradeStatus.REJECTED])]
        
        # Update the remaining observers with the new data
        for observer in self.observers:
            observer.update(self.data)
            
    def reset(self):
        """Reset the market but keep data in the market
        """
        self.timestamp = None
        self.observers = []


