### Creating a new DB

- Every postgres installation has a catalogue table called pg_database which stores the metadata of every database

```sql
select datname, datistemplate  from pg_database;
```

- A new database is created based on the template1 db (template1 appears as one of the rows in the above query output)

```sql
# Copied from template1
CREATE DATABASE appdb;
```

- template1 can be edited
- template0 is the original unedited version of template1
- New templates can be created, which also appear in pg_database and can be used to create DB's from them
- template DB tables can have normal data in them

### Schema

- Namespaces inside a DB which hold all the objects such as tables, views, indexes etc
- Check the current schema

```sql
SELECT current_schema();
```

- Create a new schema and use it

```sql
CREATE SCHEMA hr
SET search_path TO hr;
```

- The default schema is `public`

### DDL

- CREATE
- ALTER
- DROP
- TRUNCATE

### DML

- SELECT
- UPDATE
- INSERT
- DELETE

### Data Types

- INTEGER (4 bytes)
- BIGINT (8 bytes)
- NUMERIC (float)
- CHAR (fixed length n)
- VARCHAR (max length n)
- TEXT (true variable length)
- BOOLEAN
- JSON
- JSONB (binary JSON)
- time related data
- UUID

### Composite types

- Create a composite type

```sql
CREATE TYPE person_type AS (
    id INTEGER,
    name TEXT,
    age INTEGER
);
```

- person_type can be used as a column type in a table

- Create a typed table

```sql
CREATE TABLE people OF person_type;
# Will contain id, name and age columns
```

### Auto Increments

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    name TEXT
);
```


### Types of tables

#### Typed tables

#### Temporary tables

- Only exists for the duration of the session
- Use to store intermediate results of complex queries

```sql
CREATE TEMP TABLE sales_summary AS
SELECT customer_id, SUM(amount) AS total
FROM sales
GROUP BY customer_id;
```

#### Unclogged Tables

- Skips the WAL logs
- A table can be defined as clogged or unclogged at any point in its lifecycle
- The table is entirely truncated after a restart because it might be violating the ACID properties
- Since WAL logs are not written, replication is not supported
- https://www.crunchydata.com/blog/postgresl-unlogged-tables

#### Inherited tables

- Tables support inheritance
- Partition tables are an example of it
- Changes in the parent are propagated to the child
- Columns and the constraints defined on them are propagated by default, but the physical storage remains different

```sql
CREATE TABLE parent (
    id   int,
    name text
);

CREATE TABLE child (
    age int
) INHERITS (parent);
```

- Propagating indexes to the child tables

```sql
CREATE TABLE child (
    LIKE parent INCLUDING INDEXES
    age int,
) INHERITS (parent);
```

- Can suffer with something similar to the diamond problem, example, if a table inherits from 2 tables, which define the same column name but of different types


#### Views

- A view is a stored procedure. The query is executed and the results are not stored.

```sql
CREATE VIEW active_users AS
SELECT id, name
FROM users
WHERE active = true;

SELECT * FROM active_users; # Executes the above query
```

#### Materialized views

- The query is executed once and the result is stored as a table

```sql
CREATE MATERIALIZED VIEW  datatypes_mviewcustomer_sales AS
SELECT customer_id, SUM(amount) AS total_sales
FROM orders
GROUP BY customer_id;

