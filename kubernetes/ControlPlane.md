- All control plane components run as static pods under /etc/kubernetes/manifests
- All APIs are declarative

### How does resource conciliation work

```
Pod created
    ↓
API Server stores Pod in etcd
    ↓
Scheduler and Controllers receive watch notifications (vai SSE)
    ↓
Scheduler chooses a node
    ↓
Scheduler updates Pod.spec.nodeName
    ↓
API Server stores updated Pod
    ↓
Kubelet on that node receives watch notification
    ↓
Kubelet creates containers via container runtime
    ↓
Kubelet updates Pod status
```

### What if a node crashes

```
Node crashes
    ↓
Kubelet stops sending heartbeats
    ↓
Node Controller notices missing heartbeats
    ↓
Node marked NotReady
    ↓
Pods on that node become unavailable
    ↓
Controllers notice fewer replicas than desired
    ↓
Controllers create replacement Pods
    ↓
Scheduler schedules replacements
    ↓
New kubelets create replacement Pods
```

### Kube-Api Server

```yml
apiVersion: v1
kind: Pod
metadata:
  annotations:
    kubeadm.kubernetes.io/kube-apiserver.advertise-address.endpoint: 172.16.0.2:6443
  labels:
    component: kube-apiserver   
    tier: control-plane                                 # Not a required field
  name: kube-apiserver
  namespace: kube-system
spec:
  containers:
  - command:
    - kube-apiserver
    - --advertise-address=172.16.0.2                    # Address used by other kubelets to connect to the API server             
    - --allow-privileged=true                           # Allows the privileged: true setting in pods. Misuse is avoided through admission hooks
    - --authorization-mode=Node,RBAC
    - --client-ca-file=/etc/kubernetes/pki/ca.crt       # cacerts for authorizing the clients
    - --enable-admission-plugins=NodeRestriction        
    - --enable-bootstrap-token-auth=true
    - --etcd-cafile=/etc/kubernetes/pki/etcd/ca.crt     # etcd root certificate must belong to this trust store
    - --etcd-certfile=/etc/kubernetes/pki/apiserver-etcd-client.crt  # certificate and private key that the API server presents to etcd during the TLS handshake for mutual TLS
    - --etcd-keyfile=/etc/kubernetes/pki/apiserver-etcd-client.key
    - --etcd-servers=https://127.0.0.1:2379
    - --kubelet-client-certificate=/etc/kubernetes/pki/apiserver-kubelet-client.crt    # certificate and private key that the API server presents to kubelets during the TLS handshake for mutual TLS
    - --kubelet-client-key=/etc/kubernetes/pki/apiserver-kubelet-client.key
    - --kubelet-preferred-address-types=InternalIP,ExternalIP,Hostname
    - --proxy-client-cert-file=/etc/kubernetes/pki/front-proxy-client.crt
    - --proxy-client-key-file=/etc/kubernetes/pki/front-proxy-client.key
    - --requestheader-allowed-names=front-proxy-client
    - --requestheader-client-ca-file=/etc/kubernetes/pki/front-proxy-ca.crt
    - --requestheader-extra-headers-prefix=X-Remote-Extra-
    - --requestheader-group-headers=X-Remote-Group
    - --requestheader-username-headers=X-Remote-User
    - --secure-port=6443                                                                # The HTTPS port to listen on
    - --service-account-issuer=https://kubernetes.default.svc.cluster.local             # Issuer value of JWT tokens
    - --service-account-key-file=/etc/kubernetes/pki/sa.pub
    - --service-account-signing-key-file=/etc/kubernetes/pki/sa.key                     
    - --service-cluster-ip-range=10.96.0.0/12
    - --tls-cert-file=/etc/kubernetes/pki/apiserver.crt
    - --tls-private-key-file=/etc/kubernetes/pki/apiserver.key
    - --kubernetes-service-node-port=32222
    image: registry.k8s.io/kube-apiserver:v1.36.1
    imagePullPolicy: IfNotPresent
    livenessProbe:
      failureThreshold: 8
      httpGet:
        host: 172.16.0.2
        path: /livez
        port: probe-port
        scheme: HTTPS
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 15
    name: kube-apiserver
    ports:
    - containerPort: 6443
      name: probe-port
      protocol: TCP
    readinessProbe:
      failureThreshold: 3
      httpGet:
        host: 172.16.0.2
        path: /readyz
        port: probe-port
        scheme: HTTPS
      periodSeconds: 1
      timeoutSeconds: 15
    resources:
      requests:
        cpu: 250m
    startupProbe:
      failureThreshold: 24
      httpGet:
        host: 172.16.0.2
        path: /livez
        port: probe-port
        scheme: HTTPS
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 15
    volumeMounts:
    - mountPath: /etc/ssl/certs
      name: ca-certs
      readOnly: true
    - mountPath: /etc/ca-certificates
      name: etc-ca-certificates
      readOnly: true
    - mountPath: /etc/kubernetes/pki
      name: k8s-certs
      readOnly: true
    - mountPath: /usr/local/share/ca-certificates
      name: usr-local-share-ca-certificates
      readOnly: true
    - mountPath: /usr/share/ca-certificates
      name: usr-share-ca-certificates
      readOnly: true
  hostNetwork: true
  priority: 2000001000
  priorityClassName: system-node-critical
  securityContext:
    seccompProfile:
      type: RuntimeDefault
  volumes:
  - hostPath:
      path: /etc/ssl/certs
      type: DirectoryOrCreate
    name: ca-certs
  - hostPath:
      path: /etc/ca-certificates
      type: DirectoryOrCreate
    name: etc-ca-certificates
  - hostPath:
      path: /etc/kubernetes/pki
      type: DirectoryOrCreate
    name: k8s-certs
  - hostPath:
      path: /usr/local/share/ca-certificates
      type: DirectoryOrCreate
    name: usr-local-share-ca-certificates
  - hostPath:
      path: /usr/share/ca-certificates
      type: DirectoryOrCreate
    name: usr-share-ca-certificates
status: {}
```

