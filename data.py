"""
    Data Handler

    Peter Lee
    Last update: 2016-Jan-14

    The DataHandler is an abstract base class (ABC), which means that it is impossible to instantiate an instance directly. Only subclasses may be instantiated. The rationale for this is that the ABC provides an interface that all inherited DataHandler subclasses must adhere to, thereby ensuring compatibility with other classes that communicate with them.

    There are 6 fundamental methods:
     1. get_latest_bar()
     2. get_latest_bars() - It is used to retrieve a recent subset of the historical trading bars from a stored list of such bars. These methods come in handy within the Strategy and Portfolio classes, due to the need to constantly be aware of current market prices and volumes.
     3. get_latest_bar_datetime() - it returns a Python datetime object that reprsents the timestamp of the bar (e.g., a date for daily bars or a minute-resolution object for minutely bars)
     4. get_latest_bar_value()
     5. get_latest_bar_values() - It is a convinient method used to retrive individual values from a particular bar, or list of bars. For instance, it is often the case that a strategy is only interested in closing prices. In this instance, we can use these methods to rewturn a list of floating point values representing the closing prices of previous bars, rather than having to obtain it from the list of bar objects. This generally increaess efficiency of strategies that utilise a "lookback window" or "rolling window", such as those involving regressions.
     6. update_bars() - It provides a "drip feed" mechanism for placing bar information on a new data structure that strictly prohibits lookahead bias. This is one of the key differences between an event-driven backtesting system and one based on vectorisation.

    Note:
    One of the goals of an event-driven trading system is to minimise duplication of code between the   backtesting element and the live execution element. Ideally, it would be optimal to utilise the same signal generation methodology and portoflio management components for both historical testing and live trading.

    In order for this to work, the Strategy objecct (which generates the Signals), and the Portfolio object (which provides Orders based on them), must utilise an identical interface to a market feed for both historic and live running.

    This motivates the concept of a class hierachy based on a DataHandler object, which gives all subclasses an interface for providing market data to the remaining components within the system. In this way, any subclass data handler can be "swapped out", without affecting strategy or portfolio calculation.

    Specific example subclasses, could include:

 - HistoricCSVDataHandler
 - QuandlDataHandler
 - SecuritiesMasterDataHandler
 - InteractiveBrokersMarketFeedDataHandler
 - and etc.

    # Abstract Base Class (ABC)
    We make use of the __metaclass__ property to let Python know that this is an ABC. In addition, we use the @abstractmethod decorator to let Python know that the method will be overriden in subclasses (this is identical to a pure virtual method in C++).
"""


from abc import ABCMeta, abstractmethod
import os
import os.path
import pandas as pd
import numpy as np
import datetime as dt

from event import MarketEvent


