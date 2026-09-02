### Properties defined at a pod level
- Containers
- restartPolicy
- Volumes
- terminationGracePeriodSeconds
- nodeSelector
- tolerations
- affinity

### initContainers

- Init containers are executed strictly in the order they are defined.
- Init container with `restartPolicy: Always` is a sidecar. This is an exeption to the general rule of restartPolicy only being defined at the pod level

```
Normal init container:
    Start → Complete → Next container starts

Native sidecar:
    Start → Keep running → Next init container starts
```

### Container resources

- Pod scheduling is based on the sum of all container resource requests.

- If the CPU limit is exceeded, the CPU cycles are withheld by the kernel. The container is throttled but not restarted

- If the memory limit is exceeded, the kernel kills the container with an exit code 137. The container is restarted according to the pod restartPolicy.

### QOS (Decides the Pod Eviction during memory/cpu pressure on node)

- Guaranteed: Every container has CPU and memory requests and limits defined, and request = limit for both resources.

- Burstable: At least one container has a request or limit defined, but the Pod is not Guaranteed.

- BestEffort: No container defines CPU or memory requests or limits.

### Pod Eviction

```
Low memory
    ↓
Node can become unstable
    ↓
Kubelet evicts Pods
```

```
High CPU usage
    ↓
Processes are throttled/scheduled less often
    ↓
No eviction
```


- The kubelet periodically checks node resource pressure (default housekeeping-interval: 10s).
- Eviction thresholds are configured through evictionSoft and evictionHard settings defined in the kubelet config.
- If a soft threshold is crossed, the condition must remain true until `eviction-soft-grace-period` before eviction occurs.
- If a hard threshold is crossed, kubelet immediately begins evicting Pods. The node is tainted as `MemoryPressure=True`. This prevents the scheduler from assigning new pods to that node. The node must stay out of hard eviction zone for `--eviction-pressure-transition-period` before removing `MemoryPressure` condition.

### PodScheduling

The node labelling is managed using Ansible

#### nodeSelector

This pod can be scheduled on only the nodes which have the labels disktype: ssd and zone: us-east-1a:

```yml
nodeSelector:
    disktype: ssd  
    zone: us-east-1a  
```
The label is checked only during scheduling. If the label is removed from the node later, the pod keeps running

#### Taints and Tolerations

Taints repel Pods. Tolerations allow Pods to ignore that repulsion. They don't attract Pods; they only remove a scheduling restriction.

Taint a node:

```
# Format: key=value:effect  
kubectl taint nodes node-1 gpu=true:NoSchedule
```

Check the taints of a node:

```bash
kubectl describe node cplane-01 | grep -i taint
```

Effects:
- PreferNoSchedule: Scheduler tries to avoid placing pods here but will if no other option exists.
- NoSchedule: New pods without a matching toleration are never scheduled on this node. Already-running pods are not evicted. Only affects future scheduling decisions.
- NoExecute: Blocks new pods AND evicts already-running pods that don’t tolerate it.

Define tolerations of a pod

```yml
tolerations:
- key: "gpu"
  operator: "Equal"
  value: "true"
  effect: "NoSchedule"
```

Example: 

```bash
kubectl drain
# Taint the node: `kubectl taint nodes <> drain=true:NoExecute`
```

#### nodeAffinity

- requiredDuringSchedulingIgnoredDuringExecution: The node label conditions need to meet during scheduling. If the node labels are removed after scheduling, the pod is not evicted.
- Here, a node with label `((gpu in true) AND (zone in east)) OR (workload in ml)` is eligible for scheduling the pod

```yml
requiredDuringSchedulingIgnoredDuringExecution:
  nodeSelectorTerms:
  - matchExpressions:
    - key: gpu
      operator: In
      values: ["true"]
    - key: zone
      operator: In
      values: ["east"]

  - matchExpressions:
    - key: workload
      operator: In
      values: ["ml"]
```

- preferredDuringSchedulingIgnoredDuringExecution: Each node is given a score based on the `preference`. The pod is scheduled on a node with the highest score, i.e, the weight

```yml
preferredDuringSchedulingIgnoredDuringExecution:
- weight: 80
  preference:
    matchExpressions:
    - key: disktype
      operator: In
      values: ["ssd"]

- weight: 20
  preference:
    matchExpressions:
    - key: zone
      operator: In
      values: ["east"]
```

| Node     | SSD? | East? | Score |
| -------- | ---- | ----- | ----- |
| worker-1 | Yes  | Yes   | 100   |
| worker-2 | Yes  | No    | 80    |
| worker-3 | No   | Yes   | 20    |
| worker-4 | No   | No    | 0     |

```
nodeSelectorTerms:
- ...
- ...
behaves like OR
```

### podAffinity

Used for:
- Keep tightly coupled services together
- Improve cache locality

#### Hard Affinity

```yml
affinity:
  podAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
    - labelSelector:
        matchLabels:
          app: redis
      topologyKey: kubernetes.io/hostname
```

#### Soft Affinity

