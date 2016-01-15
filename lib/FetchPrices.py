"""
    Module: Fetch a stock's historical prices from Yahoo! API (Pandas_Datareader)
    Author: Peter Lee
    Date: Oct 2015

    Usage:
        >>>
        from FetchPrices import FetchPrices
        # To download historical prices for the 1st stock
        new_fetch = FetchPrices("600320.ss")
        new_fetch.get()
        # To download prices for the 2nd stock
        new_fetch.set_stock("600321.ss")
        new_fetch.get()

    Notes:
        FetchPrices.get() fetches historical data (since 1900) for the input
        stock from Yahoo! Finance using Pandas_DataReader.

        ------------------------
        China A Shares Symbols
        ------------------------
        Replace 'x' as a number.

        **A Shares**
        - Shanghai Exchange: 60xxxx
        - Shenzhen Exchange: 000xxx
        - Mid-small Exchange: 00xxxx

        **B Shares**
        - Shanghai Exchange: 900xxx
        - Shenzhen Exchange: 200xxx

        **创业板**
        - 创业板: 30xxxx
        - 创业板增发: 37xxxx
        - 创业板配股: 38xxxx

    Flow Chart:
        Input: Stock ID

        * Initialize variables:
            self.id = stock ID
            self.exchange = exchange ID
            self.id_exists = None
            self.new_entry = False
            self.last_check = None
            self.last_obs = None
            self.data = None

        * Check if default data folder exists
            - If no, create a new folder
        * Check if default stock list exist
            - If no, create a new file from an empty DataFrame
              The file has five variables:
                  0) [yahoo_id] Yahoo Stock ID
                  1) [id] Stock ID
                  2) [exchange] Exchange ID
                  3) [if_exists] If this stock actually exists when it was checked previously
                  4) [last_check] Date of the previous check
                  5) [last_obs] Date of the last observation in the prices

        -------------------- START: Check if an ID is valid --------------------
        1. Look up the stock ID in the stock list file
        2. Check if the ID has been recorded in the table
            - If recorded:
                self.new_entry = False
                Go to (3)
            - If NOT recorded:
                self.new_entry = True
                Go to END
        3. Read the content of [last_check]
            - self.last_check = Content of [last_check]
        4. Read the content of [if_exists]
            - self.id_exists = Content of [if_exists]
        4. Read the content of [last_obs]
            - self.last_obs = Content of [last_obs]
        -------------------- END --------------------

        -------------------- START: Download Historical Prices --------------------
        Let start date be 1900, Jan, 1
        Let end date be today.
        Using Yahoo! Finance API.
        0. Check if TODAY is a trading day
            - If True, say something like "Nothing to download as it is a
            non-trading day today!!" and go to END.
        1. If self.new_entry==True:
            Proceed to Download
        2. Check if self.last_obs<TODAY
            - If True:
                Go to (3)
            - If False:
                Go to END.
        3. If self.id_exists = True or (self.id_exists = False and self.last_check = more than 30 days ago):
            Proceed to Download (The second condition ensures that new IDs can be spotted at a 30-day interval)

        4. Download - Historical prices
            Nothing fancy here. Just download the series.
            - If there is data:
                self.data = data
            - If there is no data:
                self.data = None

        5. Save the data.(if self.data != None)
            - Check if self.new_entry==True:
                - If Yes, create a new file to store the data.
                - If No, find the gap between self.last_obs and the last
                observation. Update the existing data file with the new data.

        6. Check if the stock has been delisted for more than 1 day
            - If last observation of the data < TODAY - 1 day:
              the stock is regarded as temporarily delisted (new check in 30Days)
              self.id_exists = False
            - Otherwise
              self.id_exists = True

        7. Update self.last_check = TODAY
              self.last_obs = Last obs of the data

        8. Update the stock list file.
            - Check if self.new_entry==True:
                Create a new row in the data file.
            - Otherwise, modify the existing row with new information.
        -------------------- END --------------------


    Sources:
        Pandas-datareader
        http://pandas.pydata.org/pandas-docs/stable/remote_data.html

        User Pandas to find business days
        http://stackoverflow.com/questions/13019719/get-business-days-between-start-and-end-date-using-pandas

    To-do list:
        [ ]  There is an issue reading/saving datetime () from the files
        [ ] Disable download if today is not a business day.
        [ ] Automatically swtich from pandas datareader to my own yql
        downloader when exceeding the hourly requests limit.
        [ ] Add a clock-timer to notify the user when to use the program to download historical price data. e.g. after 4 pm China time.
        [ ] To make saving the stock_index file less frequent.
"""

import numpy as np
import pandas_datareader.data as wb
import datetime
import pandas as pd
import os
import logging
import logging.config
try:
    from lib.logger import FincLogger
