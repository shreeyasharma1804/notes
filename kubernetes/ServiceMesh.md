### Requirements

- mTLS
- Traffic observability
- L7 policies like allowed HTTP methods
- NetworkPolicy

### Istio

- Provides all these requirements expect NetworkPolicy
- Istio updates the iptables of the pod to redirect to the envoy proxies

```bash
crictl ps | grep <pod>
crictl inspect <containerid> | grep pid # Get the container PID
sudo nsenter -t <container PID> -n iptables -t nat -L -n -v
```

- The IP table

Ingress rules: PREROUTING
Egress rules: OUTPUT

```bash
Chain PREROUTING (policy ACCEPT 123 packets, 7380 bytes)
 pkts bytes target     prot opt in     out     source               destination
  123  7380 ISTIO_INBOUND  6    --  *      *       0.0.0.0/0            0.0.0.0/0

Chain INPUT (policy ACCEPT 123 packets, 7380 bytes)
 pkts bytes target     prot opt in     out     source               destination

Chain OUTPUT (policy ACCEPT 22 packets, 1838 bytes)
 pkts bytes target     prot opt in     out     source               destination
   22  1838 ISTIO_OUTPUT  0    --  *      *       0.0.0.0/0            0.0.0.0/0

Chain POSTROUTING (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination

Chain ISTIO_INBOUND (1 references)
 pkts bytes target     prot opt in     out     source               destination
    0     0 RETURN     6    --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:15008
    0     0 RETURN     6    --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:15090
  123  7380 RETURN     6    --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:15021
    0     0 RETURN     6    --  *      *       0.0.0.0/0            0.0.0.0/0            tcp dpt:15020
    0     0 ISTIO_IN_REDIRECT  6    --  *      *       0.0.0.0/0            0.0.0.0/0

Chain ISTIO_IN_REDIRECT (3 references)
 pkts bytes target     prot opt in     out     source               destination
    0     0 REDIRECT   6    --  *      *       0.0.0.0/0            0.0.0.0/0            redir ports 15006

Chain ISTIO_OUTPUT (1 references)
 pkts bytes target     prot opt in     out     source               destination
    0     0 RETURN     0    --  *      lo      127.0.0.6            0.0.0.0/0
    0     0 ISTIO_IN_REDIRECT  6    --  *      lo      0.0.0.0/0           !127.0.0.1            tcp dpt:!15008 owner UID match 1337
    0     0 RETURN     0    --  *      lo      0.0.0.0/0            0.0.0.0/0            ! owner UID match 1337
   22  1838 RETURN     0    --  *      *       0.0.0.0/0            0.0.0.0/0            owner UID match 1337
    0     0 ISTIO_IN_REDIRECT  6    --  *      lo      0.0.0.0/0           !127.0.0.1            tcp dpt:!15008 owner GID match 1337
    0     0 RETURN     0    --  *      lo      0.0.0.0/0            0.0.0.0/0            ! owner GID match 1337
    0     0 RETURN     0    --  *      *       0.0.0.0/0            0.0.0.0/0            owner GID match 1337
    0     0 RETURN     0    --  *      *       0.0.0.0/0            127.0.0.1
    0     0 ISTIO_REDIRECT  0    --  *      *       0.0.0.0/0            0.0.0.0/0

Chain ISTIO_REDIRECT (1 references)
 pkts bytes target     prot opt in     out     source               destination
    0     0 REDIRECT   6    --  *      *       0.0.0.0/0            0.0.0.0/0            redir ports 15001
```

- L7 Policies

```yml
apiVersion: security.istio.io/v1
kind: AuthorizationPolicy
metadata:
  name: backend-allow-get
  namespace: backend
spec:
  selector:
    matchLabels:
      app: backend
  rules:
  - to:
    - operation:
        methods: ["GET"]
```

```bash
kubectl exec -n frontend frontend -- curl http://backend-svc.backend.svc.cluster.local #Works
kubectl exec -n frontend frontend -- curl -X POST http://backend-svc.backend.svc.cluster.local #Does not work
```
