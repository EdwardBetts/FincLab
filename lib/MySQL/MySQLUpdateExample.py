""" To update data in MySQL table 

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


def updateOneRow(bookid, title):
    """ Update one row at the time. """
    dbConfig = ReadMySQLConfig('MySQL_testing')
    
    query = """ UPDATE books
                set title = %s
                WHERE id = %s """

    data = (title, bookid)

    try:
        conn = mdb.Connection(**dbConfig)
        cursor = conn.cursor()

        cursor.execute(query, data)
        
        conn.commit()

    except mdb.Error as e:
        print(e)

    finally:
        cursor.close()
        conn.close()


if __name__ == '__main__':
    updateOneRow(5, 'yo this is the 5th book')