- Node Authorization: This is applicable when a kubelet tries to access resources. The node authorizer ensures that the kubelet can only access the resources which are scheduled on it/ refernced by a resource scheduled on it.

- NodeRestriction is an admission plugin that restricts what authenticated kubelets (system:node:<node-name>) are allowed to create, update, or delete.

- --enable-bootstrap-token-auth=true allows new kubelets to authenticate to the API server using a bootstrap token before they have their own client certificate.

- kubelet-preferred-address-types: Each node defines the InternalIP, ExternalIP and HostName which the kube-api server can use to call it.

- proxy-client-cert-file: Sent by the kube-api server when it acts as a proxy. Example, when a user runs top, kube-api server forwars this request to the metrics server and authenticates itself using this certificate and key.


| Property | Usage |
|----------|--------|
| advertise-address | The API server address used by the other components |
| secure-port | The port on which the API server listens |
| tls-cert-file and tls-cert-key | The certs and the keys used for TLS when connecting to API server |
| client-ca-file | The ca certs which API server trusts |
| service-cluster-ip-range | The range of IPs from where the cluster IP can be defined |
| kubernetes-service-node-port | The allowed port to be used in node port|
| allow-privileged | Allows the privileged: true setting in pods |
| etcd-servers | etcd server locations |
| etcd-certfile and etcd-keyfile | The certs which API server uses to prove its identity to etcd server |
| etcd-cafile | The certificate presented by etcd should be in this truststore |
| kubelet-client-certificate and kubelet-client-certificate | The certs which API server uses to prove its identity to kubelets |
| proxy-client-cert-file and proxy-client-key-file | The certs which API server uses to prove its identity to metrics server |
| requestheader-allowed-names | Not sent as a header, the allowed CNs of the cert sent by a 3rd party server like metrics server |
| requestheader-client-ca-file | The trust store to be used to authenticate 3rd party servers like metrics server |
| requestheader-username-headers and requestheader-group-headers | The user and group name sent in the headers from API server to 3rd party servers |
| service-account-issuer | The issuer field of JWT tokens |
| service-account-signing-key-file and service-account-key-file | The public and private keys used to issue and verify JWT tokens |



### Kube controller manager

