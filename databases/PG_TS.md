### Organizing data into partitions and partition management

- Create a partitioned table

```sql
CREATE TABLE metrics (
  id BIGSERIAL,
  ingest_time TIMESTAMP NOT NULL,
  metric DOUBLE PRECISION
)
PARTITION BY
  RANGE (ingest_time);
```

- Create a procedure to create the future partitions beforehand

```sql
CREATE OR REPLACE PROCEDURE create_partitions(IN partition_date DATE)
LANGUAGE plpgsql
AS $$
DECLARE
    table_name VARCHAR(50);
BEGIN
    table_name := 'metrics_' || TO_CHAR(partition_date, 'YYYY-MM-D');

    EXECUTE format(
        'CREATE TABLE %I PARTITION OF metrics
         FOR VALUES FROM (%L) TO (%L)',
        table_name,
        partition_date,
        partition_date + 1
    );
END;
$$;
```

- Create a procedure to delete partitions older than x days

```sql
CREATE OR REPLACE PROCEDURE detach_partitions () 
LANGUAGE plpgsql 
AS $$ 
DECLARE 
    table_name VARCHAR(50);
    partition RECORD;
    partition_date DATE;
BEGIN 
FOR partition IN
select
    child.relname as partition_name
from
    pg_inherits
    join pg_class parent on pg_inherits.inhparent = parent.oid
    join pg_class child on pg_inherits.inhrelid = child.oid
where
    parent.relname = 'metrics'
LOOP
    partition_date := split_part(partition.partition_name, '_', 2)::DATE;
    IF 
        partition_date < CURRENT_DATE - 7 THEN
            DROP TABLE partition.partition_name;
    END IF;
END LOOP;

END;

$$;
```


### Inserting with a cumulative update

- Cumulative data on a per day basis can be stored in a separate table.
- This allows running queries on a very large dataset sampled on a per day basis for example linear regressions.
- A procedure which updates both the tables in one transaction should be used here
- Complex functions like linear regressions can be run bu calling python script from the procedures

```sql
CREATE FUNCTION getSomeData()
RETURNS trigger
AS $$
begin
import subprocess
subprocess.call(['/path/to/your/virtual/environment/bin/python3', '/some_folder/some_sub_folder/get_data.py'])
end;
$$ 
LANGUAGE plpythonu;
```

### Columnar storage
