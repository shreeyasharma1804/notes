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

### Privilaged mode

The container setting:

```yaml
securityContext:
  privileged: true
```

Allows a pod to run with all linux capabilities.

### Pod Metrics

```bash
kubectl top pods
```