```yml
affinity:
  podAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            app: redis
        topologyKey: kubernetes.io/hostname
```

With these affinities, a pod will be scheduled on a node only if it has a pod with label: `app: redis`

#### topologyKey

- `topologyKey: kubernetes.io/hostname`: The pod will only be scheduled on a node with the same hostname as the node meeting the affinity criteria
- `topologyKey: topology.kubernetes.io/zone`: The pod will only be scheduled on a node with the same zone(eg, east, west etc) as the node meeting the affinity criteria

#### podAntiAffinity

Works opposite to podAffinity, used to fan out replicas across nodes

```yml
affinity:
  podAntiAffinity:
    preferredDuringSchedulingIgnoredDuringExecution:
    - weight: 100
      podAffinityTerm:
        labelSelector:
          matchLabels:
            app: backend
        topologyKey: kubernetes.io/hostname
```

- This rule prefers to not schedule an app on a node which is running the pod with backend label
- Can be used to achieve one pod per node like behaviour

### Probes

Probes are defined on a per container basis only.

```yml
apiVersion: v1
kind: Pod
metadata:
  name: nginx-probes
spec:
  containers:
  - name: nginx
    image: nginx:1.29

    ports:
    - containerPort: 80

    startupProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 5
      periodSeconds: 10
      timeoutSeconds: 2
      failureThreshold: 30

    readinessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 0
      periodSeconds: 5
      timeoutSeconds: 2
      failureThreshold: 3
      successThreshold: 1

    livenessProbe:
      httpGet:
        path: /
        port: 80
      initialDelaySeconds: 0
      periodSeconds: 10
      timeoutSeconds: 2
      failureThreshold: 3
```

#### startupProbe

The kubelet executes the command httpGet after initialDelaySeconds every periodSeconds, waits for the response of the command for timeoutSeconds before timing out and tolerates failureThreshold number of failures. This provides a slow pod some time to start. After the threshold exceeds, the container is restarted

#### livenessProbe

Starts after startupProbe, similar to it and also restarts the container incase of failure

#### readinessProbe

Decides if the point is included in the service endpoint

### Static pods

Static pods are created directly by the kubelet and are not registered with the API server.

The static pod location can be found in the kubelet config: `/var/lib/kubelet/config.yaml | grep static`

All pods in this location are created and managed directly by the kubelet

To list the static pods:

```bash
kubeletctl -s <nodes> pods
```

A mirror pod is created for a static pod by the API server which can be identified through unique annotations. The mirror pod support get, cat and not edit, delete

Failure in creating mirror pod does not affect the static pod

### Security

Security is evaluated in the order: sudo privilage -> capability

#### runAsUser
`runAsUser: 0`: Allows the pod to run as UID 0
If usermapping is enabled, the pod is mapped to higher user on the host, if not, it runs as UID 0 on the host

Check if user mapping is enabled:

```bash
# Inside the pod
cat /proc/self/uid_map
```

#### Capabilities

- The container setting, sllows a pod to run with all linux capabilities.:

```yaml
securityContext:
  privileged: true
```

- To set the capabilities of a pod:

```yml
securityContext:
  capabilities:
    add:
    - NET_ADMIN
    - SYS_TIME
    drop:
    - ALL
```

- To check the capabilities inside a container:

```
kubectl exec -it <pod-name> -- sh
cat /proc/1/status | grep -i cap
capsh --decode=<capability hex value>
```

#### Pod Security Standards

Kubernetes uses Pod Security Admission (PSA) to enforce security rules on pods. The rules are grouped into three levels:

```text
Privileged  →  Baseline  →  Restricted
Least Secure             Most Secure
```

1. Privileged

No restrictions.

* Can run privileged containers
* Can use hostNetwork, hostPID, hostIPC
* Can add any Linux capability
* Can run as root

Used for:

* CNI plugins
* CSI drivers
* kube-proxy
* Node agents

```yaml
pod-security.kubernetes.io/enforce: privileged
```

2. Baseline

Prevents common privilege-escalation techniques while allowing most applications to run unchanged.

Blocks:

* `privileged: true`
* `hostNetwork`
* `hostPID`
* `hostIPC`
* Dangerous capabilities (`SYS_ADMIN`, `NET_ADMIN`, `SYS_PTRACE`, etc.)

Allows:

* Running as root
* HostPath volumes
* Default Linux capabilities

Used for:

* Most application workloads

```yaml
pod-security.kubernetes.io/enforce: baseline
```

3. Restricted

Adds strong hardening requirements.

Requires:

* `runAsNonRoot: true`
* `allowPrivilegeEscalation: false`
* `seccompProfile: RuntimeDefault`
* Drop capabilities (`ALL` recommended)

Also blocks:

* HostPath volumes
* Many additional risky settings

Used for:

* Multi-tenant clusters
* Internet-facing applications
* High-security environments

```yaml
pod-security.kubernetes.io/enforce: restricted
```

#### How enforcement works

- Namespace labels:

```yaml
metadata:
  labels:
    pod-security.kubernetes.io/enforce: baseline
```

When a pod is created:

