All control plane components run as static pods under /etc/kubernetes/manifests

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
