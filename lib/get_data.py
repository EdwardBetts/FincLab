""" Module: To get data from MySQL database.

    Peter Lee
    Last update: 2016-Jan-12

    A sample program to obtain the Open-High-Low-Close (OHLC) dat for the Google stock over a certain time period from the securities master database.
"""

import pandas as pd
import MySQLdb as mdb
from lib.load_config import load_config


if __name__ == '__main__':
    db_config = load_config("MySQL_finclab")

    try:
        conn = mdb.Connection(**db_config)
        cursor = conn.cursor()

        # Select all of the historical Google adjusted close data
        query = """
            SELECT dp.price_date, dp.adj_close_price
            FROM symbol AS sym
            INNER JOIN daily_price AS dp
            ON dp.symbol_id = sym.id
            ORDER BY dp.price_date ASC;
        """

        df = pd.read_sql_query(query, con=conn, index_col='price_date')
        print(df.tail())

    except mdb.Error as e:
        print("Error:", e)

    finally:
        cursor.close()
        conn.close()