```yaml
apiVersion: v1
kind: Pod
metadata:
  labels:
    component: kube-controller-manager
    tier: control-plane
  name: kube-controller-manager
  namespace: kube-system
spec:
  containers:
  - command:
    - kube-controller-manager
    - --allocate-node-cidrs=true            # The controller assigns a pod cidr range to a node from the cluster-cidr range
    - --authentication-kubeconfig=/etc/kubernetes/controller-manager.conf
    - --authorization-kubeconfig=/etc/kubernetes/controller-manager.conf
    - --bind-address=127.0.0.1              # The address of controller manager is often local becuase it is an internal component
    - --client-ca-file=/etc/kubernetes/pki/ca.crt   # The ca file used to authenticate the clients connecting to it.
    - --cluster-cidr=10.244.0.0/16          # This should not overalp with the cluster-service-ip range
    - --cluster-name=kubernetes
    - --cluster-signing-cert-file=/etc/kubernetes/pki/ca.crt       # The cert used to sign all the certs for the cluster
    - --cluster-signing-key-file=/etc/kubernetes/pki/ca.key
    - --controllers=*,bootstrapsigner,tokencleaner
    - --kubeconfig=/etc/kubernetes/controller-manager.conf
    - --leader-elect=true
    - --requestheader-client-ca-file=/etc/kubernetes/pki/front-proxy-ca.crt
    - --root-ca-file=/etc/kubernetes/pki/ca.crt
    - --service-cluster-ip-range=10.96.0.0/12
    - --use-service-account-credentials=true
    image: registry.k8s.io/kube-controller-manager:v1.36.1
    imagePullPolicy: IfNotPresent
    livenessProbe:
      failureThreshold: 8
      httpGet:
        host: 127.0.0.1
        path: /healthz
        port: probe-port
        scheme: HTTPS
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 15
    name: kube-controller-manager
    ports:
    - containerPort: 10257
      name: probe-port
      protocol: TCP
    resources:
      requests:
        cpu: 200m
    startupProbe:
      failureThreshold: 24
      httpGet:
        host: 127.0.0.1
        path: /healthz
        port: probe-port
        scheme: HTTPS
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 15
    volumeMounts:
    - mountPath: /etc/ssl/certs
      name: ca-certs
      readOnly: true
    - mountPath: /etc/ca-certificates
      name: etc-ca-certificates
      readOnly: true
    - mountPath: /etc/kubernetes/pki
      name: k8s-certs
      readOnly: true
    - mountPath: /etc/kubernetes/controller-manager.conf
      name: kubeconfig
      readOnly: true
    - mountPath: /usr/local/share/ca-certificates
      name: usr-local-share-ca-certificates
      readOnly: true
    - mountPath: /usr/share/ca-certificates
      name: usr-share-ca-certificates
      readOnly: true
  hostNetwork: true
  priority: 2000001000
  priorityClassName: system-node-critical
  securityContext:
    seccompProfile:
      type: RuntimeDefault
  volumes:
  - hostPath:
      path: /etc/ssl/certs
      type: DirectoryOrCreate
    name: ca-certs
  - hostPath:
      path: /etc/ca-certificates
      type: DirectoryOrCreate
    name: etc-ca-certificates
  - hostPath:
      path: /etc/kubernetes/pki
      type: DirectoryOrCreate
    name: k8s-certs
  - hostPath:
      path: /etc/kubernetes/controller-manager.conf
      type: FileOrCreate
    name: kubeconfig
  - hostPath:
      path: /usr/local/share/ca-certificates
      type: DirectoryOrCreate
    name: usr-local-share-ca-certificates
  - hostPath:
      path: /usr/share/ca-certificates
      type: DirectoryOrCreate
    name: usr-share-ca-certificates
status: {}
```

| Property | Usage |
|-----------|---------|
| bind-address | The IP address the controller listens on |
| cluster-cidr | The cluster CIDR range
| allocate-node-cidrs | Controller allocates node CIDRs (which decide the pod IPs) from the cluster CIDR range |
| leader-elect | Leader election for HA setups |
| cluster-signing-cert-file and cluster-signing-key-file | The CA cert and key which is used to sign all the certificates in the cluster. This is a seperation of concerns, all components connect to the api-server and the api-server verifies the certs. The controller only issues the certs |
| root-ca-file | The root certificate of the cluster used to imbed in all kubeconfigs |
| requestheader-client-ca-file | The truststore location for 3rd party connections from controller to 3rd party servers |
| use-service-account-credentials | Use differnet service tokens for different controllers |

### Kube Scheduler

```yml
apiVersion: v1
kind: Pod
metadata:
  labels:
    component: kube-scheduler
    tier: control-plane
  name: kube-scheduler
  namespace: kube-system
spec:
  containers:
  - command:
    - kube-scheduler
    - --authentication-kubeconfig=/etc/kubernetes/scheduler.conf
    - --authorization-kubeconfig=/etc/kubernetes/scheduler.conf
    - --bind-address=127.0.0.1
    - --kubeconfig=/etc/kubernetes/scheduler.conf
    - --leader-elect=true
    image: registry.k8s.io/kube-scheduler:v1.36.1
    imagePullPolicy: IfNotPresent
    livenessProbe:
      failureThreshold: 8
      httpGet:
        host: 127.0.0.1
        path: /livez
        port: probe-port
        scheme: HTTPS
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 15
    name: kube-scheduler
    ports:
    - containerPort: 10259
      name: probe-port
      protocol: TCP
    readinessProbe:
      failureThreshold: 3
      httpGet:
        host: 127.0.0.1
        path: /readyz
        port: probe-port
        scheme: HTTPS
      periodSeconds: 1
      timeoutSeconds: 15
    startupProbe:
      failureThreshold: 24
      httpGet:
        host: 127.0.0.1
        path: /livez
        port: probe-port
        scheme: HTTPS
      initialDelaySeconds: 10
      periodSeconds: 10
      timeoutSeconds: 15
    volumeMounts:
    - mountPath: /etc/kubernetes/scheduler.conf
      name: kubeconfig
      readOnly: true
  hostNetwork: true
  priority: 2000001000
  priorityClassName: system-node-critical
  securityContext:
    seccompProfile:
      type: RuntimeDefault
  volumes:
  - hostPath:
      path: /etc/kubernetes/scheduler.conf
      type: FileOrCreate
    name: kubeconfig
status: {}
```
