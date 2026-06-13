### Kubernetes

- `kubectl tree deployment  <deployment-name>`: Shows a tree like view of all the objects created as a part of the deployment
- `kubectl stern <deployment>`: Get the logs of all the pods in a single command

- k9s
```
:po        Pods
:deploy    Deployments
:svc       Services
:ing       Ingresses
:ds        DaemonSets
:sts       StatefulSets
:cm        ConfigMaps
:secret    Secrets
:node      Nodes
:ns        Namespaces
:events    Events
:crd       CRDs
```

skin: https://github.com/catppuccin/k9s

-  metrics-server

```bash
kubectl get pods -n kube-system | grep metrics-server
```

Each kubelet exposes an API: /stats/summary which reports the resource usage of the node, pods etc

```bash
kubectl config view --raw --minify   -o jsonpath='{.users[0].user.client-certificate-data}' | base64 -d > admin.crt
kubectl config view --raw --minify   -o jsonpath='{.users[0].user.client-key-data}' | base64 -d > admin.key
curl -k --cert admin.crt --key admin.key https://192.168.1.9:10250/stats/summary
```

Usage:

```bash
kubectl top pods -A
```
