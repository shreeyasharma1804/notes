### kubeconfig

- clusters: Contains the embedded cluster root certificate, the cluster name and the API server location
- users: Contains the username, the public and private key of the user
- contexts: Contains a context name, cluster name and user
- current-context: One of the context is set as the current context.

```yml
apiVersion: v1
clusters:
- cluster:
    certificate-authority-data: <certificate>
    server: https://172.16.0.2:6443
  name: kubernetes
contexts:
- context:
    cluster: kubernetes
    user: system:node:cplane-01
  name: system:node:cplane-01@kubernetes
current-context: system:node:cplane-01@kubernetes
kind: Config
users:
- name: system:node:cplane-01
  user:
    client-certificate: /var/lib/kubelet/pki/kubelet-client-current.pem
    client-key: /var/lib/kubelet/pki/kubelet-client-current.pem
```

### Roles

- A role connects a resource(eg, pod) to a permission(eg, get)
- Permissiosn: `get, list, watch, create, update, patch, delete`. Other actions like describe are a subset of these permissions.
- `get`: Only gets one particular object, example, `kubectl get pods nginx`
- `list`: List all resources
- Roles define a namespace, ClusterRoles are applicable across the cluster(used by control plane components)

```yml
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata:
  name: pod-reader
  namespace: dev

rules:
- apiGroups: [""]
  resources: ["pods"]
  verbs: ["get","list","watch"]
```
