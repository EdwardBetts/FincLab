import os
import logging
import datetime as dt
import numpy as np
from dateutil import parser
import pandas as pd
from pandas_datareader import data as pdr
logger = logging.getLogger("Finclab.PrepareData")


class PrepareData():
    """
    The PrepareData class prepares the data for the FincLab engine using a number of criteria.

    For the up-start purpose, I only implemented the S&P 500 constituents criteria.

    Other possible criteria may include:
        - Large/small caps
        - High/low volatility
        - Other index constituents
    """

    def __init__(self, data_folder, index_names=None,
                 symbols=None,
                 start_date=dt.datetime(1990, 1, 1),
                 end_date=None):
        """
        Initialises the PrepareData class

        Parameters
        ----------
            data_folder : string
                Relative path to the data folder.

            index_names : string or a list of strings, default None
                To obtain the end-of-day data of all constituents from the index, just specify the name of the index.

            symbols : string a list of strings, default None
                Individual symbols

            start_date : dt.datetime()
                The start date of the dataset.

            end_date : dt.datetime()
                The end date of the dataset.
        """
        self.data_folder = data_folder
        if type(index_names) == str:
            self.index_names = [index_names]
        else:
            self.index_names = index_names

        if symbols is None:
            self.symbol_list = []
        elif type(symbols) == str:
            self.symbol_list = [symbols]
        else:
            self.symbol_list= symbols

        self.start_date = start_date

        self.end_date = end_date

        self.symbol_data = {} # list of dataframes

        self.logger = logging.getLogger("Finclab.PrepareData")

        self.update_data()

    def get_symbol_list(self):
        """
        Return the list of symbols
        """
        return self.symbol_list

    def update_data(self):
        """
        Prepare / update the data for the backtesting purpose.
        Flow charts:
            1. Formulate the list of stocks based on all criteria
            1. If data does not exist, download the data.
            2. If data is outdated, update the data
        """

        # Formulate the list of stocks based on all critiera
        if self.index_names is not None:
            self.get_index_constituents()

        # Check if data exists --> download from source if necessary
        for symbol in self.symbol_list:
            file_path = os.path.join(self.data_folder, symbol + ".xlsx")
            if not os.path.exists(file_path):
                self.logger.info("The data file for symbol {} does not exist, now beginning to download from the source.".format(symbol))
                self.symbol_data[symbol] = self.fetch_data(symbol)
            else:
                self.symbol_data[symbol] = pd.read_excel(file_path, parse_dates = True)

        # Check if data is outdated
        for symbol, df in self.symbol_data.items():
            last_date = df['Date'].values[-1]

            if self.end_date is None:
                end_date = dt.datetime.now()
                end_date = dt.datetime(end_date.year,
                    end_date.month,
                    end_date.day)
            else:
                end_date = self.end_date
            end_date = np.datetime64(end_date)

            if last_date < end_date:
                self.logger.info("The data file for symbol {} is outdated, more data will be downloaded from the source.".format(symbol))
                self.symbol_data[symbol] = self.fetch_data(symbol)

    def fetch_data(self, symbol):
        """
        Fetch end-of-day data for a symbol from the source, and save it to a datafile.
        """
        file_path = os.path.join(self.data_folder, symbol + ".xlsx")

        df = pdr.DataReader(name = symbol,
                            data_source = 'yahoo',
                            start = self.start_date,
                            end = self.end_date)

        df.to_excel(file_path)
        return df

    def get_index_constituents(self):
        """
        Obtain the list of constituents from the database. If database does not exist, obtain it from the source.
        """
        # Check if database exists
        folder = self.data_folder + "index_constituents"
        for index in self.index_names:
            file_path = os.path.join(folder, index + ".xlsx")
            if os.path.exists(file_path):
                self.logger.info("Data file for index {} is found. Begin to load the list of constituents from the existing data file.".format(index))
                df = pd.read_excel(file_path, parse_dates=True)
                self.symbol_list += list(df['ticker'].values)

        # Remove duplicate tickers from the list
        self.symbol_list = list(set(self.symbol_list))


if __name__=='__main__':
    logger = logging.getLogger("FincLab.Prepare")
    logger.setLevel(logging.DEBUG)
    prepare_data = PrepareData("data/", index_names = "sp500")


