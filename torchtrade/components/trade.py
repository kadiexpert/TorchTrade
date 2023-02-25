from typing import Tuple, Optional
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
    """Class representing a trade.

    Attributes:
    -----------
    id : str
        The unique identifier of the trade.
    creation_timestamp : pd.Timestamp
        The timestamp when the trade was created.
    symbol : str
        The symbol of the asset being traded.
    direction : TradeDirection
        The direction of the trade (LONG or SHORT).
    quantity : float
        The quantity of the asset being traded.
    leverage : float
        The leverage used in the trade.
    execution_timestamp : Optional[float], default=None
        The timestamp when the trade should be executed. If None, the trade is executed immediately.
    stop_loss : Optional[float], default=None
        The stop loss level of the trade as a percentage. If None, there is no stop loss.
    risk_reward : Optional[float], default=None
        The risk reward ratio of the trade. If None, there is no take profit.
    discount : Optional[float], default=0.9
        The discount factor used to calculate the discounted PNL.
    commission : Optional[float], default=0.0
        The commission rate ex 0.01 for 1% commission

    Methods:
    --------
    update(market_data: pd.DataFrame) -> None:
        Updates the trade using the market data.
    close_trade(timestamp: pd.Timestamp, price: float) -> None:
        Closes the trade at the given timestamp and price.

    """

    def __init__(
        self,
        id: str,
        creation_timestamp: pd.Timestamp,
        symbol: str,
        direction: TradeDirection,
        quantity: float,
        leverage: float,
        execution_timestamp: Optional[float] = None,
        stop_loss: Optional[float] = None,
        risk_reward: Optional[float] = None,
        discount: Optional[float] = 0.9,
        commission: Optional[float] = 0.0
    ):
        """Initializes a new trade object."""
        #Trade identification
        self.id = id
        
        #Trade Params
        self.symbol = symbol
        self.direction = direction
        self.quantity = quantity
        self.leverage = leverage
        self.stop_loss = stop_loss
        self.risk_reward = risk_reward
        self.discount = discount
        self.commission = commission
        
        #Trade Status
        self.status = TradeStatus.CREATED
        
        #Trade key times 
        self.creation_timestamp = creation_timestamp
        self.execution_timestamp = creation_timestamp if execution_timestamp is None else execution_timestamp
        self.close_timestamp = None
        self.last_update_timestamp = creation_timestamp
        
        #Trade key prices
        self.fill_price = None
        self.stop_loss_price = None
        self.take_profit_price = None
        self.close_price = None

        #Trade Metrics
        self.time_in_trade = 0
        self.paid_commission = 0
        self.unrealized_pnl = 0
        self.realized_pnl = 0
        self.unrealized_pnl_percentage = 0
        self.realized_pnl_percentage = 0
        self.unrealized_pnl_percentage_discounted = 0
        self.realized_pnl_percentage_discounted = 0
    
    def update(self, market_data: pd.DataFrame) -> None:
        """
        Update the trade based on the provided market data.

        Args:
            market_data (pd.DataFrame): The market data.

        Returns:
            None
        """
        if self.status is TradeStatus.CLOSED or self.status is TradeStatus.REJECTED:
            return

        timestamp, is_traded, open_price, high_price, low_price, close_price = self.__process_data(market_data)

        if not is_traded:
            return

        self.last_update_timestamp = timestamp

        if self.status is TradeStatus.CREATED:
            if timestamp == self.execution_timestamp:
                self.__fill_trade(close_price)
            elif timestamp > self.execution_timestamp:
                self.__reject_trade()
        else:
            # Update trade metrics
            self.__update_metrics(close_price)
            
            # Check if stop loss is hit
            if self.__has_stop_loss() and self.__is_stop_loss_hit(high_price, low_price):
                self.__close_trade(timestamp, self.stop_loss_price)

            # Check if take profit is hit
            if self.__has_take_profit() and self.__is_take_profit_hit(high_price, low_price):
                self.__close_trade(timestamp, self.take_profit_price)
                
            
    def __update_metrics(self, price: float) -> None:
        """
        Update the metrics of the trade.

        Args:
            price (float): The current price of the asset.

        Returns:
            None
        """
        # Increment the time in trade
        self.time_in_trade += 1
        
        # Calculate the unrealized P&L and its percentage
        self.unrealized_pnl = self.direction.value * ((self.quantity * price) - (self.quantity * self.fill_price))
        self.unrealized_pnl_percentage = self.unrealized_pnl / (self.quantity * self.fill_price)
        
        # Apply the trade's discount factor to the unrealized P&L percentage
        self.unrealized_pnl_percentage_discounted = self.unrealized_pnl_percentage * (self.discount ** self.time_in_trade)

    
    def __reject_trade(self) -> None:
        """
        Rejects the trade by setting its status to TradeStatus.REJECTED.
        """
        self.status = TradeStatus.REJECTED
           

    def __fill_trade(self, fill_price: float) -> None:
        """
        Fills the trade with the given fill price and calculates the stop loss and take profit prices and trade entry commission

        Args:
            fill_price (float): The fill price of the trade.

        Raises:
            ValueError: If the trade status is not `TradeStatus.CREATED`.
        """
        if self.status != TradeStatus.CREATED:
            raise ValueError("Trade must be in CREATED state to fill")
            
        self.fill_price = fill_price 
        self.stop_loss_price = fill_price*(1 - self.direction.value*self.stop_loss) if self.stop_loss is not None else None
        
        if self.stop_loss is not None and self.risk_reward is not None:
            self.take_profit_price = fill_price*(1 + self.direction.value*self.risk_reward*self.stop_loss)
        else:
            self.take_profit_price = None
                        
        self.status = TradeStatus.FILLED   
        self.paid_commission += fill_price*self.quantity*self.commission
        self.realized_pnl -= self.paid_commission
  
        
    def __has_stop_loss(self) -> bool:
        """
        Check if the trade has a stop loss.

        Returns:
            bool: True if the trade has a stop loss, False otherwise.
        """
        return self.stop_loss is not None


    def __is_stop_loss_hit(self, high_price: float, low_price: float) -> bool:
        """
        Check if the stop loss level has been hit.

        Args:
            high_price (float): The highest price reached since the trade was executed.
            low_price (float): The lowest price reached since the trade was executed.

        Returns:
            bool: True if the stop loss level has been hit, False otherwise.
        Raises:
            ValueError: If the trade direction is invalid.
        """
        if self.direction == TradeDirection.LONG:
            return low_price <= self.stop_loss_price
        elif self.direction == TradeDirection.SHORT:
            return high_price >= self.stop_loss_price
        else:
            raise ValueError("Invalid trade direction")


    def __has_take_profit(self):
        """
        Checks if the trade has a take profit price set.
        
        Returns:
            bool: True if the trade has a take profit price, False otherwise.
        """
        return self.take_profit_price is not None


    def __is_take_profit_hit(self, high_price: float, low_price: float):
        """
        Checks if the trade's take profit price has been hit based on the given high and low prices.

        Args:
            high_price (float): The highest price of the asset since the last trade update.
            low_price (float): The lowest price of the asset since the last trade update.

        Returns:
            bool: True if the take profit price has been hit, False otherwise.
        """
        if self.direction == TradeDirection.LONG:
            return high_price >= self.take_profit_price
        elif self.direction == TradeDirection.SHORT:
            return low_price <= self.take_profit_price
        else:
            raise ValueError("Invalid trade direction")


    def __close_trade(self, timestamp: pd.Timestamp, price: float):
        """
        Close the trade with the given price and timestamp.

        Args:
            timestamp (pd.Timestamp): The timestamp at which the trade is closed.
            price (float): The price at which the trade is closed.
        """
        self.close_price = price
        self.close_timestamp = timestamp
        self.status = TradeStatus.CLOSED
        self.paid_commission += price*self.quantity*self.commission
        
        self.realized_pnl -= price*self.quantity*self.commission
        self.realized_pnl += self.direction.value* ((self.quantity * price) - (self.quantity*self.fill_price))
        self.realized_pnl_percentage =  self.realized_pnl /(self.quantity*self.fill_price)
        self.realized_pnl_percentage_discounted = self.realized_pnl_percentage * (self.discount**self.time_in_trade) 
        
        self.unrealized_pnl = 0
        self.unrealized_pnl_percentage =  0
        self.unrealized_pnl_percentage_discounted = 0
       


    def __process_data(self, data: pd.DataFrame) -> Tuple[pd.Timestamp, float, float, float, float, bool]:
        """
        Extract the relevant trade data from the given DataFrame.

        Args:
            data (pd.DataFrame): The DataFrame containing the trade data.

        Returns:
            Tuple[pd.Timestamp, float, float, float, float, bool]: A tuple containing the timestamp,
            is_traded flag, open price, high price, low price, and close price.
        """
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
Last Update Timestamp: {self.last_update_timestamp}
Symbol: {self.symbol}
Trade Details:
    Execution time: {self.execution_timestamp}
    Closing Time: {self.close_timestamp}
    Entry Price: {self.fill_price}
    Time In Trade : {self.time_in_trade}
    Stop Loss %: {self.stop_loss}
    Risk Reward: {self.risk_reward}
    Stop Loss Price: {self.stop_loss_price}
    Take Profit Price: {self.take_profit_price}
    Status: {self.status}
    Realized P&L %: {self.realized_pnl_percentage}
    Realized P&L : {self.realized_pnl}
    Realized Discounted P&L% : {self.realized_pnl_percentage_discounted}
    Unrealized P&L %: {self.unrealized_pnl_percentage}
    Unrealized P&L : {self.unrealized_pnl}
    Unrealized Discounted P&L% : {self.unrealized_pnl_percentage_discounted}
    Paid Commission : {self.paid_commission}
            """