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

### Consumer groups, consumer offset management, and Group coordinator

Any number of consumer clients with the same group.id belong to the same consumer group.
If a topic has x partitions, it is recommended to have >=x consumers in the consumer group associated with the topic

consumer offset:(group.id, topic, partition) stored in the topic __consumer_offsets.
After the consumer commits (auto/manually), the coordinator updated the in memory table and __consumer_offsets topic.
At startup, the group coordinator creates an in memory map of (group.id, topic, partition): offset. This map is updated and managed in memory instead of reading the data in __consumer_offsets topic.

If a consumer leaves a consumer group, the group coordinator triggers a rebalance.

### Topic

Each topic is configured with the number of partitions and replication factor. The replication factor decides the number of replicas for each partition.
Each partition has a leader broker and replica brokers.

### Broker failure

#### Broker was partition leader

The new partition leader is the 1st alive ISR

### Broker was group coordinator

- Each group coordinator coordinates a certain number of consumer groups. The broker of that group coordinator is also the partition leader of the __consumer_offsets
- When a broker dies, a new partition leader is elected for the partition of __consumer_offsets. This is usually the next insync replica.
- That broker is now automatically the coordinator for all groups that write to that partition.
- Consumers get NOT_COORDINATOR on next request
- Consumers call FindCoordinator → get directed to new broker
- Group rebalance triggered


