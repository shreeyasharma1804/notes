Kubeproxy only alters the host's routing tables

### Inside a pod

### 2 pods on the same node

### 2 pods on different nodes 

### Service: ClusterIP

- A ClusterIP assigns an IP to a set of pods based on the selector from the cluster-ip cidr range.
- CorDNS resolves the ClusterIP service name to the ClusterIP

| Part            | Meaning                        | Defined where?                        |
| --------------- | ------------------------------ | ------------------------------------- |
| `default`       | Namespace                      | Namespace of the Service              |
| `svc`           | Indicates a Service DNS record | Kubernetes DNS convention             |
| `cluster.local` | Cluster DNS domain             | DNS configuration (CoreDNS / kubelet) |


```bash
NAME             TYPE        CLUSTER-IP     EXTERNAL-IP   PORT(S)   AGE   SELECTOR
hi-bye-service   ClusterIP   10.43.82.235   <none>        80/TCP    9d    app=hi-bye-app

# Inside a debug pod
wget http://10.43.82.235/hi
wget http://hi-bye-service/hi
wget http://hi-bye-service.default.svc.cluster.local/hi
```

 Internals:

 - wget http://10.43.82.235/hi
 - No DNS resolution required here
 -
```bash
ip route
default via 10.42.0.1 dev eth0
```
  
### MetalLB

MetalLB creates a LoadBalancer in the cluster which answers to external IPs and redirects the traffic to the pods

```yml
apiVersion: metallb.io/v1beta1
kind: IPAddressPool
metadata:
  name: production
  namespace: metallb-system
spec:
  # Production services will go here. Public IPs are expensive, so we leased
  # just 4 of them.
  addresses:
  - 192.168.1.20-192.168.1.40

---
apiVersion: metallb.io/v1beta1
kind: L2Advertisement
metadata:
  name: local-l2
  namespace: metallb-system
```

In this example, MetalLB picks up one IP from the available list, and broadcasts it using ARP(Layer 2)/ BGP(Layer 3)

Created LB:

```bash
kube-system      traefik                   LoadBalancer   10.43.251.160   192.168.1.20   80:32231/TCP,443:30560/TCP   141m
```
