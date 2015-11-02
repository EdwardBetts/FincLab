"""
    Module: Check if a stock ID exists, and update any out-dated items in the
    Data ID panel to keep information up-to-date.
    Author: Peter Lee (Oct 21 2015)

    Usage:
        # Load all config settings
        >>> import lib.config

    Note:
        Use this module to load configuration settings from a file.

        Format of data table:
            Variables: Exchange_ID, Stock_ID, If_Exists, Last_Check

    Flow Chart:
        Input: Stock ID
        1. Does ID exist in data table?
           Yes -> 2A
           No  -> 2B
        2A. Add a new Entry. Go to END.
        2B. Read date info. Was last check > 30 days?
            Yes -> 3A
            No  -> 3B
        3A. Check again. Go to END.
        3B. Go to END.
        END. Read result and return result.

    Sources:
"""


import pandas as pd
import os
import logging
import logging.config
import datetime
from pandas_datareader import data, wb
import pandas_datareader
try:
    from lib.logger import FincLogger
except:
    from logger import FincLogger


logging.setLoggerClass(FincLogger)
logger = logging.getLogger(__name__)
logger.debug("Fuck off")


class Check_Stock_ID(object):
    """
    Check if a stock ID exists by comparing to a data table.
    An algorithm is in place to ensure that the next check occurs every
    30-day to keep the data table up-to-date.
    """

    def __init__(self,
                 stock_id,
                 df_index,
                 logger=FincLogger):
        self.stock_id = stock_id
        self.df_index = df_index

        # Initiate a logger
        if logger is None:
            logging.config.fileConfig(
                '/Users/peter/Workspace/FincLab/settings/log.conf')
            self.logger = logging.getLogger('FincLab')
        else:
            logging.setLoggerClass(FincLogger)
            self.logger = logging.getLogger(__name__)

        # Does the ID exist in the table?
        self.update_id()

        self.logger.debug("Finished Initialisation.")

    def update_id(self, stock_id, df_index):
        """
        Check if the stock_id exists in the df_index
        """
        if stock_id in df_index['id']:
            self.logger.debug("The stock_id exists")
            return True
        else:
            self.logger.debug("The stock_id does not exist")
            self.add_new_row(stock_id, df_index)

    def add_new_row(self, stock_id, df_index):
        """
        If the stock_id does not exist, create a new row
        """
        # Parse the ID
        if "." in stock_id:
            code, exchange = stock_id.split(".")
        else:
            code = stock_id
            exchange = "US"

        if_ever_exists = self.check_if_ever_exists(stock_id)
        last_check = datetime.datetime.now().date()

        new_row = len(df_index)
        df_index.loc[new_row] =

    def check_if_ever_exists(stock_id):
        """
        True if the stock id exists by fetching historical data using Pandas_datareader
        False otherwise
        """
        try:
            response = pandas_datareader.data.DataReader(stock_id, 'yahoo',
                                                     datetime.datetime(1980,1,1),
                                                     None)
            return True
        except:
            return False


    def touch(self, path):
        """
        Create an empty file
        """
        with open(path, 'a'):
            os.utime(path, None)

if __name__ == "__main__":
    # check if the default dataset folder exists
    if not os.path.exists(self.data_folder):
        self.logger.debug("Create a new dataset folder.")
        os.makedirs(self.data_folder)

    # Check if the index data exists. Create one if not.
    # Read data_index
    data_folder='/Users/peter/Workspace/StockData/',
    if os.path.exists(data_folder + "index.csv"):
        print("Reading from index.csv")
        df_index = pd.read_csv(data_folder + "index.csv")
    else:
        print("Create an empty stock index file - index.csv.")
        vars = ['exchange', 'id', 'if_exists', 'last_check']
        df_index = pd.DataFrame(columns=vars)
        df_index.to_csv(data_folder + "index.csv")

    test = Check_Stock_ID(stock_id="000123.ss", df_index=df_index)
    print("Tests complete!")

