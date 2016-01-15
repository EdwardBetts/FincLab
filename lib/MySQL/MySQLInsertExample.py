""" Example on how to insert data into MySQL table using Connection API.

Steps:
    1. Connect to the MySQL database by creating the Connection object
    2. Initiate a cursor()
    3. Execute the INSERT statement to insert data to the intended table
    4. Close the database connection

    In case a new row is inserted successfully, we can retrieve the lsat insertid of the AUTO_INCREMENT column by using the lastrowid property of the MySQLCursor object.

Source: http://www.mysqltutorial.org/python-mysql-insert/
"""

import MySQLdb as mdb
from ReadConfig import ReadMySQLConfig


def insertOneRow(title, isbn):
    """ Insert a row to the database 'testing' table 'books' """
    query = """INSERT INTO books(title, isbn)
               VALUES(%s, %s)
            """
    args = (title, isbn)

    dbConfig = ReadMySQLConfig('MySQL_testing')

    try:
        conn = mdb.Connection(**dbConfig)
        cursor = conn.cursor()
        cursor.execute(query, args)

    # In case a new row is inserted successfully, we can retrieve the lsat insertid of the AUTO_INCREMENT column by using the lastrowid property of the MySQLCursor object.
        if cursor.lastrowid:
            print('last insert id', cursor.lastrowid)
        else:
            print('last insert id not found.')

        conn.commit()

    except mdb.Error as e:
        print(e)

    finally:
        cursor.close()
        conn.close()


def insertManyRows(books):
    """ Insert many rows using .executemany() method
    :param books: a list of tuples
    """
    query = """INSERT INTO books(title, isbn)
               VALUES(%s, %s)
            """

    dbConfig = ReadMySQLConfig('MySQL_testing')

    try:
        conn = mdb.Connection(**dbConfig)
        cursor = conn.cursor()
        cursor.executemany(query, books)
        conn.commit()
    except mdb.Error as e:
        print(e)
    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    # Insert 1 row at a time
    insertOneRow('Snoopy', 'ADFasdlkfj20384')
    insertOneRow('yoyoyo', 'ADFasdlkfj20384')
    insertOneRow('super man is here!!', 'Alkjzlxjcglksjdf')
    # Insert many rows at the same time
    insertManyRows([
        ('Peter is awesome', 'alksdfjlkasdadf'),
        ('Kayden is smart', 'alsdkjfask82109347'),
        ('Toni is not bad', 'lkajsdfgkajsd098')
    ])
