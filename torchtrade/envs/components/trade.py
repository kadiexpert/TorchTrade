import pandas as pd
from torchtrade.envs.components.market import Market
from typing import Tuple

class BoundedTrade:
    """A class representing a trade with stop loss and take profit limits.

    Attributes:
        symbol:(str): The symbol of the traded asset
        entry_timestamp (pd.Timestamp): The timestamp when the trade was opened.
        entry_price (float): The price when the trade was opened.
        stop_loss (float): The percentage loss at which the trade should be stopped.
        risk_reward (float): The risk-reward ratio for the trade.
        stop_loss_price (float): The stop loss price for the trade.
        take_profit_price (float): The take profit price for the trade.
        is_open (bool): Whether the trade is currently open or not.
        reward (int): The reward earned from the trade (-1 for loss, 0 for ongoing, 1 for win).
    """
    def __init__(self, symbol:str, entry_timestamp: pd.Timestamp, entry_price: float, stop_loss: float, risk_reward: float, market: Market , timeframe : pd.Timedelta , discount_factor: float):
        """
        Initialize a new trade.

        Args:
            symbol:(str): The symbol of the traded asset
            entry_timestamp (pd.Timestamp): The timestamp when the trade was opened.
            entry_price (float): The price when the trade was opened.
            stop_loss (float): The percentage loss at which the trade should be stopped.
            risk_reward (float): The risk-reward ratio for the trade.
            market (Market): The market to subscribe to for updates.
        """
        self.symbol = symbol
        self.entry_timestamp = entry_timestamp
        self.exit_timestamp = None
        self.entry_price = entry_price
        self.stop_loss = stop_loss
        self.risk_reward = risk_reward
        self.stop_loss_price = self.entry_price * (1 - self.stop_loss / 100)
        self.take_profit_price = self.entry_price * (1 + (self.risk_reward * self.stop_loss) / 100)
        self.is_open = True
        self.reward = 0
        self.market = market
        self.timeframe  = timeframe
        self.discount_factor = discount_factor
        self.time_in_trade = 0
        self.market.register_observer(self)

    def update_mktData (self, data: pd.DataFrame):
        """
        Update the trade's state with new market data.

        Args:
            data (pd.DataFrame): The updated market data for the trade.
        """
        timestamp = data.index[0][1]
        is_traded = data.loc[(self.symbol, timestamp), 'isTraded']
        if not self.is_open or timestamp <= self.entry_timestamp or is_traded==0:
            pass
        else:
            close = data.loc[(self.symbol, timestamp), 'close']
            low = data.loc[(self.symbol,timestamp), 'low']
            if close >= self.take_profit_price:
                self.time_in_trade = len(pd.date_range(start=self.entry_timestamp, end=timestamp, freq=self.timeframe))
                self.reward = self.stop_loss* self.risk_reward * (self.discount_factor**self.time_in_trade)
                self.is_open = False
                self.exit_timestamp = timestamp
                self.market.unregister_observer(self)
            elif low <= self.stop_loss_price:
                self.time_in_trade = len(pd.date_range(start=self.entry_timestamp, end=timestamp, freq=self.timeframe))
                self.reward = -self.stop_loss
                self.is_open = False
                self.exit_timestamp = timestamp
                self.market.unregister_observer(self)
                
    def __str__(self) -> str:
        """
        Return a string representation of the trade.

        Returns:
            str: A string representation of the trade.
        """
        return f"""
            Current Timestamp: {self.market.timestamp}
            Symbol: {self.symbol}
            Trade Details:
                Entry Time: {self.entry_timestamp}
                Exit Time: {self.exit_timestamp}
                Entry Price: {self.entry_price}
                Time In Trade : {self.time_in_trade}
                Stop Loss: {self.stop_loss}
                Risk Reward: {self.risk_reward}
                Stop Loss Price: {self.stop_loss_price}
                Take Profit Price: {self.take_profit_price}
                Is Open: {self.is_open}
                Reward: {self.reward}
            """