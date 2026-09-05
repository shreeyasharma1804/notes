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

- The leader receives a write request, creates a zid(transaction id) and writes the request to its transaction store.
- The leader sends a PROPOSAL broadcast to all the followers.
- Each follower writes the transaction to it's transaction store and sends an ACK back to the leader.
- If a majority of ACK are received, the leader sends the COMMIT broadcast and all the nodes apply the changes to the znode
- Response is sent to the client
- This tolerates network partitions.
- Multiple IDs are added while connecting to any cluster due to this reason. If a network partition occurs, the leader of the smaller quorum cannot accept writes and the client should retry with the other nodes

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


