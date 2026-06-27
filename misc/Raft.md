### Writes

```
         Leader
        etcd-1
       /      \
Follower      Follower
etcd-2        etcd-3
```

- When the leader recieves a write, is appends it to its log entry (No changes are made to the DB) and updates its 
- Leader sends AppendEntries RPC to the followers
- All the online followers append the entry to their log and send an ACK to the leader
- If the leader does not recieve majority ACKs, thw write is rejected
- Otherwise, the leader advances it commitIndex, makes the log changes to the DB and sends a success response to the client
- The leader then broadcasts the advance commitIndex to the followers
- The followers apply the changes to their DB asynchronously