select * from datatypes_mviewcustomer_sales; # This is faster because the grouping operation is not performed again
```

- Refresh the view

```sql
REFRESH MATERIALIZED VIEW datatypes_mviewcustomer_sales;
```

- Materialized view vs CREATE TABLE AS: The query is executed each time and the results are also stored.

#### Partition tables

- Create a table and define the key based on which the data will be partitioned and the partitioning scheme
- Schemes: range, list, hash
- Useful for dividing data across tables for faster searches
- No data is stored in the parent table
- Performance benefits: Partition pruning, Each partition has its own index, Detach a partition from the parent for archiving/ delete the entire partition based on retention policy instead of scanning the entire table based on a where clause
- Range and List scheme inserts might fail if the required child table does not exist
- Uniqueness of the primary key across partitions is not guaranteed since each partition is a unique table

### Constraints

#### NOT NULL

- A column value cannot be null
- Checked in the INSET/ UPDATE query syntax itself

#### UNIQUE

- A column value needs to be unique across the table
- A NULL value is allowed because it is not checked for uniqueness

#### CHECK

- A defined condition should be true while inserting a value into the table for a particular column
- Checked in the INSET/ UPDATE query syntax itself

```
CHECK (age >= 18)
CHECK (area in (IN))
```

#### PRIMARY KEY

- Defines a row uniquely
- Uses the constraints NOT NULL and UNIQUE

#### FOREIGN KEY

- Enforces a column value to be a valid value in a foreign table

```sql
CREATE TABLE employees (
    id INT PRIMARY KEY,
    name TEXT,
    department_id INT,
    FOREIGN KEY (department_id)
        REFERENCES departments(id)
);
```

#### Composite key

```sql
CREATE TABLE student_courses (
    student_id INT,
    course_id INT,
    enrolled_at DATE,

    PRIMARY KEY (student_id, course_id)
);
```

### Sequences

```sql
CREATE SEQUENCE mysequence
INCREMENT 5
START 100;

SELECT nextval('mysequence');
```

### Roles

- Roles represent interaction with the database
- A role with a login privilege is a user

```sql
-- A basic login role (application user)
CREATE ROLE app_user WITH LOGIN PASSWORD 'strong_password_here';

-- A role that can create databases (for a developer)
CREATE ROLE dev_user WITH LOGIN CREATEDB PASSWORD 'dev_password';

-- A group role (no login, used for grouping permissions)
CREATE ROLE readonly_group;

-- A role with a password expiration
CREATE ROLE temp_contractor WITH LOGIN PASSWORD 'temp_pass' VALID UNTIL '2026-06-01';
```


#### Privileges

```
PostgreSQL Privileges
│
├── DATABASE
│   │
│   ├── CONNECT
│   │   └── Connect to the database
│   │
│   └── CREATE
│       └── Create schemas in the database
│
├── SCHEMA
│   │
│   ├── USAGE
│   │   └── Access objects inside the schema
│   │
│   └── CREATE
│       └── Create objects inside the schema
│
├── TABLE
│   │
│   ├── SELECT
│   │   └── Read rows
│   │
│   ├── INSERT
│   │   └── Add rows
│   │
│   ├── UPDATE
│   │   └── Modify rows
│   │
│   ├── DELETE
│   │   └── Remove rows
│   │
│   ├── TRUNCATE
│   │   └── Empty table
│   │
│   ├── REFERENCES
│   │   └── Create foreign-key constraints
│   │
│   └── TRIGGER
│       └── Create triggers
│
├── SEQUENCE
│   │
│   ├── USAGE
│   │   └── Use sequence values
│   │
│   ├── SELECT
│   │   └── Read sequence value
│   │
│   └── UPDATE
│       └── Modify sequence value
│
└── FUNCTION
    │
    └── EXECUTE
        └── Run the function
```

- Granting a privilege to a role

```sql
GRANT privilege ON object TO role
```

### Rules

```sql
CREATE [ OR REPLACE ] RULE name AS ON event
    TO table_name [ WHERE condition ]
    DO [ ALSO | INSTEAD ] { NOTHING | command | ( command ; command ... ) }

CREATE OR REPLACE RULE AUDIT_EMPLOYEE AS ON UPDATE
    TO EMPLOYEE 
    DO ALSO INSERT INTO TABLE EMPLOYEE_LOG () values ();
