FincLab
=======

Author: Peter Lee

The FincLab project is designed to back-test investment strategies in several equity markets.

The project comprises of three main components, namely:

**FincLab.py** - fetches historical stock daily data of major stock exchanges in U.S., Australia and China via Yahoo! YQL.
**Back-testing** - a platform that prepares local data and evaluate investment strategies.
- Each quantitative model is implemented in an individual Jupyter notebook for easy access.
- Markdowns and visuals are removed from the Jupyter notebook when executing an investment strategy in back-testing.
- Result highlights and portfolio weights are emailed to the end-user.

**Real-time Trading** - for future developement, real-time trading integration with financial brokers.

## To-do list
- [ ] Get company info: symbol, name (CN/EN), industry. Store in a cross-sectional data table.
- [ ] Make yql_auth.py to solely return the URL strings. Use other classes to complete download tasks.
- [ ] Sequentially fetch histoical prices of all A shares using Pandas datareader.
- [ ] Add a counter in the fetching process to track number of requests sent within an hour.
- [ ] Automatically swtich from pandas datareader to my own yql downloader when exceeding the hourly requests limit.
- [ ] To include a pause command in .get() to avoid Yahoo penalty.
- [ ] To save responses in Pandas.DataFrame rather than json.
- [ ] To find out the naming rules for stock IDs in China. Use bruteforce to find out all of the IDs, including both listed and unlisted stocks.
- [ ] For all other stock exchanges, gather their IDs from the Excel sheet available on internet.
- [ ] Trace number of queries sent every hour and every day. Delay query to the following hour once approached the quota limit.
- [ ] Automate and repeat the process of finding stock IDs every month.
- [ ] Using the master list of stock IDs, download stock information from Yahoo! Finance.
- [ ] Store stock information using SQL Lite and MYSQL.
- [ ] Use IPython notebook as a back-testing platform to simulate investment portfolios and produce visuals.
- [ ] Construct an Alpha strategy.
- [ ] Implement real-time trading by following the strategy.
- [ ] Seek possible integration with online brokers, such as the Interactive Brokers' API.

## Updates
1 Oct 2015
- [X] Port application to server-au; Installed virtualenv using the following
  command:
```
  python3 -m virtualenv -p /usr/bin/python3 venv
```

27 Aug 2015
- [X] Improved the config class by reading all setting values as object properties.
- [X] To replace urllib and http.client as requests. Handle http exceptions using requests.

26 Aug 2015
- [X] Change settings file from json to configparser

25 Aug 2015
- [X] Load all config settings from settings.conf
```
    import src.config
    config = src.config.Config(settings_folder)
```

24 Aug 2015
- [X] Set out an API to receive YQL raw command, parse into an URL, and return results.
```
        response = YahooOAuth.get('YQL Command')
```
        
- [X] Get response from YQL URL

22 Aug 2015
- [X] Use logger to display debug messages. Logging levels:
 - DEBUG: Detailed information of interests when diagnosing problems.
 - INFO: Confirmation that things are working as expected.
 - WARNING: An indication of something unexpected happend (e.g., 'disk space low').
 - ERROR: The software has not been able to perform some functions.
 - CRITICAL: The program itself maybe unable to continue running.

21 Aug 2015
- [X] Change OAuth to web url based
- [X] Read/save consumer key and secret to a json file.
- [X] Auto refresh session token if it is close to expiry (less than 60 secs)

07 Aug 2015 - First version
- [X] Sign up Yahoo! API, and use OAuth and YQL to send 100,000 legitimate YQL Queries every day.

## FAQs

### Why choose Yahoo! YQL?
YQL has the advantage of high customizability. Theoretically it supports downloading most data from Yahoo! (e.g. news events and industry classifications), providing more flexibility than other APIs.
In addition, I can send more YQL queries after completing the authenticating process (20,000 requests per hour capped at 100,000 per day compared to 2000 per hour via public API). Note I can easily inflate request quota by rotating Yahoo accounts. Large usage quota is useful when using brute force to find possible symbols of all stocks in U.S.


## Notes
-------------------------------------
Download Historical Stock Information
-------------------------------------
On the first run, FincLab downloads historical daily price series up to the day before yesterday (three days ago). Such data fetching is completed via 'yahoo.finance.historicaldata' table.

More recent data are fetched on a daily basis from a different table. More variables are available in this method (e.g. market cap), however, such data are only available at the time when fetching occurs. The server is programmed to begin the fetching process after market closes.

The final dataset for quantitative analysis is formed by merging the hostircal data and the more recent dataset.

------------------------
China A Shares - Symbols
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
