"""
    Module: Obtaining all of the ticker symbols associated with S&P 500
    Author: Peter Lee
    Date: Nov 2015

    Usage:
        >>>

    Notes:
        At the time of writing, there are actually 505 stock components of 500 companies in the S&P 500, due the reason that some companies have multiple share classes.
        The program scrapes the Wikipedia website using the Python requests and BeautifulSoup.
        If trading from the UK and wish to use UK domestic indices, obtain the list of FTSE100 companies traded on the LSE.
"""

import datetime
import bs4
import requests
import pandas as pd

import MySQLdb as mdb
from lib.load_config import load_config

import os
import logging


logger = logging.getLogger("FincLab.Parse.Wiki_SP500")


##
def parse_wiki_sp500():
    """
    Download and parse the Wikipedia list of S&P 500 constituents using requests and Beautifulsoup.
    Returns a list of tuples (to be uploaded to MySQL)
    """
    url = "http://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

    logging.info("Begin to parse S&P500 constituents from Wikipedia: {}".format(url))

    # Stores the current time, for the created_at record
    now = datetime.datetime.utcnow()

    # Use requests and BS4 to download / obtain the symbol table
    response = requests.get(url)
    soup = bs4.BeautifulSoup(response.text)

    # This selects the first table, using CSS Selector syntax and then ignores the header row ([1:])
    symbol_list = soup.select('table')[0].select('tr')[1:]

    # Obtain the symbol information for each row in the S&P 500 constituents table
    symbols = []
    for i, symbol in enumerate(symbol_list):
        tds = symbol.select('td')
        symbols.append(
            [
                tds[0].select('a')[0].text,  # Ticker
                'stock',
                tds[1].select('a')[0].text,  # Name
                tds[3].text,                 # Sector
                'USD', now, now
            ]
        )

    return symbols
##


def save_sp500_to_sql(data):
    """
    Insert the S&P 500 symbols into the MySQL database
    """
    db_config = load_config('MySQL_finclab')

    try:
        conn = mdb.Connection(**db_config)
        cursor = conn.cursor()

        cols = "ticker, instrument, name, sector, currency, created_date, last_updated_date"
        args = "%s, " * len(cols.split(','))
        args = args[:-2]
        query = """
                    INSERT INTO symbol ({cols}) VALUES ({args})
                """.format(cols=cols, args=args)

        # Using the MySQL connection, carry out an INSERT INTO for every symbol
        cursor.executemany(query, data)
        # print("Last updated row is:", cursor.lastrowid)
        conn.commit()
    except mdb.Error as e:
        print("Error:", e)
    finally:
        cursor.close()
        conn.close()


def save_sp500_to_file(data_folder):
    """ Save the list of S&P500 companies to a spreadsheet (.xlsx)

    Parameters
    ----------
        data_folder : string
            Relative (or aboslute) path to the data folder (i.e. "data/")
        data : list of lists
            The list of S&P500 stocks parsed from wikipedia.
            Format: [Ticker, 'stock', name, sector, 'USD', dt.now(), dt.now()]
    """

    # Fetch sp500 constituents
    symbols = parse_wiki_sp500()

    logger.info("The list of S&P500 constituents is successfully parsed.")

    df = pd.DataFrame(symbols, columns=['ticker', 'instrument', 'name', 'sector', 'currency', 'created_date', 'last_updated_date'])

    # logger.info("The first 20 of the stocks are: {}".format(df[['ticker', 'name']].head(20)))

    # Check if the default folder exists
    if not os.path.exists(data_folder):
        os.makedirs(data_folder)

    df.to_excel(os.path.join(data_folder, "sp500.xlsx"))


if __name__ == "__main__":
    symbols = parse_wiki_sp500()
    for i, symbol in enumerate(symbols):
        print(i + 1, ' '.join(str(x) for x in symbol))
    print("Begin to insert symbols to MySQL.")
    save_sp500_to_sql(symbols)
    print("{} symbols were successfully added.".format(len(symbols)))
