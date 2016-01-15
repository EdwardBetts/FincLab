""" Create the default database for the FincLab project. If exist, the database will be deleted and re-created.
    Date: 2015 Jan 06
    Author: Peter Lee
"""


import MySQLdb as mdb
from lib.ReadConfig import ReadMySQLConfig


def resetDatabase():
    """ Reset the entire database """

    dbRoot = ReadMySQLConfig('MySQL_root')
    dbUser = ReadMySQLConfig('MySQL_finclab')

    try:
        conn = mdb.Connection(**dbRoot)
        cursor = conn.cursor()

        query = """
            # Drop user
            DROP USER IF EXISTS {user}@{host};
            FLUSH PRIVILEGES;

            # Create a new database 'finclab'
            DROP DATABASE IF EXISTS {db};
            CREATE DATABASE {db};
            USE {db};

            # Create a new user and grant privileges
            CREATE USER {user}@{host} IDENTIFIED BY '{passwd}';
            GRANT ALL PRIVILEGES on {db}.* TO {user}@{host};
            FLUSH PRIVILEGES;

            # Create the 'exchange' table
            CREATE TABLE exchange (
                id int NOT NULL AUTO_INCREMENT,
                abbrev varchar(32) NOT NULL,
                name varchar(255) NOT NULL,
                city varchar(255) NULL,
                country varchar(255) NULL,
                currency varchar(64) NULL,
                timezone_offset time NULL,
                created_date datetime NOT NULL,
                last_updated_date datetime NOT NULL,
                PRIMARY KEY (id)
            ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

            # Create the 'data_vendor' table
            CREATE TABLE data_vendor (
                id int NOT NULL AUTO_INCREMENT,
                name varchar(64) NOT NULL,
                website_url varchar(255) NULL,
                support_email varchar(255) NULL,
                created_date datetime NOT NULL,
                last_updated_date datetime NOT NULL,
                PRIMARY KEY (id)
            ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

            # Create the 'symbol' table
            CREATE TABLE symbol (
                id int NOT NULL AUTO_INCREMENT,
                exchange_id int NULL,
                ticker varchar(64) NOT NULL,
                instrument varchar(64) NOT NULL,
                name varchar(255) NULL,
                sector varchar(255) NULL,
                currency varchar(32) NULL,
                created_date datetime NOT NULL,
                last_updated_date datetime NOT NULL,
                PRIMARY KEY (id), KEY index_exchange_id (exchange_id)
            ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;

            # Create the 'daily_price' table
            CREATE TABLE daily_price (
                id int NOT NULL AUTO_INCREMENT,
                data_vendor_id int NOT NULL,
                symbol_id int NOT NULL,
                price_date datetime NOT NULL,
                created_date datetime NOT NULL,
                last_updated_date datetime NOT NULL,
                open_price decimal(19,4) NULL,
                high_price decimal(19,4) NULL,
                low_price decimal(19,4) NULL,
                close_price decimal(19,4) NULL,
                adj_close_price decimal(19,4) NULL,
                volume bigint NULL,
                PRIMARY KEY (id), KEY index_data_vendor_id (data_vendor_id), KEY index_symbol_id (symbol_id)
            ) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8;
            """.format(**dbUser)

        cursor.execute(query)

    except mdb.Error as e:
        print(e)

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    # Create / Reset the database
    resetDatabase()
