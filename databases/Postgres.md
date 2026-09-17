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

- A view is a stored query

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

#### UNIQUE

- A column value needs to be unique across the table
- A NULL value is allowed because it is not checked for uniqueness

#### CHECK

- A defined condition should be true while inserting a value into the table for a particular column

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

### Indexing

#### Concurrent indexing

### Performance testing tools

#### pgbench

#### EXPLAIN
