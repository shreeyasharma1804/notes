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

### Pod Metrics

```bash
kubectl top pods
```
