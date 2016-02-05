import os.path
import pandas as pd
import numpy as np
import queue
import logging
from event import MarketEvent
from feeder.ABC import ABC as DataABC
from dateutil import parser
import datetime as dt


class HistoricData(DataABC):
    """
    The HistoricDataHandler imports a number of data formats, including Excel files (both .xls and .xlsx), comma-separated variables (CSV) files and Stata formats (.dta). It searches for the datafile begins with the requested "symbol" (e.g., "GOOG.xlsx") in the data_folder, and provides an interface for other system components to obtain historical bars in a manner that is identical to live trading interface.
    Assume that the data is taken from Yahoo, and its format will be respected.
    """

    def __init__(self, config, event_queue, symbol_list):
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
        self.config = config
        self.symbol_list = symbol_list

        self.symbol_data = {}
        self.latest_symbol_data = {}
        self.is_running = True

        self.data_folder = self.config['data']['data_folder']

        # Parse dates
        self.start_date = parser.parse(self.config['data']['start_date'])
        end_date = self.config['data']['end_date']
        if end_date.upper() == "NONE":
            dt_now = dt.datetime.now()
            self.end_date = dt.datetime(dt_now.year, dt_now.month, dt_now.day)
        else:
            self.end_date = parser.parse(self.end_date)

        self.logger = logging.getLogger("FincLab.HistData")
        self.logger.propagate = True

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
        ).sort_index()

    def _load_data_stata(self, symbol, file_path):
        """ Load .dta data files """
        # Load the data file with no header information, indexed on date
        self.symbol_data[symbol] = pd.read_stata(
            file_path,
            header=0,
            index_col=0,
            parse_dates=True,
            names=['datetime', 'open', 'high', 'low', 'close', 'volume', 'adj_close']
        ).sort_index()

    def _load_data_files(self):
        """
        Load the data files from the data directory and convert them into pandas DataFrames within a symbol dictionary.

        Assume that the data is taken from Yahoo, and its format will be respected.
        """
        comb_index = None

        # Load symbol data and re-construct index
        for symbol in self.symbol_list:
            self.logger.debug("[Status]loading_data:{}".format(symbol))
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

        # Update the max observation number
            self.first_obs = comb_index[0]
            self.last_obs = comb_index[-1]

        # Reindex all dataframes
        for symbol in self.symbol_list:
            df = self.symbol_data[symbol].reindex(index=comb_index, method='ffill')
            self.symbol_data[symbol] = df.iterrows()

    def _get_new_bar(self, symbol):
        """ Yields a bar from the data feed in the sequential (timely) order. """
        for bar in self.symbol_data[symbol]:
            current = (bar[0] - self.first_obs).days
            total = (self.last_obs - self.first_obs).days + 1
            self.logger.info("[Progress]{},{}".format(current, total))
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
    data_handler = HistoricData(
        event_queue=queue.Queue(),
        symbol_list=['AAPL']
    )