```

https://www.sqlservercentral.com/articles/rules-in-postgresql

### Triggers

### Policies

### Functions

### Procedures

### Storage policy

- Postgres divides the file for one table in multiple segments of size 1GB (not configurable)
- Each file has slots in the header and pages which hold the data of size 8KB
- A row or a tuple's location is defined by ctid (page number, slot number).
- The slot number holds the offset of the data in the file segment
- Since data of variable length is allowed, postgres does not update a tuple's value in place (for an UPDATE operation). Instead, it creates a new entry (preferably in the same page).

### read vs pread

- When open() is called on a file, a file descriptor is returned
- Each file descriptor has a global file offset
- read uses that offset. Thus, read should be used when a file is accessed sequentially.
- For random access, which databases need, pread is used. The offset needs to be defined in each pread call. 2 threads can thus access a file at different offsets without modifying the global offset
- Postgres uses this system call for a disk read
- The files are usually mmaped for faster IO. pread is executed only for a major page fault


#### TableSpace

### Indexing

- Why are B-Trees used: Rebalancing
- When a row is updated, a new ctid is created, and the new ctid needs to be updated in all the indexes defined on the table
- Index can be defined on a composite key
- Index needs to be re-built as index performance degrades with more deletions
- Sequential scans are faster whereas indexes use random access. The DB prefers to use a seq scan for smaller tables, bitmaps for having a more sequential access to the index pages and purely indexing for a very large table
- Partial indexes are created using where clause

#### Concurrent indexing

- Normal index creation locks the table
- Using concurrent indexing avoids that, uses MVCC and is slower

### MVCC

- Metadata of a row: ctid, xmin, xmax, state of the transaction

#### Insert

- The transaction begins
- The new row is written with xmin = current transaction id, xmax = 0 and transaction state = IN_PROGRESS
- The transaction ends and the state is converted to COMPLETE

#### Update

- The transaction begins
- For the existing row, update xmax = current transaction id
- Create a new row with a new ctid, with xmin = current transaction id, xmax = 0
- The transaction ends and the state is converted to COMPLETE
- The ctids form a chain, a ctid with a non zero xmax value means that it has been updated/deleted
- Find the ctid with the xmin value as the previous xmax value and that ctid reflects the latest version of the row

#### Delete

- The transaction begins
- For the existing row, update xmax = current transaction id
- No new row is created which means that the row is deleted

### Locks

- Read-Read concurrent transactions do not require any concurrency support
- Read-Write: MVCC
- Write-Write: Lock
- Read: https://github.com/TheOtherBrian1/Postgres_Lock_Explainer
- Locking behaviour is defined using xmax. A row with a non zero xmax value whose tid is an the ongoing transaction is considered locked. The update to the xmax value itself is a separate atomic operation.
- When inserting a row to a table which references a foreign key, the foreign table's corresponding row is locked using the FOR KEY SHARE lock.
- Example: For update lock blocks a different query acting on the same row. It also blocks any query whose update might cause a constraint violation after the query blocking the row

#### VACUUM

- Previous versions of a row are deleted using VACUUM

### Atomicity

- In Postgres, atomicity is represented at a transaction level
- All the operations in a transaction should be either be committed or rolled back
- If one of the operations fail, the transaction is marked as ABORTED
- In an ongoing transaction, the data is written to a postgres pages. WAL logs are also written but not marked committed yet. The pages may also get flushed to the disk as per the fsync. After COMMIT, the transaction is marked as committed in WAL and transaction state table(pg_xact). After this the response is returned to the client
- For INSERT, a rollback theoretically means remove the new tuple
- For UPDATE, a rollback theoretically means remove the new tuple and revert the xmax value of the previous tuple
- For DELETE, a rollback theoretically means revert the xmax value of the deleted tuple
- In practice, the tuples are left as such, the transaction state is updated to ABORTED and VACUUM eventually performs the garbage collection
- Best Practice: Commit a transaction only after a unit of work has been completed, and not after every operation
- All changes made by a transaction can be rolled back using ROLLBACK;
- A save point is like a checkpoint during a transaction. Like a snapshot, which only considers tuples of xmin < current_tid and xmax < current_tid where xmax should be DONE, maybe a save point considers all tuples with xmin <= current_tid and xmax <= current_tid. The ntransaction_id could be updated so that the further changes can reflect that they were executed after the savepoint.
- A transaction can rollback to a save point and a release it

### Isolation

Concurrent transactions on a row introduces the following problems:

- Dirty reads: A new transaction(T2) reads a value which has not been committed yet(by T1). If T1 fails, then T2 was always operating on a wrong value
- Non repeatable reads: Two select statement in T2 might return different values if T1 has updated a row while T2 was running.
- Lost updates: T1 and T2 both read a row. T1 commits and ends, followed by T2. Now the update from T1 is lost
- Constraint violation

Each issue is solved by isolation levels, locks and constraint checks

1. Read committed: Only committed rows are visible to a transaction, i.e, the transaction state of a row should be DONE. Example, during the scan all the rows with xmin and xmax belonging to committed transactions are valid.
2. Repeatable read: Uses snapshot isolation. A snapshot is used to perform all reads in the table. During the scan, all rows with xmin and xmax belonging to committed transactions and both less than current_transaction_id are considered valid. This isolation level only solves the repeatable read problem. Updates inside a transaction with repeatable reads are aborted if the current version of the row belongs to a committed transaction with higher id. This ensures that updates are not performed on stale snapshot versions
4. Lost Update: FOR UPDATE lock for row level locks used in update queries.

#### UNIQUE Constraint checks (Also includes primary key violations)

For UPDATE lock does not allow concurrent writes to the same row. But what if 2 transactions try to write the same primary key to the table. Locks do not stop this because the rows are different. Example: T1 updates id 1 to id 2, T2 updates id 3 to id 2. Both transactions are running on different rows but end up causing a UNIQUE constraint violation. When 2 transactions try to update a row such that the key being updated has a UNIQUE constraint, a unique index is created using all the values with transaction state DONE and IN PROGRESS. The write is allowed only if the row can be inserted in this index. Access to this index is serialized

#### FOREIGN KEY

T1 updates a row to use a foreign key reference. T2 concurrently deleted the foreign key reference from the foreign table. Maybe: T1 and T2 need to acquire a common lock before proceeding. If T1 acquires it, then T2 fails and vice versa

#### CHECK across row values

Again, maybe a common lock is introduced before making changes to rows affected by a common CHECK constraint

#### Serializability

- Would the changes made by 2 transactions be the same had they been executed serially ?
- 

### Consistency

- A transaction is allowed only if it does not violate any constraints

### Durability

- A successfully committed transaction should always be reflected in the DB
- WAL is used for this
- If the transaction was reported as committed but its WAL wasn't durable, PostgreSQL cannot recover that transaction after a crash, so its changes may be lost.
- With fsync=on and synchronous_commit=on, PostgreSQL prevents this by waiting for the required WAL to become durable before confirming COMMIT.


### General

- Double quotes are identifiers, single quotes are used for strings
- <>: All values except the specified one

```sql
FROM -> WHERE -> GROUP BY -> HAVING -> SELECT -> ORDER BY -> LIMIT
```

### Performance tools

#### pgbench

#### EXPLAIN vs EXPLAIN ANALYZE

- Explain returns the path which might be followed to execute the query by the query engine based on statiscal estimates about the table
- ANALYZE runs the analysis query again and shows the latest estimated query cost
- The stored analysis can be viewed using:

```sql
SELECT * FROM pg_stats WHERE tablename = 'sensor_reading';
schemaname
tablename
attribute name: The column name
inherited
null_frac: Fraction of rows that are null
avg_width: The average number of bytes required to store the value
n_distinct: NUmber of distinct values
most_common_vals
most_common_freqs: Frequencies of the most common values
histogram_bounds: Boundry values
correlation: correlation(sorted values, page size). This determines how sequential the disk access would be and the cost if the query
```

#### VACUUM
