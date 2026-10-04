### Using Postgres as a Queue

#### Schema

- Topic_Name
- Data
- Consumed

```sql
(TOPIC_A,'a', False)
(TOPIC_A, 'b', False)
(TOPIC_B, 'a', False)
(TOPIC_B, 'b', False)
```

Each topic holds multiple data points

#### Producing data

```sql
INSERT INTO KAFKA_TABLE (Topic_Name, Data, Consumed) VALUES (TOPIC_A, 'c', False)
```

#### Consumer

- Consumer which consumes from TOPIC_A

```sql
UPDATE kafka_table
SET consumed = true
WHERE id = (
    SELECT id
    FROM kafka_table
    WHERE topic_name = 'TOPIC_A'
      AND consumed = false
    ORDER BY id
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
RETURNING data;
```
