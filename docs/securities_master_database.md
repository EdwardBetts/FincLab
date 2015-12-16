Securities Master Database
==

Author: Peter Lee

Date: 21 Nov 2015

Learning Material: Quantstart ebook Chapter 7

Def. Securities Master Database: An organisation-wide database that stores fundamental, pricing and transactional data for a variety of financial instruments across asset classes. Here are some of the intruments that might be of interest:

 - Equities
 - Equity options
 - Indices
 - Forex
 - Intrest rates
 - Futures
 - Commodities
 - Bonds - Government and Corporate
 - Derivatives - Caps, Floors and Swaps

Securities master databases often have teams of developers and data specialists ensuring high availability within a financial institution. While this is necessary in large companies, at retail level or in a small fund a securities master database can be far simpler. In fact, while large securities masters make use of expensive enterprise database and analysis systems, it is possile to use commodity open-source software to provide the same level of funtionality, assuming a well-optimised system.

## End of Day (EOD) Data
There are a number of services providing access for free via web-available APIs:

 - Yahoo Finance
 - Google Finance
 - QuantQuote: https://www.quantquote.com (S&P 500 EOD data only)
 - EOD Data: http://eoddata.com (requires registration)

#### Issue: Look-back period
How far in the past do we need to go with our data? The most common is **regime change**, which is often characterised by a new regulatory environment, periods of higher/lower volatility or longer-term trending markets.

For instance a long-term short-directional trend-following/momentum strategy would likely perform very well from 2000-2003 or 2007-2009. However, it would have had a tough time from 2003-2007 or 2009 to the present.

The rule of thumb is to obtain as much data as possible, especially for EOD data where storage is cheap. Just because the data exists in your security master, does not mean it must be utilised.

Other isses include:

 - Incorrect high/low prices
 - Survivorship bias

## Storage Formats

#### 1. Flat-file Storage
Flat-files often make use of the Comma-Separated Variable (CSV) format. 

The advantage of flt-files are their simplicity and ability to be heavily compressed for archiving or download.

The main disadvantage lie in their lack of query capability and poor performance for iteration across large datasets. **SQLite** and **Excel** mitigate some of these problems by providing certain querying capabilities.

#### 2. Document Stores/NoSQL
Document stores/NoSQL databases, while certainly not a new concept, have gained significant prominence in recent years due to their use at "web-scale" firms such as Google, Facebook and Twitter.

They differ substantially fro mRDBMS in that there is no concept of table schemas. Instead, there are collections and documents, which are the closest analogies to tables and records, respectively.

Some of the more popular stores include **MangoDB**, **Cassandra** and **CouchDB**.

Advantages: Mostly suited to fundamental or meta data, as they comes in many forms, such as corporate actions, earnings statements, SEC filings etc.

Disadvantages: Not well designed for time-series such as high-resolution pricing data.

#### 3. Relational Database Management Systems (RDBMS)
RDBMS makes use of the relational model to store data. It makes use of Structured Query Language (SQL) in order to perform complex data queries. Examples include Oracle, MySQL, SQLServer and PostgreSQL.

Advantages: Simplicity of installation, platform-independence, ease of querying, ease of integration with major backtest software and high-performance capabilities at large scale.

Disadvantages: Complexity of customisationa and difficulties of achieving said performance without underlying nowledge of how RDBMS data is stored.


## Historical Data Structure

The first task is to define our *entities*, which are elements of the financial data that will eventually map to tables in the database. For an equities master database, I foresee the following entities:

 - Exchanges - The ultimate source of the data
 - Vendor - Where the data point is obtained from
 - Instrument/Ticker - The ticker/symbol for the quity or index, along with corporate information of the underlying firm or fund.
 - Price - The actual prices
 - Corporate Actions - The list of all stock splits or dividend adjustments (this may lead to one or more tables), necessary for adjusting the pricing data.
 - National Holidays - To avoid mis-classifying trading holidays as missing data errors, it can be useful to store national holidays and cross-reference.

## Data Accuracy Evaluation

