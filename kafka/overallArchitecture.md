### Zookeeper

Maintains cluster metadata in the znode tree.

```
/
├── /controller                          ← which broker is Controller
├── /controller_epoch                    ← how many times controller changed
├── /brokers
│   ├── /ids                             ← registered brokers
│   │   ├── /1
│   │   ├── /2
│   │   └── /3
│   ├── /topics                          ← topic metadata
│   │   └── /my-topic
│   │       └── /partitions
│   │           └── /0
│   │               └── /state           ← leader, ISR
│   └── /seqid
├── /config
│   ├── /topics                          ← topic configs
│   ├── /brokers                         ← dynamic broker configs
│   ├── /users                           ← quotas
│   └── /clients                         ← client quotas
├── /kafka-acl                           ← ACLs
├── /admin
│   └── /reassign_partitions             ← partition reassignment
├── /isr_change_notification             ← ISR change events
├── /log_dir_event_notification          ← log dir events
└── /consumers                           ← legacy consumer groups
```

Changes to the cluster metadata are applied through the ZAB protocol (Zookeeper atomic broadcast)

- The leader recieves a write request, creates a zid(transaction id) and writes the request to its transaction store.
- The leader sends a PROPOSAL broadcast to all the followers.
- Each follower writes the transaction to it's transaction store and sends an ACK back to the leader.
- If a majority of ACK are recieved, the leader sends the COMMIT broadcast and all the nodes apply the changes to the znode
- Response is sent to the client

Leader election

This is triggered when followers do not heartbeats from the leader in a specified time

- Every node broadcasts a vote for itself by sending the tuple (zxid, epoch, sid).
- When a node recieves a peer's vote, it runs a comparision in the order epoch < zxid < sid. If the recieved vote has a higher precedence, the node revotes with the recieved vote.
- If the node is voting with an earlier epoch number, it adopts the latest epoch and votes again
- Every node checks the vote from all the other nodes. The sid which is voted for by the majority of the quorum. is elected as the new leader.

### Consumer groups and consumer offset management

### Group coordinator

### Topic

Each topic is configured with the number of partitions and replication factor. The replication factor decides the number of replicas for each partition.
Each partition has a leader broker and replica brokers.

### Broker failure

#### Broker was partition leader

The new partition leader is the 1st alive ISR

### Broker was group coordinator


