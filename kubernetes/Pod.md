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

- The container setting:

```yaml
securityContext:
  privileged: true
```

Allows a pod to run with all linux capabilities.

Keep this setting to false, also, use mutating admission hooks to turn it to false if an application requests true

- Capabilities

To set the capabilities of a pod:

```yml
securityContext:
  capabilities:
    add:
    - NET_ADMIN
    - SYS_TIME
    drop:
    - ALL
```

To check the capabilities inside a container:

```
kubectl exec -it <pod-name> -- sh
cat /proc/1/status | grep -i cap
capsh --decode=<capability hex value>
```

The capabilities are user namespace scoped

### Pod Security Standards (PSS)

Kubernetes uses **Pod Security Admission (PSA)** to enforce security rules on pods. The rules are grouped into three levels:

```text
Privileged  →  Baseline  →  Restricted
Least Secure             Most Secure
```

`privileged: true`: Allows almost all capabilities to the pod
`runAsRootL true`: The pod can run as uid 0 mapping to the host

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

Namespace labels determine the policy:

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

Example rejection:

```text
violates PodSecurity "baseline:latest":
non-default capabilities (SYS_PTRACE)
```

#### Important commands

Check namespace policy:

```bash
kubectl get ns --show-labels
```

Enable Baseline:

```bash
kubectl label ns demo \
  pod-security.kubernetes.io/enforce=baseline
```

Enable Restricted:

```bash
kubectl label ns demo \
  pod-security.kubernetes.io/enforce=restricted
```

Test without enforcing:

```yaml
pod-security.kubernetes.io/warn: restricted
pod-security.kubernetes.io/audit: restricted
```

### Pod Metrics

```bash
kubectl top pods
```
