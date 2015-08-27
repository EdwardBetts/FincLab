"""
    Module: Fetch historical stock prices
    Author: Peter Lee (mr.peter.lee@hotmail.com)

    Usage:
        fetch_historical()

    Notes:
        Sequentially fetch histoical prices of all A shares using Pandas
        datareader.
        Automatically swtich from pandas datareader to my own yql
        downloader when exceeding the hourly requests limit.

    Sources:
        Pandas-datareader
        http://pandas.pydata.org/pandas-docs/stable/remote_data.html


"""
from pandas_datareader import data, wb
import pandas_datareader
import datetime


class Fetch_historical():
    """
    """
    def __init__(self):
        pass

    def begin(self):
        """Fetch historical data from Yahoo! Finance
        """
        start = datetime.datetime(2015, 1, 1)
        end = datetime.datetime(2015, 1, 27)
        f = pandas_datareader.data.DataReader("000058.sz", 'yahoo', start, end=None)
        print(f)


class Symbols():
    """Naming rules for stock/options symbols.

    ------------------------
    China A SharesSymbols
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
    """

    def __init__(self):
        pass

    def get_Shanghai_A(self):
        """Return a list of possible symbols to try out
        Process:
            - Check if the company info data file exists
            - If yes, return the list from zero to the last of the existing companies plus 100
            - If no, return [0, 4000]
        """


if __name__ == "__main__":
    session1 = Fetch_historical()
    session1.begin()
    print("testing")

