## CTE (Common Table Expression)

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

## Neo4j

### Storage model

#### For the graph:

   (Alice:Person) ──LIKES {rating:5}──► (The Matrix:Movie {released:1999})
        │                                    ▲         ▲
        └──────LIKES──────┐                  │         │
                          ▼                  │         │
   (Bob:Person) ──LIKES──► (Inception:Movie  │         │
        │                   {released:2010}) │         │
        └────────────LIKES───────────────────┘         │
                                                       │
   (Carol:Person) ──────────────LIKES──────────────────┘

#### Node store

┌─────┬────────┬───────┬──────────┬───────────┬────────┬────────────┐
│ ID  │ Offset │ inUse │ firstRel │ firstProp │ labels │ (meaning)  │
├─────┼────────┼───────┼──────────┼───────────┼────────┼────────────┤
│ N0  │ 0      │ 1     │ R1       │ P0        │ L0     │ Alice      │
├─────┼────────┼───────┼──────────┼───────────┼────────┼────────────┤
│ N1  │ 15     │ 1     │ R3       │ P1        │ L0     │ Bob        │
├─────┼────────┼───────┼──────────┼───────────┼────────┼────────────┤
│ N2  │ 30     │ 1     │ R4       │ P2        │ L0     │ Carol      │
├─────┼────────┼───────┼──────────┼───────────┼────────┼────────────┤
│ N3  │ 45     │ 1     │ R4       │ P3        │ L1     │ The Matrix │
├─────┼────────┼───────┼──────────┼───────────┼────────┼────────────┤
│ N4  │ 60     │ 1     │ R3       │ P5        │ L1     │ Inception  │
└─────┴────────┴───────┴──────────┴───────────┴────────┴────────────┘

#### Relationship store

┌─────┬───────────┬──────────────┬──────┬───────────┬───────────┬────────────┬────────────┬──────┐
│ ID  │ firstNode │  secondNode  │ type │ firstPrev │ firstNext │ secondPrev │ secondNext │ prop │
├─────┼───────────┼──────────────┼──────┼───────────┼───────────┼────────────┼────────────┼──────┤
│ R0  │ N0 Alice  │ N3 Matrix    │ T0   │ R1        │ ∅         │ R2         │ ∅          │ P7   │
├─────┼───────────┼──────────────┼──────┼───────────┼───────────┼────────────┼────────────┼──────┤
│ R1  │ N0 Alice  │ N4 Inception │ T0   │ head      │ R0        │ R3         │ ∅          │ ∅    │
├─────┼───────────┼──────────────┼──────┼───────────┼───────────┼────────────┼────────────┼──────┤
│ R2  │ N1 Bob    │ N3 Matrix    │ T0   │ R3        │ ∅         │ R4         │ R0         │ ∅    │
├─────┼───────────┼──────────────┼──────┼───────────┼───────────┼────────────┼────────────┼──────┤
│ R3  │ N1 Bob    │ N4 Inception │ T0   │ head      │ R2        │ head       │ R1         │ ∅    │
├─────┼───────────┼──────────────┼──────┼───────────┼───────────┼────────────┼────────────┼──────┤
│ R4  │ N2 Carol  │ N3 Matrix    │ T0   │ head      │ ∅         │ head       │ R2         │ ∅    │
└─────┴───────────┴──────────────┴──────┴───────────┴───────────┴────────────┴────────────┴──────┘
