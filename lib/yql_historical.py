"""
    Module: Fetch Stock Historical Data via Yahoo YQL
    Author: Peter Lee (mr.peter.lee@hotmail.com)

    Usage:

    Notes:
        Fetch data from yahoo.finance.historicaldata table using
        user specified YQL queries.

    Sources:

"""
import requests
# My lib
try:
    from src.config import Config
    from src.yql_auth import YahooOAuth
except:
    from config import Config
    from yql_auth import YahooOAuth


class YQL_historical():
    """Fetch data from yahoo.finance.historicaldata table using YQL
    """
    def __init__(self, symbol):
        """
        symbol: Stock symbol
        """
        self.symbol = symbol

    def fetch(self):
        """Download data"""
     # Initiate a connection
        try:
            response = requests.get(url, timeout=None, proxies=None)
            return simplejson.loads(response.text)
        except requests.exceptions as e:
            self.logger.warning("Http Error in executing YQL: " + yql)
            self.logger.warning("Error code: " + e)
            return None

