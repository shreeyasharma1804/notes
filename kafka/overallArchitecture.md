## Zookeeper

### Cluster metadata znode tree.

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

### ZAB

Changes to the cluster metadata are applied through the ZAB protocol (Zookeeper atomic broadcast)

- The leader receives a write request, for example, new topic formation, and creates a zid(transaction id) and writes the request to its transaction store.
- The leader sends a PROPOSAL broadcast to all the followers.
- Each follower writes the transaction to it's transaction store and sends an ACK back to the leader.
- If a majority of ACK are received, the leader sends the COMMIT broadcast and all the nodes apply the changes to the znode
- Since the zid is already in the write ahead log, a success response is sent to the client

### Leader election

This is triggered when followers do not heartbeats from the leader in a specified time

- Every node broadcasts a vote for itself by sending the tuple (zxid, epoch, sid).
- When a node receives a peer's vote, it runs a comparison in the order epoch < zxid < sid. If the received vote has a higher precedence, the node revotes with the received vote.
- If the node is voting with an earlier epoch number, it adopts the latest epoch and votes again
- Every node checks the vote from all the other nodes. The sid which is voted for by the majority of the quorum. is elected as the new leader.


#### High Level Design

- A semaphore, value 0 means no leader election required.
- A thread which waits on this semaphore and does the leader election operations
- If a heartbeat is not received for x seconds, another thread increments the semaphore
- The leader election thread(lt) sends a broadcast message.

Scenario 1: lt is in a network partition on the quorum side

- lt evaluates the broadcast responses and checks which node to vote for during the next election
- lt sends out the new vote and this time a quorum should be formed
- The semaphore is decremented

Scenario 2: lt is in a network partition not on the quorum side

- lt will not receive enough responses to form a quorum
- Maybe, the semaphore is not decremented signalling that the node has no leader

Scenario 3: No network partition, and a real leader zookeeper failure

- lt evaluates the broadcast responses and checks which node to vote for during the next election
- lt sends out the new vote and this time the response should indicate a clear quorum
- The semaphore is decremented

Note: Multiple IDs are added while connecting to any cluster due to this reason. If a network partition occurs, the leader of the smaller quorum cannot accept writes and the client should retry with the other nodes


### Topic

- Each topic consists of x partitions where each partition has y replicas and a minimum number of in-sync replicas (<= y)
- Each partition has a leader which accepts the writes from the client
- The leader needs to ensure that a write is acknowledged by the quorum, which is based on the client's config and then send a success response back.

### Consumer groups, consumer offset management, and Group coordinator

- Any number of consumer clients with the same group.id belong to the same consumer group.
- If a topic has x partitions, it is recommended to have >=x consumers in the consumer group of that topic
- The offsets of a consumer group are stored in an im-memory table `(group.id, topic, partition): offset` and the __consumer_offsets topic with the key `(group.id, topic, partition)`
- After the consumer commits (auto/manually), the group coordinator updates the in memory table and the __consumer_offsets topic.
- The partition of a consumer group in the topic _consumer_offsets depends on its group.id. The group coordinator of a consumer group is thus the leader of the partition its writing to.
- At startup, the group coordinator creates an in memory map of `(group.id, topic, partition): offset`. By reaading the log segment files. This map is updated and managed in memory instead of reading the data in __consumer_offsets topic later.
- If a consumer leaves a consumer group, the group coordinator triggers a rebalance.

### Broker failure

#### Broker was partition leader

The new partition leader is the 1st alive ISR

### Broker was group coordinator

- Each broker is the group coordinator of a certain number of consumer groups.
- When a broker dies, a new partition leader is elected for the partition of __consumer_offsets. This is usually the next in-sync replica.
- That broker is now automatically the coordinator for all consumer groups that write to that partition.

### Internals

- The logs are stored in .log files which are auto-rotated and auto-deleted based on the configuration
- The .index files make this traversal faster
- sendfile is used to move offset x: x+y from the OS page cache to the socket