Historical pricing data from vendors is prone to many forms of error:

 - Corporate Actions - Incorrect handling of stock splits and dividend adjustments. One must be absolutely sure that the formulae have been implemented correctly.
 - Spikes - Pricing pionts that greatly exceed certain historical volatility levels - see *May Flash Crash* for a scary example. Spikes can also be caused by not taking into account stock splits when they do occur. *Spike Filter* scripts are used to notify traders of such situations.
 - OHLC Aggregation - Yahoo/Google is particular prone to 'bad tick aggregation' situations where smaller exchanges process small trades well above the 'main' exchange prices for the day, thus leading to over-inflated maxima/minima once aggregated. This is less an 'error' as such, but more of an issue to be wary of.
 - Missing Data - Missing data can be caused by lack of trades in a particular time period (common in second/minute resolution data of illiquid small-caps), by trading holidays or simply an error in the exchange system. Missind data can be *padded* (filled with the previous value), *interpolated* (linearly or otherwise) or ignored, depending upon the trading system.

Many of these errors rely on manual judgement in order to decide how to proceed. It is possible to automate the notification of such errors, but it is much harder to automate their solution.

## Automation
A production process, for instance, might automate the download all of the S&P 500 end-of-day prices as soon as they are published via a data vendor. It will then automatically run the aforementioned missing data and spike filtration scripts, alerting the trader via email, SMS, or some other form of notification. 

At this point any backtesting tools will automatically have access to recent data, without the trader having to lift a finger.

#### Data Availability
Once the data is automatically updated and residing in the RDBMS it is necessary to get it into the backtseting software. This process will be highly dependent upon how your database is installed and whether your trading system is local or remote.

One of the most important considerations is to minimise excessive Input/Output (I/O) as this can be extremely expensive both in terms of time and money. The best way to approach this problem is to only move data across a network connection that you need (via selective querying) or exporting and compressing the data.

Many RDBMS support **replication** technology, which allows a database to be cloned onto another remote system, usually with a degree of latency. Depending upon your setup and data quantity this may only be on the order of minutes or seconds. A simple approach is to replicate a remote database onto a local desktop. However, be warned that synchronisation issues are common and time consuming to fix.


# Installation


## Configuring MySQL
After installation of MySql server, create a new *database* and a *user* to interact with it. First to log on as root:
```
mysql -u root -p
```
Then create the database, tables, user. User = 'sec_user' with reduced permission.
```
CREATE DATABASE securities_master;
USE securities_master;
CREATE USER 'sec_user'@'localhost' IDENTIFIED BY 'FincLab2015';
GRANT ALL PRIVILEGES on securities_master.* TO 'sec_user'@'localhost';
FLUSH PRIVILEGES;
```

## Schema Design for EOD Equities
We are ready to construct the necessary tables to hold our financial data. For a simple, straightforward equities master we will create four tables:

 - Exchange - The exchange table lists the exchanges we wish to obtain equities pricing information from. In this instance, it will almost exclusively be the New York Stock Exchange (NYSE), and the National Association of Securities Dealers Automated Quotations (NASDAQ), plus Shanghai, Shenzhen exchanges.
 - DataVendor - This table lists informatoin about historical pricing data vendors. We will be using Yahoo Finance to source the EOD data. By introducing this table, we make it straightforward to add more vendors if necessary, such as Google Finance.
 - Symbol - The symbol table stores the list of ticker symbols and company information. Right now we will be avoiding issues such as differing share classes and multiple symbol names.
 - DailyPrice - This table stores the daily pricing information for each security. It can become very large if many securities are added. Hence it is necessary to optimise it for performance.

#### InnoDB v.s. MyISAM
MySQL allows you to customise how the data is stored in an underlying *storage engine*. The two primary contenders in MySQL are MyISAM and InnoDB.

**MyISAM** is more useful for fast reading (such as querying across large amounts of price information), but it doesn't support transactions (necessary to fully rollback a multi-step operation that fails mid way through).

**InnoDB** is transaction safe, but slower for reads. It also allows row-level locking when making writes, while MyISAM locks the entire table when writing to it. If we find that a table is slow to be read, we can create *indexes* as a first step and then change the underlying storage engine if performance is still an issue. 

