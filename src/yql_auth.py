"""
    Module: Yahoo! YQL Authenticator (2-legged)
    Author: Peter Lee (mr.peter.lee@hotmail.com)

    Usage:
        session = YahooOAuth(config=config, logger=logger)
        request_url = session.parse('YQL Command')

    Notes:
        Use this module to retreive authentication token and relevant strings
        to construct YQL request URLs.

    Sources:
        Two-legged YQL authentication
        https://developer.yahoo.com/forum/OAuth-General-Discussion-YDN-SDKs/OAuth-two-legged-documentation-omission-/1253773254000-104aac85-a511-3985-87b8-36f430730ca4/

        Good implementation of both two-legged and three-legged YQL authentication
        pip yql_oauth

        Python Logger
        https://docs.python.org/3/howto/logging.html#logging-basic-tutorial

"""
import random
import time
import base64
import urllib.request
import requests
import re
import logging
import logging.config
import http.client
import simplejson
import configparser
# My lib
try:
    from src.config import Config
except:
    from config import Config


class YahooOAuth(object):
    """
    Yahoo! two-legged authentication
    """
    def __init__(self, config=Config('/Users/peter/Workspace/FincLab/settings/'),
                 logger=None):
        """
        config: Initiatate from src.config
                Default is to use the first account in accounts.conf
        """
        self.acc_number = 0  # Default to use the first account from accounts.conf
        self.config = config
        self.acc_name = self.config.accounts.sections()[self.acc_number]

        # Initiate a logger
        if logger is None:
            logging.config.fileConfig('/Users/peter/Workspace/FincLab/settings/log.conf')
            self.logger = logging.getLogger('FincLab')
        else:
            self.logger = logger

        # Debug
        for index, acc in enumerate(self.config.accounts.sections()):
            for item in self.config.accounts[acc]:
                self.logger.debug(str(index) + acc + item)

        if self.config.accounts[self.acc_name].get('timestamp'):
            self.token_time = int(self.config.accounts[self.acc_name]['timestamp'])
        else:
            self.config.accounts[self.acc_name]['timestamp'] = '0'
            self.token_time = 0

        self.logger.debug('token_time is: ' + str(self.token_time))
        self.logger.debug('consumer secret is: ' + self.config.accounts[self.acc_name]['consumer_secret'])

        if not self.token_is_valid():
            self.refresh_access_token()

    def parse(self, yql):
        """Method to retreive user specified YQL command

        Learning resource: yos-social-python from github.com

        YQL Command to get historical data for a single stock:
            select * from yahoo.finance.historicaldata where symbol = "YHOO" and startDate = "2009-09-11" and endDate = "2010-03-10"
        """
        if not self.token_is_valid():
            self.refresh_access_token()

        # Convert YQL command to an URL
        opendatatables_url = 'store://datatables.org/alltableswithkeys'
        request_base = 'http://query.yahooapis.com/v1/public/yql'
        consumer_key = 'oauth_consumer_key=' + self.config.accounts[self.acc_name]['consumer_key']
        oauth_nonce = 'oauth_nonce=' + self.get_nonce()
        oauth_signature_method = 'oauth_signature_method=PLAINTEXT'
        oauth_signature = 'oauth_signature=' + self.config.accounts[self.acc_name]['consumer_secret'] + '%26' + self.config.accounts[self.acc_name]['oauth_token_secret']
        oauth_timestamp = 'oauth_timestamp=' + str(int(time.time()))
        oauth_version = 'oauth_version=1.0'
        request_oauth_token = 'oauth_token=' + self.config.accounts[self.acc_name]['oauth_token']
        request_q = urllib.parse.urlencode({'q': yql, 'format': 'json', 'env': opendatatables_url})

        self.logger.debug('REQUEST_Q:' + request_q)

        # Construct the request URL
        url = (request_base +
               '?' + consumer_key +
               '&' + oauth_nonce +
               '&' + oauth_signature_method +
               '&' + oauth_signature +
               '&' + oauth_timestamp +
               '&' + oauth_version +
               '&' + request_oauth_token +
               '&' + request_q)

        return url

    def refresh_access_token(self):
        """Refresh access token.
        """
        self.logger.info("Refresh access token.")

        self.logger.info("try to update time_nonce()")
        self.update_time_nonce()  # update timestamp & nonce
        self.logger.debug("now try to get some config info.")
        self.token_time = int(self.config.accounts[self.acc_name]['timestamp'])

        self.logger.debug("token_time: " + str(self.token_time))

        # Form auth url and parse results
        self.oauth_url = 'https://api.login.yahoo.com/oauth/v2/get_request_token?oauth_callback=oob'
        self.two_leg_oauth_url = (self.oauth_url +
                                  '&oauth_consumer_key=' + self.config.accounts[self.acc_name]['consumer_key'] +
                                  '&oauth_signature=' + self.config.accounts[self.acc_name]['consumer_secret'] + '%26' +
                                  '&oauth_timestamp=' + self.config.accounts[self.acc_name]['timestamp'] +
                                  '&oauth_nonce=' + self.config.accounts[self.acc_name]['nonce'] +
                                  '&oauth_signature_method=PLAINTEXT&oauth_version=1.0')

        self.token = self.url_request(self.two_leg_oauth_url)
        self.parse_token(self.token)

        # Save session token to file
        self.config.save_accounts()

    def token_is_valid(self):
        """ Check the validity of the token: 3600s
        """
        remain_time = 3600 - (time.time() - self.token_time)
        self.logger.debug("The token will be refreshed in {time:.2f} secs.".format(time=remain_time))
        if remain_time == 0:
            self.logger.debug("There are no previous authentication tokens. Now generating a new one.")
        elif remain_time < 60:  # 1 minute before it expires
            self.logger.debug("Token has expired.")
            return False
        else:
            self.logger.debug("Token is valid.")
            return True

    def parse_token(self, s):
        """Parse session token from the authentication url
        I don't need the xoauth_request_auth_url.
        I think that is what I would need to pass to the user
        if it was for a three-legged authentication.

        s : token
        """
        oauth_token = re.search('oauth_token\=.*?\&', s).group(0)[12:-1]
        oauth_token_secret = re.search('oauth_token_secret\=.*?\&', s).group(0)[len('oauth_token_secret='):-1]
        oauth_expires_in = re.search('oauth_expires_in\=.*?\&', s).group(0)[len('oauth_expires_in='):-1]

        self.config.accounts[self.acc_name]['oauth_token'] = oauth_token
        self.config.accounts[self.acc_name]['oauth_token_secret'] = oauth_token_secret
        self.config.accounts[self.acc_name]['ooauth_token_expires_in'] = oauth_expires_in

    def url_request(self, url):
        """Read the content from a url
        Returns the content in string
        """
        try:
            response = requests.get(url, timeout=None, proxies=None)
            return response.text
        except requests.exceptions as e:
            self.logger.warning("Http Error in reaching the YQL server.")
            self.logger.warning("Error code: " + e)
            return None

    def update_time_nonce(self):
        """Update two-leg authentication:
        - timestamp
        - nonce
        """
        self.config.accounts[self.acc_name]['timestamp'] = str(int(time.time()))
        self.config.accounts[self.acc_name]['nonce'] = self.get_nonce()

    def get_nonce(self):
        """Unique token generated for each request"""
        n = base64.b64encode(
            ''.join([str(random.randint(0, 9)) for i in range(24)]).encode('utf-8'))
        return str(n.decode('utf-8'))

if __name__ == '__main__':
    # Load program settings
    config = Config('/Users/peter/Workspace/FincLab/settings/')

    # Some testings
    config.set_default()
    yf = YahooOAuth(config=config)
    print(yf.parse('select * from yahoo.finance.historicaldata where symbol = "000058.sz" and startDate = "2015-08-26" and endDate = "2015-08-28"'))
    print('current time is: ',  time.time())
    print('Done!')