class DataHandler(object):
    """
    DataHandler is an abstract base class (ABC) providing an interface for all inherited data handlers (both live and historic).

    The goal of a (derived) DataHandler object is to output a generated set of bars (OHLCVI) for each symbol requested.

    This will replicate how a live strategy would function as current market data would be sent "down the pipe". Thus, a historic and live system will be treated identically by the rest of the backtesting engine.
    """

    __metaclass__ = ABCMeta

    @abstractmethod
    def get_lastest_bar(self, symbol):
        """
        Returns the last bar updated.
        """
        raise NotImplementedError("Should implement .get_latest_bar()")

    @abstractmethod
    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars updated.
        """
        raise NotImplementedError("Should implement .get_latest_bars()")

    @abstractmethod
    def get_latest_bar_datetime(self, symbol):
        """
        Returns a Python datetime object for the last bar.
        """
        raise NotImplementedError("Should implement .get_latest_bar_datetime()")

    @abstractmethod
    def get_latest_bar_value(self, symbol, val_type):
        """
        Returns one of the Open, High, Low, Close, Volume or OI from the last bar.
        """
        raise NotImplementedError("Should implement .get_latest_bar_value()")

    @abstractmethod
    def get_latest_var_values(self, symbol, val_type, N=1):
        """
        Returns the last N bar values from the lastest_symbol list, or N-k if less available.
        """
        raise NotImplementedError("Should implement .get_latest_bar_values()")

    @abstractmethod
    def update_bars(self):
        """
        Pushes the latest bars to the bars_queue for each symbol in a tuple OHLCVI format: (datetime, open, high, low, close, volume, open interest).
        """
        raise NotImplementedError("Should implement .update_bars()")


class HistoricCSVDataHandler(DataHandler):
    """
    The *HistoricCSVDataHandler* is a simple mechanism, that of importing comma-separated variable (CSV) files. This will allow us to focus on the mechanics of creating the DataHandler, rather than be concerned with the "boilerplate" code of connecting to a database and using SQL queries to grab data.

    It is designed to read CSV files for each requested symbol from disk and provide an interface to obtain the "latest" bAR IN a manner identical to a live trading interface.
    """

    def __init__(self, events, csv_folder, symbol_list):
        """
        Initialises by requesting the location of the CSV files and a list of symbols.

        It will be assumed that all files are of the form 'symbol.csv', where symbol is a string in the list.

        Parameters:
            events - The Event queue
            csv_folder - Absolute directory to the CSV files
            symbol_list - A list of symbol strings

        """
        self.events = events
        self.csv_folder = csv_folder
        self.symbol_list = symbol_list

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.continue_backtest = True

        self._open_convert_csv_files()

    def _open_convert_csv_files(self):
        """
        opens the CSV files from the data directory, converting them into pandas DataFrames within a symbol dictionary.

        For this handler it will be assumed that the data is taken from Yahoo. Thus its format will be respected.
        """
        comb_index = None
        for s in self.symbol_list:
            # Load the CSV file with no header information, indexed on date
            self.symbol_data[s] = pd.read_csv(
                os.path.join(self.csv_folder, "{}.csv".format(s)),
                header=0,
                index_col=0,
                parse_dates=True,
                names=['datetime', 'open', 'high', 'low', 'close', 'volume', 'adj_close']
            ).sort()

            # Combine the index and pad forward the values
            if comb_index is None:
                comb_index = self.symbol_data[s].index
            else:
                comb_index.union(self.symbol_data[s].index)

            # Set the latest symbol-data to None
            self.latest_symbol_data[s] = []

        # Reindex the dataframe
        for s in self.symbol_list:
            self.symbol_data[s] = self.symbol_data[s].\
                reindex(index=comb_index, method='ffill').iterrows()

    def _get_new_bar(self, symbol):
        """
        Returns the latest bar from the data feed.

        The _get_new_bar() method creates a generator to provide a new bar. This means that subsequent calls to the method will yield a new bar until the end of the symbol data is reached.
        """
        for b in self.symbol_data[symbol]:
            yield b

    def get_latest_bar(self, symbol):
        """
        Returns the last bar from the latest_symbol list.

        The method simply provides a bar from the lastest_symbol_data structure.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1]

    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list.

        or N-k if less available.
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-N:]

    def get_latest_bar_datetime(self, symbol):
        """
        Returns a Python datetime object for the last bar.

        Queries the latest bar for a datetime object representing the "last market price".
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return bars_list[-1][0]

    def get_latest_bar_value(self, symbol, val_type):
        """
        Returns one of the:
            Open, High, Low, Close, Volume or OI values from the pandas Bar series object.

        Note:
            It makes use of the Python .getattr function, which queries an object to see if a particular attribute exists on an object.

            Thus we can pass a string such as "open" or "close" to .getattr and obtain the value direct from the bar, thus making the method more flexible (this stops us from having to write methods of the type .get_latest_bar_close etc.).
        """
        try:
            bars_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return getattr(bars_list[-1][1], val_type)

    def get_latest_bars_values(self, symbol, val_type, N=1):
        """
        Returns the last N bar values from the latest_symbol list, or N-k if less available.
        """
        try:
            bars_list = self.get_latest_bars(symbol, N)
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return np.array([getattr(b[1], val_type) for b in bars_list])

    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure for all symbols in the symbol list.

        It simply generates a MarketEvent that gets added to the queue as it appends the latest bars to the latest_symbol_data dictionary
        """
        for s in self.symbol_list:
            try:
                bar = next(self._get_new_bar(s))
            except StopIteration:
                self.continue_backtest = False
            else:
                if bar is not None:
                    self.latest_symbol_data[s].append(bar)
        self.events.put(MarketEvent())