#### Creating the *Exchange* Table
The *Exchange* table stores the abbreviation and name of the exchange:
 - NYSE - New York Stock Exchange
 - NASDAQ
 - SS - Shanghai
 - SZ - Shenzhen

It as well sotres:
 - Geographic location
 - Currency
 - A timezone offset from UTC
 - A timestamp at creation
 - A timestamp when the entry was laste updated
 - An Index key - an auto-incrementing integer

```
CREATE TABLE ‘exchange‘ (
  ‘id‘ int NOT NULL AUTO_INCREMENT,
  ‘abbrev‘ varchar(32) NOT NULL,
  ‘name‘ varchar(255) NOT NULL,
  ‘city‘ varchar(255) NULL,
  ‘country‘ varchar(255) NULL,
  ‘currency‘ varchar(64) NULL,
  ‘timezone_offset‘ time NULL,
  ‘created_date‘ datetime NOT NULL,
  ‘last_updated_date‘ datetime NOT NULL,
  PRIMARY KEY (‘id‘)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

CREATE TABLE ‘data_vendor‘ (
  ‘id‘ int NOT NULL AUTO_INCREMENT,
  ‘name‘ varchar(64) NOT NULL,
  ‘website_url‘ varchar(255) NULL,
  ‘support_email‘ varchar(255) NULL,
  ‘created_date‘ datetime NOT NULL,
  ‘last_updated_date‘ datetime NOT NULL,
  PRIMARY KEY (‘id‘)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

CREATE TABLE ‘symbol‘ (
  ‘id‘ int NOT NULL AUTO_INCREMENT,
  ‘exchange_id‘ int NULL,
  ‘ticker‘ varchar(64) NOT NULL,
  ‘instrument‘ varchar(64) NOT NULL,
  ‘name‘ varchar(255) NULL,
  ‘sector‘ varchar(255) NULL,
  ‘currency‘ varchar(32) NULL,
  ‘created_date‘ datetime NOT NULL,
  ‘last_updated_date‘ datetime NOT NULL,
  PRIMARY KEY (‘id‘),
  KEY ‘index_exchange_id‘ (‘exchange_id‘)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

CREATE TABLE ‘daily_price‘ (
  ‘id‘ int NOT NULL AUTO_INCREMENT,
  ‘data_vendor_id‘ int NOT NULL,
  ‘symbol_id‘ int NOT NULL,
  ‘price_date‘ datetime NOT NULL,
  ‘created_date‘ datetime NOT NULL,
  ‘last_updated_date‘ datetime NOT NULL,
  ‘open_price‘ decimal(19,4) NULL,
  ‘high_price‘ decimal(19,4) NULL,
  ‘low_price‘ decimal(19,4) NULL,
  ‘close_price‘ decimal(19,4) NULL,
  ‘adj_close_price‘ decimal(19,4) NULL,
  ‘volume‘ bigint NULL,
  PRIMARY KEY (‘id‘),
  KEY ‘index_data_vendor_id‘ (‘data_vendor_id‘),
  KEY ‘index_symbol_id‘ (‘symbol_id‘)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
```

Note the datatype is *decimal(19,4)* to deal with financial data to ensure absolutely precision. To store the trading volume for the day, the datatype is *bigint* so that we don't accidently truncate extreme high volume days.

## Connecting to the Database
Before we can use MySQL with Python, we need to install the *mysqlclient* library from pip. *mysqlclient* is a fork of another library, known as *Python-MySQL*. Unfortunately, the latter library is not supported in Python3.

#### Using an Object-Relational Mapper (ORM)
An ORM allows objects within a programming language to be directly mapped to tables in databases such that the program code is fully unaware of the underlying storage engine. They can save a great deal of time, however, the time-saving usually comes at the expense of performance. A popular ORM for Python is SQLAlchemy - it can automatically generate the CREATE TABLE code.

## Symbol Retrieval (S&P 500 Constituents Only)
See fetch_S&P500.py.
