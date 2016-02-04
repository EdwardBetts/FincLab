"""
Class: Data Handler

The DataHandler is an abstract base class (ABC), the rationale for this is that the ABC provides an interface that all inherited classes must adhere to, thereby ensuring compatibility with other system components that communicate with them.

Its inherited classes require the input of 2 key parameters (events and symbol_list) and other optional parameters.

Parameters
----------
events : queue.Queue() object
    The Queue() object that comprises of events (such as MarketEvent etc)
symbol_list : list of strings
    List of symbols (tickers) for which to fetch data.

Notes
-----
One of the goals of an event-driven trading system is to minimise duplication of code between the backtesting element and the live execution element. Ideally, it would be optimal to utilise the same signal generation methodology and portoflio management components for both historical testing and live trading.

In order for this to work, the Strategy objecct (which generates the Signals), and the Portfolio object (which provides Orders based on them), must utilise an identical interface to a market feed for both historic and live running.

This motivates the concept of a class hierachy based on a DataHandler object, which gives all subclasses an interface for providing market data to the remaining components within the system. In this way, any subclass data handler can be "swapped out", without affecting strategy or portfolio calculation.

Specific example subclasses, could include:

 - HistoricDataHandler
 - QuandlDataHandler
 - SecuritiesMasterDataHandler (SQL)
 - InteractiveBrokersMarketFeedDataHandler
 - and etc.
"""


from abc import ABCMeta, abstractmethod
import os
import os.path
import pandas as pd
import numpy as np
import queue

from event import MarketEvent


class ABC(object):
    """
    DataHandler is an abstract base class (ABC) providing an interface for all inherited data handlers (both live and historic). The goal of a (derived) DataHandler object is to output a generated set of bars (OHLCVI) for each symbol requested.

    Parameters at initialisation
    ----------------------------
    event_queue : queue.Queue()
        Event queue object. Default as FIFO queue.
    data_folder : string, default "~/Work/FinanceData/Stock/US/"
        The path to data folder.
    symbol_list : a list of strings.
        The DataHandler will fetch data for the list of symbols (tickers).
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_lastest_bar(self, symbol):
        """
        Returns the latest market data bar.

        Parameters
        ----------
        symbol : string
            The symbol of the financial asset.
        """
        raise NotImplementedError("Should implement .get_latest_bar()")

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars updated.

        Parameters
        ----------
        symbol : string
            The symbol of the financial asset.
        N : int
            The number of bars to retrieve
        """
        raise NotImplementedError("Should implement .get_latest_bars()")

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        """
        Returns a datetime.datetime() object for the last bar.

        Parameters
        ----------
        symbol : string
            The symbol of the financial asset.
        """
        raise NotImplementedError("Should implement .get_latest_bar_datetime()")

    @abstractmethod
    def get_latest_bar_value(self, symbol, var):
        """
        Returns one of the Open, High, Low, Close, Volume or OI from the last bar.

        Parameters
        ----------
        symbol : string
            The symbol of the financial asset.
        var : string
            The name of the variable of the data DataFrame
        """
        raise NotImplementedError("Should implement .get_latest_bar_value()")

    @abstractmethod
    def get_latest_bars_values(self, symbol, var, N=1):
        """
        Returns the last N bar values from the lastest_symbol list, or N-k if less available.

        Parameters
        ----------
        symbol : string
            The symbol of the financial asset.
        var : string
            The variable name to retrive from the data DataFrame
        N : int
            Number of bars to retrieve from.
        """
        raise NotImplementedError("Should implement .get_latest_bar_values()")

    @abstractmethod
    def update_bars(self):
        """
        Pushes the latest bars to the bars_queue for each symbol in a tuple OHLCVI format: (datetime, open, high, low, close, volume, open interest).
        """
        raise NotImplementedError("Should implement .update_bars()")


