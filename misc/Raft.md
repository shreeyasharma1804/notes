### Writes

```
         Leader
        etcd-1
       /      \
Follower      Follower
etcd-2        etcd-3
```

- When the leader recieves a write, is appends it to its log entry (No changes are made to the DB) and updates its 
- Leader sends AppendEntries RPC to the followers in format (log_index, term, data)
- All the online followers append the entry to their log and send an ACK to the leader
- If the leader does not recieve majority ACKs, thw write is rejected
- Otherwise, the leader advances it commitIndex, makes the log changes to the DB and sends a success response to the client
- The leader then broadcasts the advance commitIndex to the followers
- The followers apply the changes to their DB asynchronously

### LeaderElection

- Ensure only one leader at a time.
- Each follower recieves a broadcast heartbeat every hundred milliseconds.
- If the heartbeat stops, each follower starts a timeout after which it promotes itself to a candidate state. These timeouts are random which avoid multiple followers promoting themselves to candidate at the same time, voting themselves and no majority being formed.
- Each candidate sends the RequestVote RPC which contains:

```
RequestVote
term = 8               # The current election term of the candidate (might not be the actual election number if this candidate failed to participate in a previous election)
candidate = B
lastLogIndex = 125
lastLogTerm = 7
```

- Now, the follower updates it's election term if it's election term < term sent by candidate.
- The follower checks if it has not voted in this term. If it has, it does not vote again.
- Otherwise, the follower compares the lastLogTerm to check if the candidate has the latest data. If lastLogTerm of candidate > lastLogTerm of follower, it votes for it, otherwise lastLogIndex is the tiebreaker.

#### Vote split

- If 2 followers become candidates at the same time and a vote split occurs, no one becomes the leader in that election and the election times out.
- Eventuall, a different follower promotes itself to candidate and starts the election again.

#### Index divergence

- Index divergence occurs when a follower has

#### Situation

**Consider A B C D E, with A as the leader. A write request comes to A, only D acknowledges it and now has the latest logIndex but the write has not been acknowledged to the client. Now D becomes the leader because it has the latest logIndex and streams this log to all the followers, but the write was never supposed to be done**

This is allowed in a distributed system. A write may have been acknowledged in the system even after a client timeout. Thats why retries should be idempotent

In case of K8s, the object type+name makes the CREATE request idempotent

