""" This example shows how to query data from a MySQL database in Python using MySQL Connector such as fetchone(), fetchmany(), and fetchall().

To query data from Python, you need to do the following steps:
    1. Connect to the MySQL database, you get a mdb.Connection object.
    2. Instantiate a Cursor Object from the Connection object.
    3. Use the cursor to execute a query by calling its .execute() method.
    4. Use .fetchone(), .fetchmany() or .fetchall() method to fetch data from the result set.
    5. Close the cursor as well as the database connection by calling the close() method of the corresponding object.

    Source: http://www.mysqltutorial.org/python-mysql-query/
"""


import MySQLdb as mdb
from ReadConfig import ReadMySQLConfig


def queryWithFetchone():
    """ Initiate a MySQL query using .fetchone() method """
    # Load MySQL config
    dbConfig = ReadMySQLConfig()

    try:
        conn = mdb.Connection(**dbConfig)
        cursor = conn.cursor()

        # Execute a query
        cursor.execute("""
            SELECT * FROM user
        """)

        row = cursor.fetchone()

        while row is not None:
            print(row)
            row = cursor.fetchone()  # pop out this item and fill in the next

    except mdb.Error as e:
        print(e)

    finally:
        # Close connection
        cursor.close()
        conn.close()


def queryWithFetchall():
    """ In case the number of rows in the table is small, fetchall() method to fetch all rows from the database table is more efficient.
    fetchall() needs to allocate enough memory to store the entire result set in the memory (sometimes inefficient)
    """

    dbConfig = ReadMySQLConfig()

    try:
        conn = mdb.Connection(**dbConfig)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM user
        """)
        rows = cursor.fetchall()

        print('Total rows: {}'.format(cursor.rowcount))

        for row in rows:
            print(row)

        cursor.close()
        conn.close()

    except mdb.Error as e:
        print(e)


def queryWithFetchmany():
    """ Useful for a relatively big table, it takes time to fetch all rows and return the result set.
    fetchmany() method returns the next number of rows(n) of the result set, which allows us to balance between time and memory space.
    """
    dbConfig = ReadMySQLConfig()

    try:
        conn = mdb.Connection(**dbConfig)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT * FROM user
            """)

        for row in chunkCursor(cursor, 3):
            print(row)

        cursor.close()
        conn.close()

    except mdb.Error as e:
        print(e)


def chunkCursor(cursor, size=10):
    """ A generator that chunks the database calls into a series of fetchmany() calls. """
    while True:
        rows = cursor.fetchmany(size)
        if not rows:
            break
        for row in rows:
            yield row

if __name__ == '__main__':
    # queryWithFetchone()
    # queryWithFetchall()
    queryWithFetchmany()
