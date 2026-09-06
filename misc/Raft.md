### How are writes performed in a consensus

```
         Leader
        etcd-1
       /      \
Follower      Follower
etcd-2        etcd-3
```

- When the leader receives a write, is appends it to its write ahead log (No changes are made to the DB)
- If a follower receives a write, the following happens:

```
Client
   │
   ├── request ──► Follower
   │                  │
   │                  └── "leader is A"
   │
   ├── retry ─────► Leader A
   │
   ▼
successful write
```

- Leader sends AppendEntries RPC to the followers in format (log_index, term, data)
    - log_index: The current entry position in the log
    - term: When a leader is changed, the term is incremented     
- All the online followers append the entry to their log and send an ACK to the leader
- If the leader does not receive majority ACKs, the write is rejected
- Otherwise, the leader advances it commitIndex, makes the log changes to the DB and sends a success response to the client
    - commitIndex: Highest index which has been successfully commited
- The leader then broadcasts the advance commitIndex to the followers
- The followers apply the changes to their DB asynchronously

### LeaderElection

- Requirements:
    - Ensure only one leader at a time.
- Each follower receives a broadcast heartbeat every hundred milliseconds.
- If the heartbeat stops, each follower starts a timeout after which it promotes itself to a candidate state. These timeouts are random which avoid multiple followers promoting themselves to candidate at the same time, voting themselves and no majority being formed.
- Each candidate sends the RequestVote RPC which contains:

```
RequestVote
term = 8               # The current election term of the candidate (might not be the actual election number if this candidate failed to participate in a previous election)
candidate = B
lastLogIndex = 125
lastLogTerm = 7
```

- The candidate receives a vote from the other followers only if its variables are higher
- The follower checks if it has not voted in this term. If it has, it does not vote again.

#### Success Scenario

- If a quorum is formed, the candidate becomes new leader.
- This update is broadcasted to the followers to update in their internal state.

#### Failure Scenario

- If the variables are less than majority of the followers, the candidate loses the election
- If the candidate is in a network partition, the quorum can never be formed
- Other followers election timeout will now trigger a new election in the same term

#### Vote split

- If 2 followers become candidates at the same time and a vote split occurs, no one becomes the leader in that election and the election times out.
- Eventually, a different follower promotes itself to candidate and starts the election again.

### Index divergence

- After a new leader is elected, it synchronizes each follower's log using the AppendEntries RPC.
- The leader first finds the last common log entry (matching both index and term) shared with the follower.
- If the follower has conflicting entries after that point (same index but different term), those entries and everything after them are deleted.
- The leader then sends all missing log entries after the common point, and the follower appends them to its log.
- After synchronization, the follower's log becomes an exact prefix match of the leader's log and eventually an exact copy as all entries are replicated.

#### Situation

**Consider A B C D E, with A as the leader. A write request comes to A, only D acknowledges it and now has the latest logIndex but the write has not been acknowledged to the client. Now D becomes the leader because it has the latest logIndex and streams this log to all the followers, but the write was never supposed to be done**

This is allowed in a distributed system. A write may have been acknowledged in the system even after a client timeout. Thats why retries should be idempotent

In case of K8s, the object type+name makes the CREATE request idempotent

