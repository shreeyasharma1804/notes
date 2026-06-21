### Probes

#### StartupProbe

```
startupProbe:
  httpGet:
    path: /healthz
    port: 8080
  periodSeconds: 10
  failureThreshold: 30
```

The kubelet executes the command httpGet every periodSeconds and tolerates failureThreshold number of failures. This provides a slow pod some time to start. After the threshold exceeds, the container is restarted

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

- Mutating admission policy


### Pod Metrics

```bash
kubectl top pods
```
