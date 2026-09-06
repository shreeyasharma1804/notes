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

Note: kubeadm can initialize a control plane without the etcd pod. Use this when etcd cluster needs to be bootstrapped separately (Example: etcd nodes > control plane nodes)

## Certificates

Strored at: `/etc/kubernetes/pki/`

#### ca.crt

The k8s cluster trusts all certificates signed by ca.crt

#### apiserver.crt

- The identity of the api server, signed by ca.crt
- Used when api server's receives a request and needs to prove its identity as a server

#### apiserver-kubelet-client.crt

- Also the identity of the api server, signed by ca.crt
- Used when api server's needs to send a request and prove its identity as a client

<span style="color:red">Note:</span> A control plane node also runs the kubelet, because the kubelet is responsible to run the static pods

#### Kubelet certs

- Located at `/var/lib/kubelet/pki/`
- `kubelet.crt`: Identity of the kubelet as a server
- `kubelet.key `: Identity of the kubelet as a client

#### Controller and Scheduler

- The controller connects to the api server via the file: `/etc/kubernetes/controller-manager.conf` which also contains its client certificates
- Similarly, the scheduler connects to the api server via the file: `/etc/kubernetes/scheduler-manager.conf` which also contains its client certificates

## Best Practices

- One application per namespace
- dev and admin role and role binding per namespace, to isolate access per application

## What should the cluster repo contain

- rbac
- namespaces
- telenetry
- flux/argo
- ingress


## etcd

### config file template (to be modified with the correct ansible variables)

```
name: node1

data-dir: /var/lib/etcd

listen-client-urls: https://10.0.0.11:2379
advertise-client-urls: https://10.0.0.11:2379

listen-peer-urls: https://10.0.0.11:2380
initial-advertise-peer-urls: https://10.0.0.11:2380

initial-cluster: node1=https://10.0.0.11:2380
initial-cluster-state: new
initial-cluster-token: my-etcd-cluster

cert-file: /etc/etcd/pki/node1.crt
key-file: /etc/etcd/pki/node1.key
trusted-ca-file: /etc/etcd/pki/ca.crt

peer-cert-file: /etc/etcd/pki/node1.crt
peer-key-file: /etc/etcd/pki/node1.key
peer-trusted-ca-file: /etc/etcd/pki/ca.crt
```

### Bootstrapping using ansible

#### Bootsrap one node

```yaml
---
- name: Bootstrap first etcd node
  hosts: node1
  become: true

  vars:
    etcd_name: "{{ inventory_hostname }}"
    etcd_data_dir: /var/lib/etcd
    etcd_config_dir: /etc/etcd
    etcd_config_file: /etc/etcd/etcd.conf
    etcd_bin: /usr/local/bin/etcd

  tasks:

    # ---------------------------------------------------------
    # 1. Create directories
    # ---------------------------------------------------------

    - name: Create etcd directories
      ansible.builtin.file:
        path: "{{ item }}"
        state: directory
        owner: root
        group: root
        mode: "0755"
      loop:
        - "{{ etcd_config_dir }}"
        - "{{ etcd_data_dir }}"


    # ---------------------------------------------------------
    # 2. Create etcd configuration
    # ---------------------------------------------------------

    - name: Create first-node etcd configuration
      ansible.builtin.copy:
        dest: "{{ etcd_config_file }}"
        owner: root
        group: root
        mode: "0644"
        content: |
          name: "{{ etcd_name }}"

          data-dir: "{{ etcd_data_dir }}"

          listen-client-urls: "https://0.0.0.0:2379"
          advertise-client-urls: "https://{{ inventory_hostname }}:2379"

          listen-peer-urls: "https://0.0.0.0:2380"
          initial-advertise-peer-urls: "https://{{ inventory_hostname }}:2380"

          initial-cluster: "{{ etcd_name }}=https://{{ inventory_hostname }}:2380"
          initial-cluster-state: "new"
          initial-cluster-token: "my-etcd-cluster"


    # ---------------------------------------------------------
    # 3. Create systemd service
    # ---------------------------------------------------------

    - name: Create etcd systemd service
      ansible.builtin.copy:
        dest: /etc/systemd/system/etcd.service
        owner: root
        group: root
        mode: "0644"
        content: |
          [Unit]
          Description=etcd
          Documentation=https://etcd.io/docs/
          After=network-online.target
          Wants=network-online.target

          [Service]
          Type=notify
          ExecStart={{ etcd_bin }} --config-file={{ etcd_config_file }}

          Restart=always
          RestartSec=5

          LimitNOFILE=40000

          [Install]
          WantedBy=multi-user.target


    # ---------------------------------------------------------
    # 4. Tell systemd about the new service
    # ---------------------------------------------------------

    - name: Reload systemd
      ansible.builtin.systemd:
        daemon_reload: true


    # ---------------------------------------------------------
    # 5. Start etcd
    # ---------------------------------------------------------

    - name: Enable and start etcd
      ansible.builtin.systemd:
        name: etcd.service
        enabled: true
        state: started


    # ---------------------------------------------------------
    # 6. Wait until etcd is healthy
    # ---------------------------------------------------------

    - name: Wait for etcd client port
      ansible.builtin.wait_for:
        host: "{{ inventory_hostname }}"
        port: 2379
        delay: 2
        timeout: 60


    - name: Check etcd health
      ansible.builtin.command:
        cmd: >
          /usr/local/bin/etcdctl
          --endpoints=https://{{ inventory_hostname }}:2379
          endpoint health
      register: etcd_health
      retries: 10
      delay: 3
      until: etcd_health.rc == 0
      changed_when: false


    - name: Show etcd health
      ansible.builtin.debug:
        var: etcd_health.stdout
```

- Add the remaining nodes to the cluster


```yaml
- name: Add remaining etcd members
  hosts: etcd[1:]
  gather_facts: true
  serial: 1

  tasks:

    - name: Add member to existing cluster
      ansible.builtin.command:
        cmd: >
          {{ etcdctl_bin }}
          --endpoints=https://{{ hostvars[groups['etcd'][0]].ansible_host }}:2379
          --cert={{ etcd_cert_path }}/{{ inventory_hostname }}.pem
          --key={{ etcd_cert_path }}/{{ inventory_hostname }}.key
          --cacert={{ etcd_cert_path }}/{{ inventory_hostname }}.crt
          member add {{ inventory_hostname }}
          --peer-urls=https://{{ ansible_host }}:2380
      register: member_add


    - name: Extract initial cluster
      ansible.builtin.set_fact:
        etcd_initial_cluster: >-
          {{
            member_add.stdout
            | regex_search('ETCD_INITIAL_CLUSTER="([^"]+)"', '\1')
            | first
          }}


    - name: Generate member config
      ansible.builtin.template:
        src: etcd.conf.j2
        dest: "{{ ansible_env.HOME }}/etcd/config/etcd.conf"


    - name: Start member
      ansible.builtin.systemd:
        name: etcd
        scope: user
        state: started
        enabled: true
        daemon_reload: true


    - name: Wait for member to become healthy
      ansible.builtin.command:
        cmd: >
          {{ etcdctl_bin }}
          --endpoints=https://{{ ansible_host }}:2379
          --cert={{ etcd_cert_path }}/{{ inventory_hostname }}.pem
          --key={{ etcd_cert_path }}/{{ inventory_hostname }}.key
          --cacert={{ etcd_cert_path }}/{{ inventory_hostname }}.crt
          endpoint health
      register: result
      retries: 30
      delay: 2
      until: result.rc == 0
      changed_when: false
```
