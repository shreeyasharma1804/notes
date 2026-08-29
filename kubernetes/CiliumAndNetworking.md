### CNI

- A CNI plugin is normally just an executable. For example

```
/opt/cni/bin/mycni
```

- The container runtime (containerd) executes the CNI binary with container specific environment variables:

```
CNI_COMMAND=ADD 
CNI_CONTAINERID=abc123
CNI_NETNS=/proc/12345/ns/net
CNI_IFNAME=eth0
CNI_NETNS=/proc/12345/ns/net
```

- The CNi configuration, which is provided by the CNI itself is passed through stdin:

```
{
  "cniVersion": "1.0.0",
  "name": "mynet",
  "type": "mycni",
  "bridge": "br0",
  "subnet": "10.244.0.0/16"
}
```

#### Responsibilities of a CNI (When CNI_COMMAND is ADD and bridge networking is used):

Containerd creates the network namespace and sets the environment variables

```bash
# Initially it only contains the loopback interface
ip netns add netns0
```

Create a veth pair

```bash
ip link add veth0 type veth peer name ceth0
ip link set veth0 up
```

Move one peer to the container network namespace

```bash
ip link set ceth0 netns netns0
ip --net=/run/netns/netns0 link set lo up
ip --net=/run/netns/netns0 link set ceth0 up
```

Assign an IP address to the container interface from the subnet

```bash
ip addr add 10.244.0.10/16 dev ceth0
```

The below route is added automatically:

```bash
10.244.0.0/16 dev eth0 proto kernel scope link src 10.244.0.10
```

Create the bridge (If required)

```bash
ip link add br0 type bridge
ip link set br0 up
```

Attach the hosts end of veth to the bridge

```bash
ip link set veth0 master br0
```

Currently, since the only route is configured for networking inside the 10.244.0.0/16 subnet, only the connectivity between containers attached to the same bridge interface works

To establish the connectivity between the root and container namespaces, we need to assign the IP address to the bridge network interface and create the default routes

```bash
ip addr add 10.244.0.1/16  dev br0

nsenter --net=/run/netns/netns0 \
  ip route add default via 10.244.0.1 # i.e. via the bridge interface
```

Ping to an address outside of this subnet will still not work, if ip forwarding is disabled at the host. K8S requires this setting to be enabled

```bash
echo 1 > /proc/sys/net/ipv4/ip_forward
```

The CNI needs to add the SNAT rules as well

```bash
iptables -t nat -A POSTROUTING -s 10.244.0.1/16 ! -o br0 -j MASQUERADE
```

### VXLAN
