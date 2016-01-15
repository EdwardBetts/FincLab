""" To delete data in MySQL table 

Steps:
    1. Connect to the database by creating a Connection object
    2. Create a new cursor object. 
    3. Call .execute()
    4. call .commit()
    5. close cursor and connection

Source: http://www.mysqltutorial.org/python-mysql-update/
"""


import MySQLdb as mdb
from ReadConfig import ReadMySQLConfig


def deleteOneRow(bookid):
    """ Update one row at the time. """
    dbConfig = ReadMySQLConfig('MySQL_testing')
    
    query = """ DELETE from books 
                WHERE id = %s """

    try:
        conn = mdb.Connection(**dbConfig)
        cursor = conn.cursor()

        cursor.execute(query, (bookid, ))  # This comma - , - is magic
        
        conn.commit()

    except mdb.Error as e:
        print(e)

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    deleteOneRow(5)


