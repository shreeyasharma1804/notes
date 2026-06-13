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
