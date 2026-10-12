### CTE (Common Table Expression)

- Unlike a temporary table which exists for the duration of the session, a CTE only exists during the execution of the statement

```sql
WITH tempValues AS (
    SELECT 1
    UNION ALL
    SELECT 2
    UNION ALL
    SELECT 3
)
select * from tempValues;
```

### Recursive CTE (DFS inside a relations graph)

```sql
WITH RECURSIVE tertiary_management as (
    SELECT
        1 as id,
        ARRAY [1] as visited
    UNION
    ALL
    select
        target_id,
        t.visited || e.target_id
    from
        edges e
        join tertiary_management t on e.source_id = t.id
    where
        not e.target_id = any(t.visited)
)
select
    *
from
    tertiary_management;
```

