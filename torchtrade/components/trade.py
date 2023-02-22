from abc import ABC, abstractmethod
from typing import final,Tuple,Optional
from torchtrade.components.market import Market
import pandas as pd
from enum import Enum


class TradeDirection(Enum):
    LONG = 1
    SHORT = -1

class TradeStatus(Enum):
    CREATED = "created"
    FILLED = "filled"
    REJECTED = "rejected"
    CLOSED = "closed"


    
class Trade:
    """An abstract base class representing a trade.
      order are only market, or market at a certain timestamp
    
    """
    
    def __init__(
        self, 
        id : str,
        creation_timestamp : pd.Timestamp ,
        symbol: str, 
        timeframe: pd.Timedelta,
        direction: TradeDirection, 
        quantity: float, 
        leverage: float,
        market: Market,  
        execution_timestamp: Optional[float] = None,
        stop_loss: Optional[float] = None, 
        risk_reward: Optional[float] = None,
        discount: Optional[float] = 0.9
    ):
        
        self.id = id
        self.creation_timestamp = creation_timestamp
        self.execution_timestamp = creation_timestamp if execution_timestamp is None else execution_timestamp
        self.symbol = symbol
        self.timeframe = timeframe
        self.status = TradeStatus.CREATED
        self.direction = direction
        self.quantity = quantity
        self.leverage = leverage
        self.stop_loss = stop_loss
        self.risk_reward = risk_reward
        self.discount = discount
        self.fill_price = None
        self.stop_loss_price =None
        self.take_profit_price = None
        self.market = market
        self.market.register_observer(self)

   
    # We can omit this function if we notify at subscription
    
    def update(self, market_data):
        if self.status is TradeStatus.CLOSED or self.status is TradeStatus.REJECTED:
            return
        
        timestamp, is_traded, open_price, high_price, low_price, close_price = self.__process_data(market_data)
        
        if not is_traded:
            return 
        
        if self.status is TradeStatus.CREATED: 
            if timestamp == self.execution_timestamp:
                self.__fill_trade(close_price)
            elif timestamp > self.execution_timestamp:
                self.__rejectTrade()
        else:
            # SL
            if self.__has_stop_loss():
                if self.__is_stop_loss_hit(high_price, low_price):
                    self.__close_trade(timestamp,self.stop_loss_price)
            # TP
            if self.__has_take_profit():
                if self.__is_take_profit_hit(high_price, low_price):
                    self.__close_trade(timestamp,self.take_profit_price)
        
            
    def __rejectTrade(self):
        self.status = TradeStatus.REJECTED
        self.market.unregister_observer(self)
           
    
    def __fill_trade(self, fill_price:float):
        self.fill_price = fill_price 
        self.stop_loss_price = fill_price*(1- self.direction.value*self.stop_loss ) if self.stop_loss is not None else None
        if self.stop_loss is not None and self.risk_reward is not None:
            self.take_profit_price = fill_price*(1 + self.direction.value*self.risk_reward*self.stop_loss)
                    
        self.status = TradeStatus.FILLED   
    
    def __has_stop_loss(self):
        return self.stop_loss is not None

    def __is_stop_loss_hit(self, high_price: float, low_price: float):
        if self.direction == TradeDirection.LONG:
            return low_price <= self.stop_loss_price
        elif self.direction == TradeDirection.SHORT:
            return high_price >= self.stop_loss_price
        else:
            raise ValueError("Invalid trade direction")

    def __has_take_profit(self):
        return self.take_profit_price is not None

    def __is_take_profit_hit(self, high_price: float, low_price: float):
        if self.direction == TradeDirection.LONG:
            return high_price >= self.take_profit_price
        elif self.direction == TradeDirection.SHORT:
            return low_price <= self.take_profit_price
        else:
            raise ValueError("Invalid trade direction")

    def __close_trade(self, timestamp: pd.Timestamp, price: float):
        self.close_price = price
        self.close_timestamp = timestamp
        self.status = TradeStatus.CLOSED
        self.market.unregister_observer(self)
        self.realized_pnl = (self.fill_price - self.close_price)*self.direction.value
        self.realized_pnl_percentage = self.realized_pnl/self.fill_price
        self.time_in_trade = len(pd.date_range(start=self.execution_timestamp, end=timestamp, freq=self.timeframe))
        self.realized_pnl_percentage_discounted = self.realized_pnl_percentage *(self.discount**self.time_in_trade)
        
    def __process_data(self, data: pd.DataFrame) -> Tuple[pd.Timestamp, float, float, float, float, bool]:
        # Check if data contains a single timestamp
        if len(data.index.get_level_values(1).unique()) != 1:
            raise ValueError("Data must contain a single timestamp")

        # Select the row corresponding to the traded asset
        row = data.loc[(self.symbol, data.index.get_level_values(1)[0])]

        try:
            open_price, high_price, low_price, close_price, is_traded = row[['open', 'high', 'low', 'close', 'isTraded']].values
            timestamp = data.index.get_level_values(1)[0]
        except KeyError:
            raise KeyError("Missing columns in data.")
            
        return timestamp,is_traded, open_price, high_price, low_price, close_price
    
    def __str__(self) -> str:
        """
        Return a string representation of the trade.

        Returns:
            str: A string representation of the trade.
        """
        return f"""
Update Timestamp: {self.market.timestamp}
Symbol: {self.symbol}
Trade Details:
    Execution time: {self.execution_timestamp}
    Closing Time: {self.close_timestamp}
    Entry Price: {self.fill_price}
    Time In Trade : {self.time_in_trade}
    Stop Loss %: {self.stop_loss*100}
    Risk Reward: {self.risk_reward}
    Stop Loss Price: {self.stop_loss_price}
    Take Profit Price: {self.take_profit_price}
    Status: {self.status}
    pnl %: {self.realized_pnl_percentage}
    pnl : {self.realized_pnl}
    Discounted pnl % : {self.realized_pnl_percentage_discounted}
            """
     