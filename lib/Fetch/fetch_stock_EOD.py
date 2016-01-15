"""
    Module: Fetch a stock's historical prices from Yahoo! API (Pandas_Datareader)

    1. First retrive the list of symbols from the "symbol" table in MySQL
    2. Download daily prices from Yahoo API

    Author: Peter Lee
    Date: Nov 2015

    Usage:
    There are two methods to obtain End of Day prices from Yahoo:
    1) fetchPricesYahooAPI(): Using the Yahoo .csv API to download data
    2) fetchPricesYahoo(): Using the Pandas data_reader to download data

    Notes:
        1. To gain high concurrency from the downloads, we can make use of the Python ScraPy library, which is built on the event-driven twisted framework.

"""

import datetime as dt
import warnings
import MySQLdb as mdb
import requests
import pandas_datareader
from lib.load_config import load_config


def obtain_tickers():
    """
    Obtains a list of the ticker symbols in the database.

    return:
    A list of tuples - [(id, ticker)]
    """

    db_config = load_config('MySQL_finclab')

    try:
        conn = mdb.Connection(**db_config)
        cursor = conn.cursor()

        query = """
                    SELECT id, ticker FROM symbol
                """

        cursor.execute(query)
        data = cursor.fetchall()
        return [(d[0], d[1]) for d in data]

    except mdb.Error as e:
        print("Error:", e)
    finally:
        cursor.close()
        conn.close()


def fetch_prices_from_yahoo(
        ticker, start_date=(1900, 1, 1),
        end_date=dt.date.today().timetuple()[0:3]):
    """
    Obtains data from yahoo finance via Pandas Data_reader.

    parameters:
    ticker: Yahoo Finance ticker symbol, e.g. "GOOG" for Google.
    start_date: Start date in (YYYY, M, D) format
    end_date: End date in (YYYY, M, D) format

    return:
    prices: a DataFrame
    """
    df = pandas_datareader.Data_reader('ticker', 'yahoo', dt.datetime(start_date[0], start_date[1], start_date[2]), dt.datetime(end_date[0], end_date[1], end_date[2]))

    return df


def fetch_prices_from_yahooAPI(
        ticker, start_date=(1900, 1, 1),
        end_date=dt.date.today().timetuple()[0:3]):
    """
    Obtains data from Yahoo Finance CSV API for a given ticker.

    parameters:
    ticker - Yahoo Finance ticker symbol, e.g. "GOOG" for Google.
    start_date - Start date in (YYYY, M, D) format
    end_date - End date in (YYYY, M, D) format

    return:
    prices: a list of tuples []
    """

    # Construct the Yahoo URL with the correct integer query parameters for start and end dates. Note that some parameters are zero-bsed.
    tickerTuple = (
        ticker,
        start_date[1] - 1,
        start_date[2],
        start_date[0],
        end_date[1] - 1,
        end_date[2],
        end_date[0]
    )

    yahooURL = "http://ichart.finance.yahoo.com/table.csv"
    yahooURL += "?s={}&a={}&b={}&c={}&d={}&e={}&f={}"
    yahooURL = yahooURL.format(*tickerTuple)

    # Try connecting to Yahoo Finance and obtaining the data.
    # On failure, print an error message.
    try:
        yf_data = requests.get(yahooURL).text.split("\n")[1:-1]
        prices = []
        for y in yf_data:
            p = y.strip().split(',')
            prices.append(
                (dt.datetime.strptime(p[0], '%Y-%m-%d'),
                 p[1], p[2], p[3], p[4], p[5], p[6])
            )
    except Exception as e:
        print("Errors: Cannot download Yahoo data - {}".format(e))

    return prices


def insert_data_to_db(vendorID, symbolID, data):
    """
    Takes a list of tuples of daily data and adds it to the MySQL database. Appends the vendor ID and symbol ID to the data.

    parameters:
    vendorID: data vendor
    symbolID: stock ticker
    data: List of tuples of the OHLC data plus adj_close and volume
    """
    # MySQL config
    db_config = load_config("MySQL_finclab")

    # Create the time now
    now = dt.datetime.utcnow()

    # Amend the data to include the vendor ID and symbol ID
    daily_data = [(vendorID, symbolID, d[0], now, now, d[1], d[2], d[3], d[4], d[5], d[6]) for d in data]

    cols = "data_vendor_id, symbol_id, price_date, created_date, last_updated_date, open_price, high_price, low_price, close_price, volume, adj_close_price"

    args = "%s, " * len(cols.split(','))
    args = args[:-2]
    query = """
                INSERT INTO daily_price ({cols}) VALUES ({args})
            """.format(cols=cols, args=args)

    try:
        conn = mdb.Connection(**db_config)
        cursor = conn.cursor()

        cursor.executemany(query, daily_data)
        conn.commit()

    except mdb.Error as e:
        print("Error:", e)

    finally:
        cursor.close()
        conn.close()


if __name__ == "__main__":
    # This ignores the warnings regarding Data Truncation from the Yahoo precision to Decimal(19, 4) datatypes
    warnings.filterwarnings('ignore')

    # Loop over the tickers and insert the daily historical data into the database
    tickers = obtain_tickers()
    len_tickers = len(tickers)
    for i, t in enumerate(tickers):
        print("Adding data for {}: {} out of {}.".format(t[1], i + 1, len_tickers))
        yfData = fetch_prices_from_yahoo(t[1])
        insert_data_to_db('1', t[0], yfData)
    print("Successfully added Yahoo Finance price data to DB")
