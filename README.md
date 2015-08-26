Project FincLab
==

The main purpose of the FincLab project is to backtesting investment strategies on equity data.

*FincLab.py*: Fetches historical daily stock data of major stock exchanges in U.S., Australia and China using Yahoo! YQL.
- YQL has the advantage of high customizability, and theoretically can be used to download any data from Yahoo! (e.g. news events related to a company and industry classification). Other tools that utilises CSV api or Charts api cannot achieve this.
- I can send more frequent YQL queries by appropriately authenticating my requests (up to 100,000 requests per day). Large usage quota is useful to brute force the possible symbols of all stocks in U.S.

*Back-testing*: A back-testing platform to explore investment strategies and to simulate investment returns using historical data.
- Each quantitative model is implemented in individual IPython notebooks for visualisation.
- Markdowns and visuals are removed when an investment strategy is called by FincLab.
- Back-testing results and portfolio components are summarized and emailed to the end-user.

*Real-time Trading*: This part is left out for future developement - the real-time trading integration with multiple financial brokers to engage with trading in multiple markets.
- Real-time monitor prices of stocks in the portfolio. Send email to / call the end-user if extreme movements occur (e.g. price dropped from the local maximum by 5%).

## To-do list
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
26 Aug 2015
- [X] Change settings file from json to configparser

25 Aug 2015
- [X] Load all config settings from settings.conf
.. code:: python

    import src.config
    config = src.config.Config(settings_folder)

24 Aug 2015
- [X] Set out an API to receive YQL raw command, parse into an URL, and return results.
.. code:: python
        response = YahooOAuth.get('YQL Command')
        
- [X] Get response from YQL URL

22 Aug 2015
- [X] Use logger to display debug messages.
    Logging levels:
        - DEBUG: Detailed information of interests when diagnosing problems.
        - INFO: Confirmation that things are working as expected.
        - WARNING: An indication of something unexpected happend (e.g., 'disk space low').
        - ERROR: The software has not been able to perform some functions.
        - CRITICAL: The program itself maybe unable to continue running.

21 Aug 2015
- [X] Change OAuth to web url based
- [X] Read/save consumer key and secret to a json file.
- [X] Auto refresh session token if it is close to expiry (<60 secs)

07 Aug 2015 - First version
- [X] Sign up Yahoo! API, and use OAuth and YQL to send 100,000 legitimate YQL Queries every day.

## Notes
-------------------------------------
Download Historical Stock Information
-------------------------------------
On the first run, FincLab downloads historical daily price series up to the day before yesterday (three days ago). Such data fetching is completed via 'yahoo.finance.historicaldata' table. A sample YQL command is:
.. code: sql
    select * from yahoo.finance.historicaldata where symbol = "YHOO" and startDate = "2009-09-11" and endDate = "2010-03-10"

More recent data are fetched on a daily basis from a different table. More variables are available in this method (e.g. market cap), however, such data are only available at the time when fetching occurs. The server is programmed to begin the fetching process after market closes.

The final dataset for quantitative analysis is formed by merging the hostircal data and the more recent dataset.

