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
