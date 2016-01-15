""" Module: Fetch Futures Prices using Quandl

    Peter Lee
    2016-Jan-13

    Usage:
        Use method .downloadContractFromQuandl() to fetch all contracts for a particular symbol (e.g. "ES") between a start year and a end year.
        Make sure the default data folder exists (e.g., ~/Work/FinanceData/Futures/).
        The API is limited to 500 calls per day (using one signed-up account with Quandl). I think it is Quite possible to increase the number of calls per day by registering multiple accounts and rotate them.

    Note:
"""


import datetime as dt
import requests
import Quandl
from lib.load_config import load_config


def construct_futures_symbols(
        symbol, start_year=1900, end_year=dt.date.today().timetuple()[0]):
    """
    Generate the list of futures symbols to download
    given a particular symbol and timeperiod.
    """
    futures = []
    # March, June, September and December delivery codes
    months = 'HMUZ'
    for y in range(start_year, end_year + 1):
        for m in months:
            futures.append("{}{}{}".format(symbol, m, y))
    return futures


def download_one_futures_from_quandlAPI(contract, data_folder='~/Work/FinanceData/Futures/'):
    """
    Download an individual futures contract from Quandl and then store it to disk in the dir directory using Quandl HTTP .csv API.

    An auth_token is required, which is obtained from the Quandl upon sign-up.
    """
    # Load configuration - API key
    apiConfig = load_config('Quandl')

    # Construct the API call
    api_call = "http://www.quandl.com/api/v1/datasets/"
    api_call += "OFDP/FUTURE_{}.csv".format(contract)

    params = "?auth_token={}&sort_order=asc".format(apiConfig["api_key"])

    full_url = "".join([api_call, params])

    # Download the data from Quandl
    data = requests.get(full_url).text

    # Store the data to disk
    f = open("{folder}/{file}.csv".format(folder=data_folder, file=contract), 'w')
    f.write(data)
    f.close()


def download_one_futures_from_quandl(contract, data_folder='~/Work/FinanceData/Futures/'):
    """
    Download an individual futures contract from Quandl and then store it to disk in the dir directory. An auth_token is required, which is obtained from the Quandl upon sign-up.

    The quandl library is required:
        pip install quandl

    """
    # Load configuration - API key
    api_config = load_config('Quandl')

    # Initial download using Quandl library
    df = Quandl.get("OFDP/FUTURE_{}".format(api_config['api_key']),
                    returns="pandas")

    # Store the data to disk
    df.to_csv("{folder}/{file}.csv".format(folder=data_folder, file=contract), 'w')


def download_futures_from_quandl(symbol, start_year=1990, end_year=dt.datetime.today().timetuple()[0]):
    """ Download all contracts for a particular symbol between a StartYear and EndYear
    """
    # Generate contract symbols
    contracts = construct_futures_symbols(symbol, start_year, end_year)
    for c in contracts:
        print("Downloading contract: {}".format(c))
        download_one_futures_from_quandl(c)


if __name__ == '__main__':
    download_futures_from_quandl('ES', startYear=2014)
