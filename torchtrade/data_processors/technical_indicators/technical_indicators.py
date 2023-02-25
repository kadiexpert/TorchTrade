import talib
import pandas as pd
from torchtrade.data_processors.technical_indicators.config import indicators_config

class TechnicalIndicators:
    """
    A static class that provides methods for calculating technical indicators
    based on a given dataframe and a configuration file.
    This class assumes that the dataframe contains data for a single asset and has a datetime index
    """
    @staticmethod
    def atr(df):
        """
        Calculates the Average True Range (ATR) indicator for the input dataframe.
        Returns numpy array with the calculated values
        
        """
        # Check that the necessary columns exist in the dataframe
        required_cols = set(['high', 'low', 'close'])
        if not required_cols.issubset(df.columns):
            raise ValueError(f"Input dataframe must contain columns: {', '.join(required_cols)}")

        # Get the ATR parameters from the config dictionary
        if 'atr' not in indicators_config or 'timeperiod' not in indicators_config['atr']:
            raise ValueError("ATR parameters not found in the config file.")
        timeperiod = indicators_config['atr']['timeperiod']

        # Calculate the ATR indicator using talib
        atr_values = talib.ATR(df['high'], df['low'], df['close'], timeperiod=timeperiod)

        return atr_values
    
    
    @staticmethod
    def sma(df):
        """
        Calculates the Simple Moving Average  indicator for the input dataframe.
        Returns numpy array with the calculated values
        """
        # Get the SMA parameters from the config dictionary
        if 'sma' not in indicators_config or 'timeperiod' not in indicators_config['sma'] or 'price' not in indicators_config['sma'] :
            raise ValueError("sma parameters not found in the config file.")
        
        price = indicators_config['sma']['price']
        timeperiod = indicators_config['sma']['timeperiod']
        
        # Check that the necessary columns exist in the dataframe
        if price not in  df.columns:
            raise ValueError(f"Input dataframe must contain colum: {price}")

        # Calculate the sma indicator using talib
        sma_values = talib.SMA(df[price],timeperiod=timeperiod)

        return sma_values
    
    
    @staticmethod
    def ema(df):
        """
        Calculates the Exponential Moving Average  indicator for the input dataframe.
        Returns numpy array with the calculated values
        """
        # Get the EMA parameters from the config dictionary
        if 'ema' not in indicators_config or 'timeperiod' not in indicators_config['ema'] or 'price' not in indicators_config['ema'] :
            raise ValueError("ema parameters not found in the config file.")
        
        price = indicators_config['ema']['price']
        timeperiod = indicators_config['ema']['timeperiod']
        
        # Check that the necessary columns exist in the dataframe
        if price not in  df.columns:
            raise ValueError(f"Input dataframe must contain colum: {price}")

        # Calculate the sma indicator using talib
        ema_values = talib.EMA(df[price],timeperiod=timeperiod)

        return ema_values

