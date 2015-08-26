Project FincLab
==

FincLab is disigned for algorithmic trading. It consists of three major
components:

- Fetching data. Daily stock information in major stock exchanges (U.S.,
  Australia, and China) are downloaded from Yahoo! Finance.
- Need to do customizable YQL search (rather than relying on pandas-datareader to load stock information, as the industry classification is important (and other stock news data).
- Back testing. A back-testing platform to explore investment strategies and to
  simulate investment returns using historical data.
- Real-time trading integration. Real-time trading integration with multiple
  brokers to enable investments in multiple continents.

# To-do list
[ ] To find out the naming rules for stock IDs in China. Use bruteforce to find
out all of the IDs, including both listed and unlisted stocks.
[ ] For all other stock exchanges, gather their IDs from the Excel sheet
available on internet. 
[ ] Trace number of queries sent every hour and every day. Delay query to the
following hour once approached the quota limit.
[ ] Automate and repeat the process of finding stock IDs every month.
[ ] Using the master list of stock IDs, download stock information from Yahoo!
Finance.
[ ] Store stock information using SQL Lite and MYSQL.
[ ] Use IPython notebook as a back-testing platform to simulate investment
portfolios and produce visuals.
[ ] Construct an Alpha strategy.
[ ] Implement real-time trading by following the strategy.
[ ] Seek possible integration with online brokers, such as the Interactive
Brokers' API.

# Updates
26 Aug 2015
[X] Change settings file from json to configparser

25 Aug 2015
[X] Load all config settings from settings.conf
    Usage: 
.. code:: python

    import src.config
    config = src.config.Config(settings_folder)

24 Aug 2015
[X] Set out an API to receive YQL raw command, parse into an URL, and return results.
        response = YahooOAuth.get('YQL Command')
[X] Get response from YQL URL

22 Aug 2015
[X] Use logger to display debug messages.
    Logging levels:
        - DEBUG: Detailed information of interests when diagnosing
        problems.
        - INFO: Confirmation that things are working as expected.
        - WARNING: An indication of something unexpected happend (e.g.,
        'disk space low').
        - ERROR: The software has not been able to perform some
        functions.
        - CRITICAL: The program itself maybe unable to continue
        running.

21 Aug 2015
[X] Change OAuth to web url based
[X] Read/save consumer key and secret to a json file.
[X] Auto refresh session token if it is close to expiry (<60 secs)

07 Aug 2015 - First version
[X] Sign up Yahoo! API, and use OAuth and YQL to send 100,000 legitimate YQL Queries
every day.



