from torchtrade.components import Market, Trade, TradeDirection, TradeStatus
from typing import Optional,List
from tabulate import tabulate

class Broker:
    """
    A broker class responsible for tracking and opening trades.

    Attributes:
        trades (list): List of trades made by the broker.
        market (Market): Market instance that the broker is trading on.
        commission (float, optional): Commission charged by the broker per trade.

    Methods:
        openTrade: Open a new trade with given parameters.
        getRealizedProfit: Get the Realized Profit for all closed Trades
    """

    def __init__(
        self,
        market:Market,
        commission: Optional[float] = 0.0
    ):
        """
        Initialize the Broker instance.

        Args:
            market (Market): Market instance that the broker is trading on.
            commission (float, optional): Commission charged by the broker per trade.
        """
        self.trades :List[Trade] = []
        self.market = market
        self.commision = commission
        
    def openTrade(
        self,
        id: str,
        symbol: str,
        direction: TradeDirection,
        quantity: float,
        leverage: float,
        stop_loss: Optional[float] = None,
        risk_reward: Optional[float] = None,
    ):
        """
        Open a new trade with given parameters.

        Args:
            id (str): Unique identifier for the trade.
            symbol (str): Symbol of the asset being traded.
            direction (TradeDirection): Direction of the trade (LONG or SHORT).
            quantity (float): Quantity of the asset being traded.
            leverage (float): Leverage used for the trade.
            execution_timestamp (float, optional): Timestamp at which the trade is executed.
            stop_loss (float, optional): Stop-loss price for the trade.
            risk_reward (float, optional): Risk-reward ratio for the trade.
        """
        trade = Trade(
            id,
            self.market.timestamp,
            symbol,
            direction,
            quantity,
            leverage,
            self.market.timedelta,
            stop_loss=stop_loss,
            risk_reward=risk_reward,
            commission=self.commision
            )
        self.market.register_observer(trade)
        self.trades.append(trade)

    def get_realized_profit(self) -> float: 
        realized_profit = 0.0
        for trade in self.trades:
            if trade.status is TradeStatus.CLOSED:
                realized_profit+=trade.realized_pnl
        return realized_profit
    
    def get_unrealized_profit(self) -> float:
        unrealized_profit = 0.0
        for trade in self.trades:
            if trade.status is TradeStatus.FILLED:
                unrealized_profit+=trade.unrealized_pnl
        return unrealized_profit
    
    
    def closed_trades_count(self) -> int:
        closed_trades = [trade for trade in self.trades if trade.status is TradeStatus.CLOSED]
        return len(closed_trades)
    
    def open_trades_count(self) -> int:
        open_trades = [trade for trade in self.trades if trade.status is TradeStatus.FILLED]
        return len(open_trades)
    
    
    def winning_trades_count(self) -> int: 
        winnig_trades = [trade for trade in self.trades if trade.status is TradeStatus.CLOSED and trade.realized_pnl > 0]
        return len(winnig_trades)
    
    def losing_trades_count(self) -> int: 
        losing_trades = [trade for trade in self.trades if trade.status is TradeStatus.CLOSED and trade.realized_pnl < 0]
        return len(losing_trades)
    
    def get_additive_reward_percentage(self) -> float :
        additive_reward_percentage = 0.0
        for trade in self.trades:
            if trade.status is TradeStatus.CLOSED:
                additive_reward_percentage+=trade.realized_pnl_percentage
        return additive_reward_percentage
    
    def reset(self):
        self.trades = []
        
        
    def info(self) -> dict: 
        """Return broker information as Dictionnary

        Returns:
            dict: Broker info
        """
        info = {
            "Timestamp": self.market.timestamp,
            "Number of trades" : len(self.trades),
            "Realized Profit": self.get_realized_profit(),
            "Unrealized Profit": self.get_unrealized_profit(),
            "Closed Trades Count": self.closed_trades_count(),
            "Open Trades Count": self.open_trades_count(),
            "Winning Trades Count": self.winning_trades_count(),
            "Losing Trades Count" : self.losing_trades_count(),
            "Win Rate" : "{:.2%}".format(self.winning_trades_count()/self.closed_trades_count()) if  self.closed_trades_count()> 0 else None 
        }
        return info
        
    def __str__(self) -> str: 
        """Broker info as String

        Returns:
            str: Broker info
        """
        info = self.info()
        headers = ["Key", "Value"]
        rows = [[k, v] for k, v in info.items()]
        return tabulate(rows, headers=headers)
            
