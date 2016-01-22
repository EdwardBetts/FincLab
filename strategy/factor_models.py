# Back-testing multi-factor models

# Program version: v0.1
# Last update: Nov-09-2015
# Author: Peter Lee

import numpy as np
import pandas as pd
from pandas import Series, DataFrame, Panel, datetime
from datetime import timedelta
import datetime
import os
##
# ==================== Environment Variables ====================
# Folder locations
folder = "/Users/peter/Workspace/FincLab/"                  # Location of the scripts
folder_output = "/Users/peter/Workspace/FincLab/strategies/outputs/"   # Location of the output files
folder_temp = "/Users/peter/Workspace/Temp/"                           # Where temporary files should be stored
folder_stock_data = "/Users/peter/Workspace/StockData/"                # Where the stock historical data are stored
folder_factors = "/Users/peter/Workspace/StockData/Factors/"           # Where the factor variables are stored
# Program settings
debug = True                                                           # True: To load only 10 files.
# ===============================================================
##
os.chdir(folder)

# Initial a logger
from lib.logger import SimpleLogger
import logging
import logging.config

logging.setLoggerClass(SimpleLogger)
logger = logging.getLogger("Alpha")  # the logger tracks the package/module hierarchy, and events are logged just from the logger name.
logger.propagate = False

# logger.debug('debug message')
# logger.info('info msg')
# logger.warning('warn msg')
# logger.error('error msg')
# logger.critical('critical msg')

# Initial Checks
folders = [folder, folder_output, folder_temp, folder_stock_data, folder_factors]
for path in folders:
    if not os.path.exists(path):
        raise ValueError(path + " does not exist!")

##
# -------------------- S1. Prepare Dataset --------------------
# Form a panel dataset comprising of all historical data
# from Shanghai and Shenzhen exchages
data_panel = None
for root, dirs, files in os.walk(folder_stock_data):
    if debug==True:
        # Limit the number of files to load to 10
        files = files[:4]

    data_dict = {}
    for file in files:
        if file.endswith('.xlsx') and file != "index.xlsx":
            logger.debug("Now loading " + root + '/' + file)
            stock_id, dump = file.split('.')
            data_temp = pd.read_excel(root + '/' + file)
            # Declare timeseries
            data_temp = data_temp.set_index('Date').tz_localize('Asia/Shanghai')
            data_dict[stock_id] = data_temp

data_panel = Panel(data_dict)  # Daily series

##
# Calculate return and cumulative return

# Non-trading stocks - The days that a stock is non-traded are excluded from the
# sample.
for item in data_panel.items:
    df_temp = data_panel.ix[item]
##
