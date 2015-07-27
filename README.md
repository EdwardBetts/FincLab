Project FincLab
==

FincLab is disigned for algorithmic trading. It consists of three major
components:

- Fetching data. Daily stock information in major stock exchanges (U.S.,
  Australia, and China) are downloaded from Yahoo! Finance.
- Back testing. A back-testing platform to explore investment strategies and to
  simulate investment returns using historical data.
- Real-time trading integration. Real-time trading integration with multiple
  brokers to enable investments in multiple continents.

# To-do list

[ ] Sign up Yahoo! API, and find a way to send 100,000 legitimate YQL Queries
every day.
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




