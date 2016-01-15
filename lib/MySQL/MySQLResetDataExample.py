""" Create (or reset) a test database """

import MySQLdb as mdb
from ReadConfig import ReadMySQLConfig


def resetTestDatabase():
    """ To delete and create a MySQL database named Testing """

    dbConfigRoot = ReadMySQLConfig("MySQL_root")
    dbConfigTesting = ReadMySQLConfig("MySQL_testing")

    try:
        conn = mdb.Connection(**dbConfigRoot)
        cursor = conn.cursor()

        # Delete the user
        cursor.execute("""
            # Drop the user
            DROP USER IF EXISTS {user}@{host};
            FLUSH PRIVILEGES;
            # Create a new database
            DROP DATABASE IF EXISTS {db};
            CREATE DATABASE {db};
            USE {db};
            CREATE USER {user}@{host} IDENTIFIED BY '{passwd}';
            GRANT ALL PRIVILEGES on {db}.* TO {user}@{host};
            FLUSH PRIVILEGES;
            # Create a table
            CREATE TABLE books (
                id int NOT NULL AUTO_INCREMENT,
                title varchar(1024) NOT NULL,
                ISBN varchar(32) NOT NULL,
                PRIMARY KEY (id)
            )
            ENGINE=InnoDB
            AUTO_INCREMENT=1
            DEFAULT
            CHARSET=utf8;
        """.format(**dbConfigTesting))

    except mdb.Error as e:
        print(e)

    finally:
        cursor.close()
        conn.close()


if __name__=='__main__':
    resetTestDatabase()
