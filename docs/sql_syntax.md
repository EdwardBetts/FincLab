# SQL Syntax

## Background of SQL
**Tables**: The data is organised and stored into tables. Tables comprise of Rows and Columns.
    - **rows** or record: Like those in Excel
    - Column: Each column has a name.

**id**: Normally there is a unique identifier.

The search path first searches across columns, and rows (as there are typically more columns than rows).

NULL: A NULL value in a table is a value in a field that appears to be blank (missing).

SQL Constraints: Constraints are the rules enforced on data columns on table. These are used to limit the type of data that can go into a table. Constraints could be column level or table level.

SQL Syntax: All the SQL statements start with any of the keywords like SELECT, INSERT, UPDATE, DELETE, ALTER, DROP, CREATE, USE, SHOW. Syntax is case insensitive.


## Some usefule syntax

Show all tables
```
mysql -u root -p
SHOW DATABASES;
use securities_master;
show tables;
```

Select all data
```
SELECT * from table1;
```




