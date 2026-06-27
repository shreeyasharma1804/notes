| Component               | Runs on every control plane?   | Active instances                                     |
| ----------------------- | ------------------------------ | ---------------------------------------------------- |
| kube-apiserver          | ✅ Yes                          | **All are active**                                   |
| kube-scheduler          | ✅ Yes                          | **One leader**, others standby                       |
| kube-controller-manager | ✅ Yes                          | **One leader**, others standby                       |
| etcd                    | ✅ Yes (typically 3 or 5 nodes) | **All participate** via the Raft consensus algorithm |

### kube-apiserver: Active-Active

Every control-plane node runs an API server.

```text
          Load Balancer
        /      |       \
    API1    API2    API3
```

Any API server can handle any request:

* `kubectl get pods`
* `kubectl apply`
* kubelet heartbeats
* controller requests

They are stateless. They all read from and write to the same etcd cluster.


### kube-scheduler: Active-Passive

All scheduler processes are running, but only one schedules pods.

```text
Scheduler1  <-- Leader ✅
Scheduler2  <-- Waiting
Scheduler3  <-- Waiting
```

If the leader dies:

```text
Scheduler2 becomes leader
```

This avoids two schedulers assigning the same Pod simultaneously.


### kube-controller-manager: Active-Passive

Same pattern.

```text
Controller1 <-- Leader ✅
Controller2 <-- Standby
Controller3 <-- Standby
```

Only the leader runs control loops such as:

* Deployment controller
* ReplicaSet controller
* Node controller
* Job controller

The others are ready to take over if the leader fails.


The design philosophy is:

* **API servers:** scale horizontally and remain active on every control-plane node.
* **Schedulers:** exactly one active leader to avoid conflicting scheduling decisions.
* **Controller managers:** exactly one active leader to avoid duplicate reconciliation.
* **etcd:** replicated with Raft, requiring quorum to safely store the cluster state.
