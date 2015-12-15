# Delete the existing user
user=root
password=Tonkay2819
mysql --user="$user" --password="$password" --execute="DROP USER sec_user@localhost; FLUSH PRIVILEGES;"

# Create a new database - securities_master
mysql --user="$user" --password="$password" --execute="DROP DATABASE IF EXISTS securities_master; CREATE DATABASE securities_master; USE securities_master; CREATE USER sec_user@localhost IDENTIFIED BY 'FincLab@2015'; GRANT ALL PRIVILEGES on securities_master.* TO sec_user@localhost; FLUSH PRIVILEGES;"

# Create the 1st table - exchange
user=sec_user
password=FincLab@2015
database=securities_master
mysql --user="$user" --password="$password" --database="$database" --execute="CREATE TABLE exchange (id int NOT NULL AUTO_INCREMENT, abbrev varchar(32) NOT NULL, name varchar(255) NOT NULL, city varchar(255) NULL, country varchar(255) NULL, currency varchar(64) NULL, timezone_offset time NULL, created_date datetime NOT NULL, last_updated_date datetime NOT NULL, PRIMARY KEY (id)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;"

# Create the 2nd table - data_vendor
mysql --user="$user" --password="$password" --database="$database" --execute="CREATE TABLE data_vendor (id int NOT NULL AUTO_INCREMENT, name varchar(64) NOT NULL, website_url varchar(255) NULL, support_email varchar(255) NULL, created_date datetime NOT NULL, last_updated_date datetime NOT NULL, PRIMARY KEY (id)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;"

# Create the 3rd table - symbol
mysql --user="$user" --password="$password" --database="$database" --execute="CREATE TABLE symbol (id int NOT NULL AUTO_INCREMENT, exchange_id int NULL, ticker varchar(64) NOT NULL, instrument varchar(64) NOT NULL, name varchar(255) NULL, sector varchar(255) NULL, currency varchar(32) NULL, created_date datetime NOT NULL, last_updated_date datetime NOT NULL, PRIMARY KEY (id), KEY index_exchange_id (exchange_id)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;"

# Create the 4th table - daily_price
mysql --user="$user" --password="$password" --database="$database" --execute="CREATE TABLE daily_price (id int NOT NULL AUTO_INCREMENT, data_vendor_id int NOT NULL, symbol_id int NOT NULL, price_date datetime NOT NULL, created_date datetime NOT NULL, last_updated_date datetime NOT NULL, open_price decimal(19,4) NULL, high_price decimal(19,4) NULL, low_price decimal(19,4) NULL, close_price decimal(19,4) NULL, adj_close_price decimal(19,4) NULL, volume bigint NULL, PRIMARY KEY (id), KEY index_data_vendor_id (data_vendor_id), KEY index_symbol_id (symbol_id)) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;"
