## Setting up K8s with kubeadm

- kubelet requires a container runtime (containerd) and swapping to be disabled
- Enable required kernel modules:

```bash
sudo modprobe overlay
sudo modprobe br_netfilter
```

- Enable IP forwarding

```bash
sudo sysctl -w net.ipv4.ip_forward=1
```

- Get the required version to be installed

```bash
KUBE_VERSION=$(curl -fsL https://dl.k8s.io/release/stable.txt)
```

- Add the apt repository

```bash
curl -fsSL https://pkgs.k8s.io/core:/stable:/${KUBE_VERSION%.*}/deb/Release.key | sudo gpg --dearmor --yes -o /etc/apt/keyrings/kubernetes-apt-keyring.gpg
echo "deb [signed-by=/etc/apt/keyrings/kubernetes-apt-keyring.gpg] https://pkgs.k8s.io/core:/stable:/${KUBE_VERSION%.*}/deb/ /" | sudo tee /etc/apt/sources.list.d/kubernetes.list
```

- Install kubelet, kubectl, kubeadm

```bash
sudo apt-get update
sudo apt-get install -y \
    kubeadm=${KUBE_VERSION#v}-* \
    kubelet=${KUBE_VERSION#v}-* \
    kubectl=${KUBE_VERSION#v}-*
```

- Lock to avoid accidental upgrade

```bash
sudo apt-mark hold kubeadm kubelet kubectl
```

- Initialize the control plane

```
sudo kubeadm init \
    --pod-network-cidr=10.244.0.0/16 \
    --kubernetes-version=${KUBE_VERSION}
```

- Installed static pods (coreDNS is deployed as normal deployment and not a static pod)

```
laborant@cplane:manifests$ pwd
/etc/kubernetes/manifests

laborant@cplane:manifests$ ls -la
total 24
drwxrwxr-x 2 root root 4096 Aug 30 05:58 .
drwxrwxr-x 4 root root 4096 Aug 30 05:58 ..
-rw-r--r-- 1 root root    0 Aug 26 11:11 .kubelet-keep
-rw------- 1 root root 2580 Aug 30 05:58 etcd.yaml
-rw------- 1 root root 3944 Aug 30 05:58 kube-apiserver.yaml
-rw------- 1 root root 3229 Aug 30 05:58 kube-controller-manager.yaml
-rw------- 1 root root 1726 Aug 30 05:58 kube-scheduler.yaml
```

- The cplane node stays in a NotReady state until a CNI is installed
- Install flannel

```
kubectl apply -f https://github.com/flannel-io/flannel/releases/latest/download/kube-flannel.yml
```

- Get the commands to join the worker node to the cluster

```
kubeadm token create --print-join-command
```

## High Availability

- The role of a node is just a label (cplane/worker)
- `sudo kubeadm init` command adds these labels when bootstrapping the cluster

### API Server

- Multiple API servers can run on multiple nodes of a cluster
- The API server pod uses the host network namespace. Thus it does not need service/nodeport to be reachable
- This also allows to use a common domain for the API Server with NGINX for loadbalancing across node:<api-server-port>
- Check the API server location:

```bash
kubectl cluster-info
```

- The API Servers can also be made reachable via VRRP (Also, the current master can be checked via `ip address`)

```
kubectl
   |
   | https://k8s-api.example.com:6443
   |
   v
/etc/hosts
   |
   | 10.0.0.100
   v
VRRP VIP
   |
   | currently owned by CP-01
   v
NGINX on CP-01
   |
   | load balances
   +----------+----------+
   |          |          |
   v          v          v
 CP-01      CP-02      CP-03
 :6443      :6443      :6443
```

- After the 1st node has been initialized via kubeadm, the other cplane nodes can join via the `kubeadm join <clane>:6443 --control-plane`

### Scheduler and Controller

- Both these components support leader election
- Lets say one cluster has n control plane nodes, the nodes try to renew a lease object. The node which renews it becomes the current leader
- These components then watch the etcd events independently
