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

### Endpoints

All the pod IPs a service can reach

```bash
sudo k3s kubectl get endpoints hi-bye-service
Warning: v1 Endpoints is deprecated in v1.33+; use discovery.k8s.io/v1 EndpointSlice
NAME             ENDPOINTS                                      AGE
hi-bye-service   10.42.0.4:8000,10.42.0.5:8000,10.42.0.6:8000   9d
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

### Service: Headless

- In a headless service:

```yml
spec
  clusterIP: None
```

- Instead of using a virtual IP which is loadbalanced across the Pod IPs by kube-proxy, the pod IP is returned directly by the DNS.
- This feature is used specifically in stateful applications using daemonsets.

### CoreDNS

- The CorDNS runs as a pod in the kube-system namespace.
- Every pod has the location of the DNS in the `/etc/resolv.conf` file.

### External connectivity

- Nginx ingress uses 3 resources: ingress(Define the routing rules), ingress-nginx-controller(serivce of type loadbalancer) and ingress-nginx-controller-xxx (The ingress pod)
- Ingress provides the interface for creating routing rules.
- The ingress loadbalancer service is a service for the ingress pods. It uses both ClusterIP and NodePort. In case of availability of external loadbalancer like MetalLB, an external IP is assigned to this service.
- The ingress pod(ingress-nginx-controller-xxx) contains the actual nginx process and generated nginx.conf. Since it is a deployment, it can be scaled and attached with HPA.
- There is no synchronized state between the ingress pods, they watch the API server for the ingress rules and configmaps(for nginx settings)

```bash
curl -H "Host:hi-bye.local" 192.168.1.21:80/hi
curl -H "Host:hi-bye.local" 192.168.1.9:30118/hi # Using nodeport

# Basically, 192.168.1.21:80 DNAT to ingress pod
# 192.168.1.9:30118/hi, also DNAT to ingress pod
# 10.43.196.118:80/hi, also DNAT to ingress pod
```

```bash
sudo k3s kubectl get pods -A -o wide | grep ingress
ingress-nginx    ingress-nginx-controller-7d65c586d6-zwqht   1/1     Running            1 (85m ago)    9d      10.42.0.12    pop-os   <none>           <none>

udo k3s kubectl get svc -A
NAMESPACE        NAME                                 TYPE           CLUSTER-IP      EXTERNAL-IP    PORT(S)                      AGE
ingress-nginx    ingress-nginx-controller             LoadBalancer   10.43.196.118   192.168.1.21   80:30118/TCP,443:32263/TCP   9d

sudo k3s kubectl get ingress -A
NAMESPACE   NAME             CLASS   HOSTS            ADDRESS        PORTS   AGE
default     hi-bye-ingress   nginx   hi-bye.local     192.168.1.21   80      9d
```

Internals

```bash
PREROUTING -> KUBE-SERVICES

Chain KUBE-SERVICES (2 references)
 pkts bytes target     prot opt in     out     source               destination
    0     0 KUBE-EXT-CG5I4G2RS3ZVWGLK  6    --  *      *       0.0.0.0/0            192.168.1.21         /* ingress-nginx/ingress-nginx-controller:http loadbalancer IP */ tcp dpt:80

Chain KUBE-EXT-CG5I4G2RS3ZVWGLK (3 references)
 pkts bytes target     prot opt in     out     source               destination
    0     0 KUBE-SVC-CG5I4G2RS3ZVWGLK  0    --  *      *       0.0.0.0/0            0.0.0.0/0            /* route LOCAL traffic for ingress-nginx/ingress-nginx-controller:http external destinations */ ADDRTYPE match src-type LOCAL

# Here, the packet is routed to the ingress pod
Chain KUBE-SEP-BYLCQHMLJ6HK5HFC (2 references)
 pkts bytes target     prot opt in     out     source               destination
    0     0 DNAT       6    --  *      *       0.0.0.0/0            0.0.0.0/0            /* ingress-nginx/ingress-nginx-controller:http */ tcp to:10.42.0.12:80

# The pod now routes the packet to the backedn service based on the rules
```

### MetalLB

- MetalLB assigns an external IP address to all the services of type LoadBalancer.
- The IP is assigned to all services of type LoadBalancer irrespective of the namespaces (MetalLB works cluster wide)
- MetalLB requires L2Advertisement for the IP pool
- In production, each environment has 2 pools, public and private

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

### NetworkPolicy

Decided which pods can connect to which pods both in terms of ingress and egress

```yml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: ipblock-policy
  namespace: default
spec:
  podSelector:
    matchLabels:
      app: nginx

  policyTypes:
  - Ingress
  - Egress

  ingress:
  - from:
    - ipBlock:
        cidr: 10.0.0.0/24
        except:
        - 10.0.0.5/32

  egress:
  - to:
    - ipBlock:
        cidr: 172.16.0.0/16
        except:
        - 172.16.1.0/24
```