except:
    from logger import FincLogger
from pandas.tseries.offsets import BDay


class FetchPrices():
    """
    Download price data of a stock and save to a database.
    If a stock is delisted / or Stock ID is invalid, the next check-up will be
    scheduled in 30 days.
    """
    def __init__(self, stock_id, logger=None,
                 data_folder="/Users/peter/Workspace/StockData/"):
        self.data_folder = data_folder

        # Initialize variables
        self.set_stock(stock_id)

        # Initiate a logger
        if logger is None:
            logging.config.fileConfig(
                '/Users/peter/Workspace/FincLab/settings/log.conf')
            self.logger = logging.getLogger('FincLab')
        else:
            logging.setLoggerClass(FincLogger)
            self.logger = logging.getLogger(__name__)

        # Create the data folder if not exist
        self.check_if_folder_exists()

        # Load stock list
        self.stock_index = self.read_stock_list()

    def get(self):
        """
        Fetch historical data for the stock.
        """
        self.logger.info("Now downloading historical data for stock: " + self.stock_id)

        today = pd.datetime.today()

        # Check if the Stock ID is valid
        self.check_valid()

        # Check if TODAY is a trading day
        if len(pd.date_range(today, today, freq=BDay())) == 1:
            self.logger.debug("Today is a business day.")
        else:
            self.logger.warning("Today is NOT a business day. I will not download historical data.")
            # return 1

        # Check if self.last_obs<TODAY
        if self.last_obs is None:
            self.logger.debug("self.last_obs" + " is None.")
        elif self.last_obs >= today:
            self.logger.warning("The last observation of the stock " + self.yahoo_id + " is TODAY, suggesting that the stock has been downloaded today. No more download for this stock.")
            return 1

        # Check if the ID actually exists, and that the last check was made
        # within 20 business days.
        if self.id_exists:
            self.logger.debug("The ID exists. Proceed to download.")
        elif self.last_check is None:
            self.logger.debug("self.last_check is None. Proceed to download.")
        elif self.last_check < today - BDay(20):
            self.logger.debug("The ID does not exist, but last check was made more than 20 days ago. Proceed to download.")
        else:
            self.logger.warning(self.yahoo_id + " does not exist and that the last check was made within 20 days. Downloading historical data is ABORTED.")
            return 1

        # Download historical prices
        """Fetch historical data from Yahoo! Finance.
        """
        start = datetime.datetime(1900, 1, 1)
        end = datetime.datetime.today()
        try:
            print("Downloading historical data for ID:", self.yahoo_id, "...")
            response = wb.DataReader(self.yahoo_id, 'yahoo', start, None)
            self.data = response
        except Exception as e:
            self.logger.info(str(e))
            self.logger.warning("Fetching data for ID: " + self.yahoo_id + " is unsuccessful.")
            self.data = None
        self.logger.debug("Historical prices has been saved to self.data")

        # Save the data
        # Create a new file to save the data.
        file_folder = self.data_folder + self.exchange_names[self.exchange.upper()] + "/"

        if self.data is None:
            self.logger.debug("The data is empty, and will not be saved.")

        elif self.new_entry or (not os.path.exists(file_folder + self.stock_id + '.xlsx')):

            if not os.path.exists(file_folder):
                self.logger.debug("The data folder is not found. Creating a new one.")
                os.makedirs(file_folder)
            else:
                self.logger.debug("The data folder exists. Now exporting data to a file.")

            self.save_data()

        else:
            # Load existing data
            self.load_data()

            # Merge with new data
            self.data = self.data_existing.merge(self.data, on=('Open', 'High', 'Low', 'Close', 'Volume', 'Adj Close'),
                                                 left_index=True, right_index=True, how='outer')

            self.save_data()

        # Check if the stock has been delisted for more than 1 day
        if self.data is not None:
            last_obs_of_data = self.data[self.data.index == max(self.data.index)].index.values[0]
            # however this var is numpy.datetime64; converting to datetime.datetime
            last_obs_of_data = pd.Timestamp(last_obs_of_data).to_pydatetime()

            if last_obs_of_data < today - BDay(1):
                self.id_exists = False
            else:
                self.id_exists = True

            self.last_obs = last_obs_of_data

        # Update self.last_check
        self.last_check = today

        # Update the stock list file
        self.logger.debug("Now updating the stock list file")
        new_row = [self.yahoo_id, self.stock_id, self.exchange, self.last_obs, self.id_exists, self.last_check]

        if self.new_entry:
            self.stock_index.loc[len(self.stock_index)] = new_row
        else:
            self.stock_index[self.stock_index.yahoo_id == self.yahoo_id] = new_row

    def set_stock(self, stock_id):
        """Change the current stock ID and initialize variables.
        """
        # Parse stock ID
        self.yahoo_id = stock_id
        if "." in stock_id:
            self.stock_id, self.exchange = stock_id.split(".")
        else:
            self.stock_id = stock_id
            self.exchange = "US"

        # Other variables
        self.id_exists = None
        self.new_entry = False
        self.last_check = None
        self.last_obs = None
        self.data = None
        self.data_existing = None

        self.exchange_names = {'SS': 'Shanghai',
                               'SZ': 'Shenzhen',
                               'AX': 'Australia',
                               'NZ': 'NewZealand',
                               'SG': 'Singapore',
                               'US': 'UnitedStates'}

    def load_data(self):
        """Load self.data_existing from a file/SQL
        """
        file_folder = self.data_folder + self.exchange_names[self.exchange.upper()] + "/"

        self.data_existing = pd.read_excel(file_folder + self.stock_id + '.xlxs',
                                           index_col=0)

    def save_data(self):
        """Save self.data to file/SQL
        """
        # Define folder names for different stock exchanges
        file_folder = self.data_folder + self.exchange_names[self.exchange.upper()] + "/"

        self.data.sort_index(ascending=True, inplace=True)

        self.data.to_excel(file_folder + self.stock_id + '.xlsx',
                           sheet_name='Sheet1',
                           index_label='Date',
                           merge_cells=False)

    def check_valid(self):
        """Check if the stock ID actually exists.
        """
        if self.yahoo_id in self.stock_index['yahoo_id']:
            self.logger.debug("The stock ID is found in the index table.")
            self.new_entry = False
            # Read the content of varaibles
            self.last_check = self.stock_index[self.stock_index["yahoo_id"] == self.yahoo_id]["last_check"]
            self.id_exists = self.stock_index[self.stock_index["yahoo_id"] == self.yahoo_id]["if_exists"]
            self.last_obs = datetime.datetime(self.stock_index[self.stock_index["yahoo_id"] == self.yahoo_id]["last_obs"])
        else:
            self.logger.debug("The stock ID cannot be found in the index table.")
            self.new_entry = True

    def read_stock_list(self):
        """Check if the default stock list file exists (index.xlsx).
        """
        if os.path.exists(self.data_folder + "index.xlsx"):
            self.logger.debug("Stock list file is found. Reading its content.")
            df_index = pd.read_excel(self.data_folder + "index.xlsx",
                                     index_col=0)
        else:
            self.logger.debug("Stock list file cannot be found. Creating an empty self.stock_index.")
            cols = ['yahoo_id', 'id', 'exchange', 'last_obs', 'if_exists', 'last_check']
            df_index = pd.DataFrame(columns=cols)
        return df_index

    def save_stock_list(self):
        """Save the stock list DataFrame to a file
        """
        self.stock_index.sort_index(ascending=True, inplace=True)

        self.stock_index.to_excel(self.data_folder + "index.xlsx",
                                  sheet_name='Sheet1',
                                  index_label='n',
                                  merge_cells=False)

    def check_if_folder_exists(self):
        """Check if the dafault dataset folder exists
        """
        if not os.path.exists(self.data_folder):
            self.logger.debug("Data folder does not exist. Creating a new folder.")
            os.makedirs(self.data_folder)


