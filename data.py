"""
Class: Data Handler

Author: Peter Lee
Date created: 2016-Jan-14

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

Abstract Base Class (ABC)
-------------------------
We make use of the __metaclass__ property to let Python know that this is an ABC. In addition, we use the @abstractmethod decorator to let Python know that the method will be overriden in subclasses (this is identical to a pure virtual method in C++).
"""


from abc import ABCMeta, abstractmethod
import os
import os.path
import pandas as pd
import numpy as np
import queue

from event import MarketEvent


class DataHandler(object):
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


class HistoricDataHandler(DataHandler):
    """
    The HistoricDataHandler imports a number of data formats, including Excel files (both .xls and .xlsx), comma-separated variables (CSV) files and Stata formats (.dta). It searches for the datafile begins with the requested "symbol" (e.g., "GOOG.xlsx") in the data_folder, and provides an interface for other system components to obtain historical bars in a manner that is identical to live trading interface.
    Assume that the data is taken from Yahoo, and its format will be respected.
    """

    def __init__(self, event_queue, symbol_list, data_folder="/Users/peter/Work/FinanceData/Stock/US/"):
        """
        Initialises by requesting the event queue, location of the data files and a list of symbols.

        It will be assumed that all files are of the form 'symbol.xxx', where symbol is a string in the list, and xxx is the supported file extensions, including .xls, .xlsx, .dta and .csv.

        Parameters
        ----------
        events : The Event queue
        csv_folder : path to the data files
        symbol_list : A list of symbol strings
        """
        self.event_queue = event_queue
        self.data_folder = data_folder
        self.symbol_list = symbol_list

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.is_running = True

        self._load_data_files()

    def _load_data_csv(self, symbol, file_path):
        """ Load .csv data files """
        # Load the data file with no header information, indexed on date
        self.symbol_data[symbol] = pd.read_csv(
            file_path,
            header=0,
            index_col=0,
            parse_dates=True,
            names=['datetime', 'open', 'high', 'low', 'close', 'volume', 'adj_close']
        ).sort_index()

    def _load_data_excel(self, symbol, file_path):
        """ Load .xls and .xlsx data files """
        # Load the data file with no header information, indexed on date
        self.symbol_data[symbol] = pd.read_excel(
            file_path,
            header=0,
            index_col=0,
            parse_dates=True,
            names=['datetime', 'open', 'high', 'low', 'close', 'volume', 'adj_close']
        ).sort()

    def _load_data_stata(self, symbol, file_path):
        """ Load .dta data files """
        # Load the data file with no header information, indexed on date
        self.symbol_data[symbol] = pd.read_stata(
            file_path,
            header=0,
            index_col=0,
            parse_dates=True,
            names=['datetime', 'open', 'high', 'low', 'close', 'volume', 'adj_close']
        ).sort()

    def _load_data_files(self):
        """
        Load the data files from the data directory and convert them into pandas DataFrames within a symbol dictionary.

        Assume that the data is taken from Yahoo, and its format will be respected.
        """
        comb_index = None
        # Load symbol data and re-construct index
        for symbol in self.symbol_list:
            if os.path.exists(os.path.join(self.data_folder, "{}.xlsx".format(symbol))):
                self._load_data_excel(symbol, os.path.join(self.data_folder, "{}.xlsx".format(symbol)))
            if os.path.exists(os.path.join(self.data_folder, "{}.xls".format(symbol))):
                self._load_data_excel(symbol, os.path.join(self.data_folder, "{}.xls".format(symbol)))
            if os.path.exists(os.path.join(self.data_folder, "{}.dta".format(symbol))):
                self._load_data_stata(symbol, os.path.join(self.data_folder, "{}.dta".format(symbol)))
            if os.path.exists(os.path.join(self.data_folder, "{}.csv".format(symbol))):
                self._load_data_csv(symbol, os.path.join(self.data_folder, "{}.csv".format(symbol)))

            # Set the latest symbol-data to an empty list
            self.latest_symbol_data[symbol] = []

            # Combine the index and pad forward the values
            if comb_index is None:
                comb_index = self.symbol_data[symbol].index
            else:
                comb_index.union(self.symbol_data[symbol].index)

        # Reindex all dataframes
        for symbol in self.symbol_list:
            self.symbol_data[symbol] = self.symbol_data[symbol].\
                reindex(index=comb_index, method='ffill').iterrows()

    def _get_new_bar(self, symbol):
        """ Yields a bar from the data feed in the sequential (timely) order. """
        for bar in self.symbol_data[symbol]:
            yield bar

    def get_latest_bar(self, symbol):
        """
        Returns the last bar from the latest_symbol_data list.
        """
        try:
            series_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return series_list[-1]

    def get_latest_bars(self, symbol, N=1):
        """
        Returns the last N bars from the latest_symbol list.
        """
        try:
            series_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return series_list[-N:]

    def get_latest_bar_datetime(self, symbol):
        """
        Returns a datetime object for the last bar to represent the "last market price".
        """
        try:
            series_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return series_list[-1][0]

    def get_latest_bar_value(self, symbol, variable):
        """
        Returns the value of one variable, i.e., Open, High, Low, Close, Volume or Open Interests from the pandas series object.

        Parameters
        ----------
        symbol : string
            The symbol of the asset.
        variable : string
            The name of the variable (column) to retrieve

        Returns
        -------
        The value of the varialbe from the latest bar.

        Notes
        -----
        The Python getattr function queries an object to see if a particular attribute exists on an object. Thus we can pass a string such as "open" or "close" to .getattr and obtain the value direct from the bar, and making the method more flexible (as such the data format could be more flexible, i.e., more columns than needed, and avoids to write methods to retrieve different variables, i.e., .get_adj_close_from_bar()
        """
        try:
            series_list = self.latest_symbol_data[symbol]
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return getattr(series_list[-1][1], variable)

    def get_latest_bars_values(self, symbol, variable, periods=1):
        """
        Returns the values of one variable, i.e., Open, High, Low, Close, Volume or Open Interests of the last N periods from the pandas series object.

        Parameters
        ----------
        symbol : string
            The symbol of the asset.
        variable : string
            The name of the variable (column) to retrieve
        periods : int
            Number of periods

        Returns
        -------
        Numpy array of values.
       """
        try:
            series_list = self.get_latest_bars(symbol, periods)
        except KeyError:
            print("That symbol is not available in the historical data set.")
            raise
        else:
            return np.array([getattr(s[1], variable) for s in series_list])

    def update_bars(self):
        """
        Pushes the latest bar to the latest_symbol_data structure for all symbols in the symbol list.

        It simply generates a MarketEvent that gets added to the queue as it appends the latest bars to the latest_symbol_data dictionary
        """
        for symbol in self.symbol_list:
            try:
                bar = next(self._get_new_bar(symbol))
            except StopIteration:
                self.is_running = False
            else:
                if bar is not None:
                    self.latest_symbol_data[symbol].append(bar)
                    date_time = bar[0]
                    market_event = MarketEvent(date_time)
                    # Put in a MarketEvent into the event queue
                    self.event_queue.put(market_event)


if __name__ == "__main__":
    print("Debugging...")
    data_handler = HistoricDataHandler(
        event_queue=queue.Queue(),
        symbol_list=['AAPL']
    )