```text
kubectl apply
      ↓
API Server
      ↓
Pod Security Admission
      ↓
Allow or Reject
```

### Pod Metrics

```bash
kubectl top pods
```

### Priority and Preemption

- The Kubernetes scheduler places pods in order of priority. When a high-priority pod cannot be scheduled because resources are exhausted, the scheduler preempts lower-priority pods to make room for it.
- Creating a priority which can be used by a pod:

```yml
# Create a priority
apiVersion: scheduling.k8s.io/v1
kind: PriorityClass
metadata:
  name: high-priority
value: 1000000
globalDefault: false
description: "High priority for critical workloads"

# Use it in a pod
apiVersion: v1
kind: Pod
metadata:
  name: critical
  labels:
    app: critical
spec:
  priorityClassName: high-priority
  containers:
  - name: nginx
    image: nginx:alpine
    resources:
      requests:
        cpu: "300m"
```

- If a PriorityClass has `preemptionPolicy: Never`, no pods are evicted when trying to schedule it. Its deployed with a high priority once the node pressure is released.
- By default, the priority of a pod is 0
- PriorityClass is only used by a scheduler. Eviction occurs based on priority values only when a node is under pressure and a critical pod needs to be deployed.
- QoS, on the other hand, is used by the kubelet to evict pods purely due to soft/hard resource limit breach
- A pod with Priority = 1,000,000 and QoS = BestEffort, is still much more vulnerable to memory-pressure eviction than a Guaranteed Pod.


### terminationGracePeriodSeconds

#### Kubernetes termination

When Kubernetes terminates a Pod:

```text
Pod termination
      │
      ▼
   kubelet
      │
      │ SIGTERM
      ▼
Container PID 1
      │
      │ graceful cleanup
      │
      ▼
   process exits
      │
      │ if still alive after
      │ terminationGracePeriodSeconds
      ▼
    SIGKILL
```

`terminationGracePeriodSeconds` gives the application time to shut down gracefully.

The normal sequence is:

```text
SIGTERM → cleanup → exit
                  │
                  └── timeout → SIGKILL
```

#### The application should handle SIGTERM

For a well-behaved Kubernetes application:

```text
SIGTERM
   │
   ▼
Application
   │
   ├── stop accepting new work
   ├── finish in-flight work
   ├── stop workers
   ├── close connections
   ├── flush state
   └── exit
```

Don't put substantial cleanup directly inside the signal handler. The handler should generally set a flag, and normal application code performs the shutdown.

#### Parent and child processes

Killing a parent **does not normally kill its children**.

For example:

```text
Parent
 ├── Child 1
 └── Child 2
```

If the parent dies, children can become orphaned and get reparented.

In C, the parent should explicitly terminate and wait for its children:

```c
kill(child, SIGTERM);
waitpid(child, &status, 0);
```

`waitpid()` is important because it **reaps** the child and prevents it from remaining as a zombie.

A good application shutdown pattern is:

```text
Parent receives SIGTERM
          │
          ▼
   stop parent work
          │
          ▼
 SIGTERM → Child 1
 SIGTERM → Child 2
          │
          ▼
 waitpid(Child 1)
 waitpid(Child 2)
          │
          ▼
   parent cleanup
          │
          ▼
        exit
```

#### PID namespaces are the key concept

A container normally has its own **PID namespace**.

From inside the container:

```text
Container PID namespace

PID 1  parent
 ├── PID 2  child
 └── PID 3  child
```

From the host, those are different PIDs:

```text
Host PID namespace

PID 1       systemd
   │
   └── PID 5000    container PID 1
          ├── PID 5001
          └── PID 5002
```

So:

> **Container PID 1 ≠ Host PID 1.**

---

#### What happens when a non-PID-1 parent dies?

Suppose:

```text
Container

PID 1  init
  │
  └── PID 20  parent
        ├── PID 21  child
        └── PID 22  child
```

If PID 20 dies:

```text
PID 1  init
 ├── PID 21  child
 └── PID 22  child
```

The children are **reparented to PID 1 of their PID namespace**.

They don't suddenly become children of the host's PID 1.

#### Special case: container PID 1 dies

This is the important exception.

If:

```text
Container PID namespace

PID 1  parent
 ├── PID 2
 └── PID 3
```

and PID 1 dies, Linux does **not** simply reparent PID 2 and PID 3 to the host's PID 1.

Instead, the kernel terminates the remaining processes in that PID namespace.

```text
PID 1 dies
    │
    ▼
PID 2 ──► killed
PID 3 ──► killed
    │
    ▼
PID namespace terminates
```

So processes don't escape their container's PID namespace.

#### Why PID 1 matters

This is why a container is ideally structured as:

```text
Container
   │
   └── PID 1: application
```

rather than unnecessarily:

```text
Container
   │
   └── PID 1: shell/wrapper
          │
          └── application
```

If your application genuinely needs child processes, that's fine:

```text
PID 1: application
   ├── worker 1
   ├── worker 2
   └── worker 3
```

But the parent should explicitly manage their lifecycle.