if __name__ == "__main__":
    # Test 1: To fetch a new stock
    fetch = FetchPrices("600288.ss")
#   fetch.get()

    # Test 2: To fetch a different stock
    fetch.set_stock("600320.ss")
#    fetch.get()

    # Test 3: To fetch a non-existing stock
    fetch.set_stock("600001.ss")
#    fetch.get()
    print("Tests completed!")

    # Download Shanghai stocks
    for x in np.arange(600000, 604000):
        fetch.set_stock(str(x) + ".SS")
        fetch.get()

        if np.mod(x, 100) == 0:
            # Save stock_index.xlsx per 100 downloads
            fetch.save_stock_list()
    fetch.save_stock_list()

    # Download Shenzhen stocks
    for x in np.arange(0, 1000):
        # To generate 6 digits stock ID
        str_x = str(x)
        while len(str_x) < 6:
            str_x = '0' + str_x

        fetch.set_stock(str_x + ".SZ")
        fetch.get()

        if np.mod(x, 100) == 0:
            # Save stock_index.xlsx per 100 downloads
            fetch.save_stock_list()
    fetch.save_stock_list()

    # Download 创业板 stocks
    for x in np.arange(300000, 302000):
        fetch.set_stock(str(x) + ".SZ")
        fetch.get()

        if np.mod(x, 100) == 0:
            # Save stock_index.xlsx per 100 downloads
            fetch.save_stock_list()
    fetch.save_stock_list()


