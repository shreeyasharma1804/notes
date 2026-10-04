### Using postgres as a Kakfa

#### Schema

- Topic_Name
- Partition_Name
- Is_Replica
- Data

```sql
(TOPIC_A, 1, False, 'a')
(TOPIC_A, 1, True, 'a')
(TOPIC_A, 1, False, 'b')
(TOPIC_A, 1, True, 'b')
(TOPIC_A, 2, False, 'a')
(TOPIC_A, 2, True, 'a')
(TOPIC_A, 2, False, 'b')
(TOPIC_A, 2, True, 'b')
(TOPIC_B, 1, False, 'a')
(TOPIC_B, 1, True, 'a')
(TOPIC_B, 1, False, 'b')
(TOPIC_B, 1, True, 'b')
(TOPIC_B, 2, False, 'a')
(TOPIC_B, 2, True, 'a')
(TOPIC_B, 2, False, 'b')
(TOPIC_B, 2, True, 'b')
```

Topic_A has 2 partitions, one replica per partition and 2 data points

#### Producing data

```sql
INSERT INTO KAFKA_TABLE (Topic_Name, Partition_Name, Is_Replica, Data) VALUES (TOPIC_A, 1, False, 'c')
INSERT INTO KAFKA_TABLE (Topic_Name, Partition_Name, Is_Replica, Data) VALUES (TOPIC_A, 1, True, 'c')
```

2 records are entered in Topic A both main and replica partition number 1

#### Consumer Groups

```sql

```

#### Consumer

```sql
UPDATE KAFKA_TABLE
SET balance = balance + 100
WHERE id IN (
    SELECT id
    FROM accounts
    WHERE status = 'active'
    ORDER BY id
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
RETURNING *;
```
