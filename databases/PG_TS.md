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
    table_name := 'metrics_' || TO_CHAR(partition_date, 'YYYY_MM_DD');

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



### Inserting with a cumulative update

select * from metrics;

CREATE PROCEDURE insert_data(
  IN ingest_time TIMESTAMP,
  IN metric DOUBLE PRECISION
)
LANGUAGE plpgsql
AS $$
BEGIN
     INSERT INTO metrics (ingest_time, metric)
     VALUES (ingest_time, metric);
END;
$$;
