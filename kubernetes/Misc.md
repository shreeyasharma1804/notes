- Mutating Admission policy: https://kubernetes.io/docs/reference/access-authn-authz/mutating-admission-policy/
- Validating Admission policy: https://kubernetes.io/docs/reference/access-authn-authz/validating-admission-policy/

- If a PVC directory has permissions such that the runAsUser UID cannot access it, the mount cannot be read/written to

- debug pod: `kubectl debug -it <target pod> --image=busybox:latest`

```bash
kubectl debug -it \
    --profile baseline \
    --image ghcr.io/iximiuz/labs/alpine:3 \
    <target pod>
```

Create the debug pod within the PID namespace of --target container
 
```bash
kubectl debug -it \
    --profile baseline \
    --image ghcr.io/iximiuz/labs/alpine:3 \
    --target app \
    slim
```
- exec pod:

```bash
kubectl exec -n <namespace> <pod> -c <container> -- <command>
```

- Annotations store metadata not used for selection by K8s

### Tools

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

Metrics server uses the above endpoint to report the resource usage through the below command:

```bash
kubectl top pods -A
```

- VPA

VPA pods aggregate the metrics data, and in recommendation mode, suggests the resource usage for the containers

- Goldilocks

Uses the recommendations from the VPA to suggest the resource usage, automatically creates the VPA pods for the namespaces labelled with the relevant goldilocks label.
Open the dashboard using:

```bash
kubectl port-forward svc/goldilocks-dashboard \
  -n goldilocks 8080:80
```

- Popeye

Static analysis of pod configs

- kube-capacity

Total requests and limits of all pods on a node:

```bash
└❯ kubectl resource-capacity
NODE     CPU REQUESTS   CPU LIMITS    MEMORY REQUESTS   MEMORY LIMITS
pop-os   545m (4%)      1600m (13%)   2326Mi (15%)      2926Mi (19%)
```

- kubectl neat

```bash
kubectl get pod hi-bye-app-784587b8b7-fwpgp -o yaml | kubectl neat
```

- kubevious

Overall resource dashboard with static analysis

- dive

Image layer analysis
