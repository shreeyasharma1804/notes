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
```bash
ip route
default via 10.42.0.1 dev eth0
```
- This IP belongs to the cni interface on the host (the veth interface of the pod and cni interface on the host are connected by a bridge network)
- PREROUTING rules are applied to this packet
```bash
Chain PREROUTING (policy ACCEPT 16 packets, 2322 bytes)
 pkts bytes target     prot opt in     out     source               destination
   84  7386 KUBE-SERVICES  0    --  *      *       0.0.0.0/0            0.0.0.0/0            /* kubernetes service portals */

Chain KUBE-SERVICES (2 references)
 pkts bytes target     prot opt in     out     source               destination
    9   540 KUBE-SVC-LC4RP4AY6E35KNJG  6    --  *      *       0.0.0.0/0            10.43.82.235         /* default/hi-bye-service cluster IP */ tcp dpt:80

# One pod is chosen randomly
Chain KUBE-SVC-LC4RP4AY6E35KNJG (1 references)
 pkts bytes target     prot opt in     out     source               destination
    0     0 KUBE-MARK-MASQ  6    --  *      *      !10.42.0.0/16         10.43.82.235         /* default/hi-bye-service cluster IP */ tcp dpt:80
    2   120 KUBE-SEP-Z7QH5NTGHAPVKVO6  0    --  *      *       0.0.0.0/0            0.0.0.0/0            /* default/hi-bye-service -> 10.42.0.4:8000 */ statistic mode random probability 0.33333333349
    3   180 KUBE-SEP-LIGFT5R6A6LUJPH4  0    --  *      *       0.0.0.0/0            0.0.0.0/0            /* default/hi-bye-service -> 10.42.0.5:8000 */ statistic mode random probability 0.50000000000
    4   240 KUBE-SEP-BM4LI7HKRJOEKMYH  0    --  *      *       0.0.0.0/0            0.0.0.0/0            /* default/hi-bye-service -> 10.42.0.6:8000 */

# DNAT is performed
Chain KUBE-SEP-Z7QH5NTGHAPVKVO6 (1 references)
 pkts bytes target     prot opt in     out     source               destination
    2   120 DNAT       6    --  *      *       0.0.0.0/0            0.0.0.0/0            /* default/hi-bye-service */ tcp to:10.42.0.4:8000

# On the host
ip route get 10.42.0.4
10.42.0.4 dev cni0 src 10.42.0.1 uid 1000

# The cni plugin then forwards the packet to the correct pod
```

### Service: NodePort

```bash
hi-bye-nodeport   NodePort    10.43.20.7     <none>        80:30080/TCP   3m27s   app=hi-bye-app

# Working
NodeIP:30080
    ↓
Service ClusterIP:80
    ↓
PodIP:8000

# Inside a debug pod
wget http://10.43.20.7/hi

# On the host
curl 192.168.1.9:30080/hi
```

Internals

```
PREROUTING -> KUBE-SERVICES

Chain KUBE-SERVICES (2 references)
 pkts bytes target     prot opt in     out     source               destination
    1    60 KUBE-SVC-QYMDJKV4WEDC2IPH  6    --  *      *       0.0.0.0/0            10.43.20.7           /* default/hi-bye-nodeport cluster IP */ tcp dpt:80

Chain KUBE-SVC-QYMDJKV4WEDC2IPH (2 references)
 pkts bytes target     prot opt in     out     source               destination
    0     0 KUBE-MARK-MASQ  6    --  *      *      !10.42.0.0/16         10.43.20.7           /* default/hi-bye-nodeport cluster IP */ tcp dpt:80
    1    60 KUBE-SEP-AISHG3UCUCO2DWAC  0    --  *      *       0.0.0.0/0            0.0.0.0/0            /* default/hi-bye-nodeport -> 10.42.0.4:8000 */ statistic mode random probability 0.33333333349
    0     0 KUBE-SEP-HBLCQNEKJ4OOHRMF  0    --  *      *       0.0.0.0/0            0.0.0.0/0            /* default/hi-bye-nodeport -> 10.42.0.5:8000 */ statistic mode random probability 0.50000000000
    2   120 KUBE-SEP-PRS734IZISVHMPCG  0    --  *      *       0.0.0.0/0            0.0.0.0/0            /* default/hi-bye-nodeport -> 10.42.0.6:8000 */

# DNAT
Chain KUBE-SEP-AISHG3UCUCO2DWAC (1 references)
 pkts bytes target     prot opt in     out     source               destination
    1    60 KUBE-MARK-MASQ  0    --  *      *       10.42.0.4            0.0.0.0/0            /* default/hi-bye-nodeport */
    1    60 DNAT       6    --  *      *       0.0.0.0/0            0.0.0.0/0            /* default/hi-bye-nodeport */ tcp to:10.42.0.4:8000
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
