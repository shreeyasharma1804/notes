### Replication is done via WAL Streaming

#### Contents of a WAL 

- Insert

```
LSN: 
Resource Manager: Heap
Operation: INSERT
Relation: employees
Block: 0
Offset: 3
Tuple: ()
transaction: 
```

- Update (Changes to the index become a seperate WAL entry)

```
LSN: 
rmgr: Heap
desc: UPDATE
old block: 2
old offset: 4
new block: 2
new offset: 5
transaction: 200
tuple: 
```

- With PostgreSQL physical (streaming) replication, the block numbers and tuple offsets are preserved across the primary and standby.
