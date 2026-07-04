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

### Role

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

### RoleBinding

- A rolebinding connects a role to a user
- The subjects.name is the CN of the certificate used for authentication. O is the group name
- ClusterRoleBindings are applicable across the cluster

```yml
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata:
  name: pod-reader-binding
  namespace: dev

subjects:
- kind: User
  name: alice

roleRef:
  kind: Role
  name: pod-reader
  apiGroup: rbac.authorization.k8s.io
```

### User Creation

```bash
# Create the keys
openssl genrsa -out shreeya.key 2048

# Create CSr
openssl req -new \
  -key shreeya.key \
  -out shreeya.csr \
  -subj "/CN=shreeya/O=developers"

# Encode the CSR to base64 format
 cat shreeya.csr | base64 -w0

# Create CSR object

apiVersion: certificates.k8s.io/v1
kind: CertificateSigningRequest
metadata:
  name: shreeya
spec:
  request: LS0tLS1CRUdJTiBDRVJUSUZJQ0FURSBSRVFVRVNULS0tLS0KTUlJQ2JEQ0NBVlFDQVFBd0p6RVFNQTRHQTFVRUF3d0hjMmh5WldWNVlURVRNQkVHQTFVRUNnd0taR1YyWld4dgpjR1Z5Y3pDQ0FTSXdEUVlKS29aSWh2Y05BUUVCQlFBRGdnRVBBRENDQVFvQ2dnRUJBTGo5ZDdXWUo2OG5LeFkyCkUranpxNkdqM1BRZGFwQ09yeGd4N09IMklyZVJDUHhIT0EvSjJnTjdFcE00cU9yUjB6Q245cTRuZk5DWGg4Y00KVitFVkVuOTFrTC9TVWNtQkE0VnlhWTBWYWNDQW53cUI5TTRzeFF5b3dGTytlNTRVT21QZ2JJa2ZUVXpBT3hLSQpVRzQyR2J0ZCtid25QZDVMekZuMkJicVdWUmF0K05yRkRyUlZHM3VwSk0xbUtudC9SdHp0WWpXQXRLWk9oMWdKCkxONnF1MWZ3aXJ4VDRQOTlEZC9Zb1BEYnRjaGZMaG5kYWpwdlNMb2puUTcyU0wwUWF3RUJVSExqLzZZYWo4djMKS1FMcjl2eG1jR3cxKyt3R1lFZGhTNUI4aHEyMXFCUzFzaCtKYmxwbVVWbWlBaVpBTEJxWVlRWEpGNU84b0xDUQo5T0lHZkJNQ0F3RUFBYUFBTUEwR0NTcUdTSWIzRFFFQkN3VUFBNElCQVFCOUcrOHorVWNLWjFZemM4R0d3WkgxCjlmUmFDMWFKQjFwSWprNVFyaGxXa1ZJUXUvVHR0U25tdEVuVFp4TkhQUWg0cURheWlQMGRCQ2gwaEtwbFU3NTUKN0JjL2ZOSHhaNm5zYU1udjdGdDBhdmVTYnkrOG8zd3kyWVNZYlNJRDJMQmkyZkw3TWRLV250OWZyOW51Y3doTgpmWVVVV2h2SWJKaXRJd0o2czRnSFJ6aVEzMHJyRTlDaVhWUlJVc2w2MUFOdUZnRmMzQXVXU0tjeGpTdDFveHU2CmFxaU8yUmgxT0t5dFJzYmdzT3hUblpjQmVCT0I4UjVEWHBrbVRaS1k2MUdNNnNYeXVzeWd2TkEvTkpTOGdzNk8KWXZPQ3NhbW9RaVpkVllLN1o0ekxhMklOR29hbEoyTW4yZUU5MW5EZkR5cXV5Z0xUcnIwNTF0QlQ1a051RXZrZwotLS0tLUVORCBDRVJUSUZJQ0FURSBSRVFVRVNULS0tLS0K
  signerName: kubernetes.io/kube-apiserver-client
  usages:
  - client auth

kubectl get csr

# Approve request
kubectl certificate approve shreeya

# Get the signed certificate
kubectl get csr shreeya -o json

# Create user credentials
kubectl config set-credentials shreeya \
  --client-certificate=shreeya.crt \
  --client-key=shreeya.key

# Create context
kubectl config set-context shreeya \
  --cluster=default \
  --user=shreeya

# Check the context in ~/.kube/config

# Use the new context
kubectl config use-context shreeya
```

### Service Account

- Service account can be used in role bindings
- Create:

```yml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: prometheus
  namespace: telemetry
```

- Provide the permissions with a role binding

```yml
apiVersion: rbac.authorization.k8s.io/v1
kind: ClusterRoleBinding
metadata:
  name: prometheus

roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: prometheus

subjects:
- kind: ServiceAccount
  name: prometheus
  namespace: telemetry
```
