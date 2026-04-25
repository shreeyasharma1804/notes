### Routing Table

- The dynamic entries of the routing table are populated by DHCP

- Check the interface where a packet will be forwarded for a destination IP address:

```
ip route get <ip-address>
```

### NAT

- Enable NAT:

```
sysctl net.ipv4.ip_forward
```

- NAT uses iptables to determine the source/destination IP

- DNAT or PREROUTING: The destination IP of the packet is changed.

- SNAT or POSTROUTING: The source IP of the packet is changed. Also called Masquerading. (The new IP is the IP of the interface the packet is leaving through).
 
- Example:

```
HostA → RouterA → RouterB → HostB

HostA: 192.168.1.10/24, GW = 192.168.1.1 (Router A)
Router A:
    -   eth0: 192.168.1.1/24 (toward HostA)
    -   eth1: 10.0.0.1/24 (toward Router B)
Router B:
    -   eth0: 10.0.0.2/24 (toward Router A)
    -   eth1: 172.16.0.1/24 (toward HostB)
HostB: 172.16.0.10/24, GW = 172.16.0.1

HostA sends the packet:
src=192.168.1.10:54321
dst=172.16.0.10:80

The packet reaches Router A on eth0.

The NAT chain is executed once, Prerouting is executed when the packet enters the router and Postrouting is executed when the packet leaves the router

NAT chain: 
     -  Prerouting
     -  Check the routing table: 172.16.0.10 → send via eth1
     -  Packet reached eth1
     -  Postrouting: SNAT is performed and conntrack table entry is created

The packet reaches eth0 on Router B

The same actions are performed by Router B for the packet to reach to HostB
```
- iptable

```
sudo iptables -t nat -L -n -v

Chain PREROUTING (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         
    1   153 DOCKER     all  --  *      *       0.0.0.0/0            0.0.0.0/0            ADDRTYPE match dst-type LOCAL

Chain INPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         

Chain OUTPUT (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 DOCKER     all  --  *      *       0.0.0.0/0           !127.0.0.0/8          ADDRTYPE match dst-type LOCAL

Chain POSTROUTING (policy ACCEPT 0 packets, 0 bytes)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 MASQUERADE  all  --  *      !docker0  172.17.0.0/16        0.0.0.0/0           
    0     0 MASQUERADE  all  --  *      !br-c2f3c54fc2c7  192.168.49.0/24      0.0.0.0/0           
    0     0 MASQUERADE  all  --  *      !br-37864d9fbcbf  172.18.0.0/16        0.0.0.0/0           
    0     0 MASQUERADE  all  --  *      !br-3244c2da4a2d  172.21.0.0/16        0.0.0.0/0           
    0     0 MASQUERADE  all  --  *      !br-27d87cf3147f  172.20.0.0/16        0.0.0.0/0           
    0     0 MASQUERADE  all  --  *      !br-15f4dac52349  172.19.0.0/16        0.0.0.0/0           
 5969  527K LIBVIRT_PRT  all  --  *      *       0.0.0.0/0            0.0.0.0/0           

Chain DOCKER (2 references)
 pkts bytes target     prot opt in     out     source               destination         
    0     0 DNAT       tcp  --  !br-37864d9fbcbf *       0.0.0.0/0            0.0.0.0/0            tcp dpt:9093 to:172.18.0.2:9093
    0     0 DNAT       tcp  --  !br-37864d9fbcbf *       0.0.0.0/0            0.0.0.0/0            tcp dpt:19093 to:172.18.0.2:19093
```

prot: Protocol
target: The next chain to jump to
in: Input interface
out: Output interface
source: Source IP
destination: Destination IP

Chain:
PREROUTING: Applied when a packet arrives at an interface. Packets which originate from the host do not go through the PREROUTING chain.
POSTROUTING: Applied when a packet is leaving an interface
DOCKER: Specific rules for published ports
INPUT: Destination IP ∈ host’s IP addresses
OUPUT:Source IP ∈ host’s IP addresses

#### Docker to Docker

Pure L2 forwarding using the bridge (virtual switch). Name resolution through /etc/hosts file which is populated when a new bridge network is created and containers are connected to it.

#### Docker to Internet NAT

- The packet is generated inside the container and routed to the gateway address.
- The packet reaches the host veth.
- PREROUTING rules are applied.
- The condition ADDRTYPE match dst-type LOCALis not met in the PREROUTING chain
- The packet is routed according to the kernel routing table and reaches the interface according to the routing table.
- Now the POSTROUTING rule is applied
- According to the table above, for any input interface and a non docker bridge output interface, the source IP belonging to the docker subnet and a foreign destination IP, the packet is MASQUERADED (SNAT to the host IP)

#### Internet to Docker NAT (Response)

- Consider a packet:

```
Client: 192.168.1.10
Router (NAT): 203.0.113.1
Internet Server: 8.8.8.8:80
```

- Original packet: 192.168.1.10:54321 → 8.8.8.8:80
- Router performs SNAT and changes the packet to: 203.0.113.1:40000 → 8.8.8.8:80
- Conntrack entry

```
<src>                  <dst>           <host>
192.168.1.10:54321  8.8.8.8:80   203.0.113.1:40000
```

- Server sends response to: 8.8.8.8:80 → 203.0.113.1:40000
- Router finds the conntrack entry for port 40000, performs DNAT and changes the packet to: 8.8.8.8:80 -> 192.168.1.10:54321

The kernel always check the conntrack table before the iptable

```
sudo conntrack -L
```

- Routed according to the mapping in the conntrack table


NAT table for port forwarding

- Redirecting traffic arriving on one IP/port to another IP/port.
- Requires IP forwarding to be enabled
- Uses NAT
- Enable port forwarding:

```
sudo iptables -t nat -A PREROUTING -p tcp --dport 8080 -j DNAT --to-destination 192.168.1.100:80
```
- Used in docker and kubectl port forwarding commands.
- When we port forward in docker, the following happens:

 ``` 
Connection via host_ip: port (ex. localhost:8080)
In the iptable, the PREROUTING chain meets the packet criteria
The DOCKER chain contains the port forwarding rules
DNAT is performed
The packet is routed to the docker_ip:port
```

### OSPF (Open shortest path first)

- Used for routers within an AS (Example, data center)

Algorithm:

- When a new router is added to the network, it advertises all the subnets it can connect to using Link State Advertisement (LSA)
- All the routers store this information and create a Link State Database (LSDB)
- The cost of connection between 2 routers is calculated based on the bandwidth of the connection between the 2 routers (Cost = Reference Bandwidth / Interface Bandwidth)
- Dijikstra is run over the network topology to construct the shortest distances to reach all the reachable subnets (with the least cost)

### BGP

- Used for routing between AS
- A router does not know the entire network topology, just the best way to reach an AS as advertised by the AS’s connected to it.
- All the paths are stored in the BGP DB
- Only the best path is stored in the routing table.

### Tunneling

Tunneling is the process of encapsulating one network protocol’s data inside another protocol to securely or logically transmit it across a network.

- SSH Tunneling: Application-layer data (e.g., HTTP, DB traffic, shell input/output) is encapsulated inside the Layer 4 SSH protocol, which is then carried over a single TCP connection.

- VXLAN: Layer 3 data is encapsulated and sent over layer 2 to achieve the k8s principle that all pods belong to the same cidr.

### IP forwarding

When IP Forwarding is DISABLED (default on most systems), The kernel acts as a normal end-host. When it receives a packet on one interface whose destination IP is not its own, it simply drops the packet.

```
[Host A] --> [Linux Machine] --> ❌ packet dropped (not for me)
```

When IP Forwarding is ENABLED, The kernel acts as a router. When it receives a packet on one interface, it looks up the destination IP in its routing table and, if a route exists, forwards the packet out through the appropriate interface — even if that interface is different from the one it arrived on.

```
[Host A: 192.168.1.10]                    [Host B: 10.0.0.20]
        |                                          |
   [eth0: 192.168.1.1]---[Linux Router]---[eth1: 10.0.0.1]
                           ✅ forwards packet
```

Docker automatically enables IP forwarding on the host to allow Internet -> Docker interface access

```
Internet
   |
[eth0: 203.0.113.5]        ← public-facing interface (packet arrives here)
   |
[Linux Host Kernel]
   |
[docker0: 172.17.0.1]      ← docker bridge interface (different interface)
   |
[Container: 172.17.0.2]

systl -a | grep ip_forward
net.ipv4.ip_forward =  1
```

Troubleshooting

- IP addressing & subnets: is the host reachable at all?
- Routing tables: is the kernel sending packets to the right next hop?
- ICMP — diagnostic protocol (ping, traceroute, MTU discovery)
- MTU / fragmentation: packet size mismatches that silently kill throughput
- Kernel IP forwarding & sysctl params: tuning how the kernel handles IP traffic
- Packet loss & reachability: distinguishing L3 loss from L4 (TCP) loss

### Connectivity & reachability

- MTU: Maximum transaction unit. The highest size of a TCP packet allowed in a network.
- If a packet size > MTU, layer 3 fragmentation occurs. This is highly discouraged. Use the don’t fragment flag. This way, the packet is dropped and ICMP error is returned stating fragmantation needed

#### Basic reachability — ICMP echo

```
ping -c 10 <target>

# With specific packet size (useful for MTU debugging)
ping -c 5 -s 1472 <target>        # 1472 + 28 (IP+ICMP header) = 1500 MTU. If the MTU is huge, the packet is either fragmented or dropped (if fragmentation is not supported by any device in the hops). This results is a 100% packet loss
ping -c 5 -s 1400 -M do <target>  # don't-fragment bit set — forces PMTUD path
# If the packet reaches, all the interfaces involved in this path support that MTU value. If not, the MTU value needs to be decreased.
```

#### Trace the routing path

traceroute: Shows all the packet hops and the maximum hops allowed before TTl
The 3 values in the output are 3 RTTs

```
traceroute <target>                # UDP by default (often blocked)
---------------------------
traceroute example.com                                                              ↵ 1
traceroute: Warning: example.com has multiple addresses; using 172.66.147.243
traceroute to example.com (172.66.147.243), 64 hops max, 40 byte packets
 1  192.168.1.1 (192.168.1.1)  3.977 ms  4.174 ms  3.649 ms
 2  223.178.8.1 (223.178.8.1)  5.212 ms  6.873 ms  6.913 ms
 3  nsg-corporate-61.95.187.122.airtel.in (122.187.95.61)  7.813 ms  6.186 ms
    nsg-corporate-57.95.187.122.airtel.in (122.187.95.57)  7.194 ms
 4  116.119.33.230 (116.119.33.230)  37.676 ms  20.743 ms  24.678 ms
 5  * * *
 6  162.158.226.81 (162.158.226.81)  26.494 ms
    162.158.226.77 (162.158.226.77)  21.478 ms
    162.158.226.21 (162.158.226.21)  32.458 ms
 7  172.66.147.243 (172.66.147.243)  29.632 ms  23.086 ms  25.599 ms
---------------------------


traceroute -I <target>             # ICMP mode
traceroute -T -p 443 <target>      # TCP mode with target port 443 — bypasses ICMP blocks
```

#### MTR

Combines ping + traceroute, runs continuously

```
mtr --report --report-cycles 4 <target>        # ICMP mode by default
mtr --tcp --port 443 --report --report-cycles 60 <target>      # TCP mode

Reading mtr output:

Host                     Loss%  Snt  Last  Avg  Best  Wrst StDev
1. gateway (10.0.0.1)     0.0%   60   0.4  0.5   0.3   1.1   0.1
2. 172.16.0.1             0.0%   60   1.2  1.3   1.0   2.1   0.2
3. target (10.10.0.5)    20.0%   60   5.4  8.2   4.1  42.1   7.3

Loss only at the final hop = real packet loss. Loss at an intermediate hop but not later hops = that router rate-limits ICMP (ignore it).
```

#### Check MTU of an interface

```
ip link show wlo1 | grep mtu
3: wlo1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc noqueue state UP mode DORMANT group default qlen 1000

# Lower MTU on the interface
ip link set eth0 mtu 1400
```

#### Show the kernel routing table

```
ip route show
ip route show table all          

# Which route would the kernel use for a given destination?
ip route get 8.8.8.8
```

#### Show ARP cache (useful when packets aren't leaving the host interface)

```
ip neigh show
ip neigh show dev eth0

# Flush ARP cache for a specific IP (force re-ARP)
ip neigh flush dev eth0 to 10.0.0.1
```

#### Asymmetric routing

- Asymmetric routing — packets leave via eth0, replies come back via eth1.
- Asymmetric routing and stateful firewalls do not work together.
- Stateful firewalls: Placed at the network edge of, for example, a DMZ

```
Internet -> firewall -> Internal network

The fireall maintains a table everytime a request is sent, containing:
(src IP, src port, dst IP, dst port, protocol)

If a response is coming from the internet, the firewall checks if the entry exists in the table, if not, the packet is dropped

But in asymmetric routing (common in BGP), the response packet might follow a different path and land on a different firewall which does not contain the request entry.
```

- To check if the network is asymmetric:

``` 
ip route get <src-ip>
ip route get <dst-ip>
```

### Interface & IP inspection

#### Show all interfaces with IPs

```
ip addr show
```

#### Check interface stats — errors, drops etc

```
ip -s link show eth0
```

#### Packet capture

```
# Captures and displays all packets on interface wlo0 to or from 10.10.0.5, without resolving names.
tcpdump -i wlo1 -nn host 10.10.0.5

# Capture all ICMP traffic
tcpdump -i wlo1 -nn icmp

# Capture and check for IP fragmentation
tcpdump -i wlo1 -nn 'ip[6:2] & 0x1fff != 0'   # Capture all packets where the fragment offset in IP headers is not 0
```

### sysctl properties

#### Enable IP forwarding (required on routers, LB nodes, hosts with multiple interfaces and port forwarding)
```
net.ipv4.ip_forward = 1
```

#### Reverse path filtering

- Packet arrives on interface ethX with source IP S.
- Kernel looks up the route to S (a normal routing-table lookup).
- Compare the egress interface from that lookup with the ingress interface:
- Match → accept
- Mismatch → drop (depending on mode)

- 0 = off, 1 = strict, 2 = loose
- Set to 2 (loose) if you have asymmetric routing

```bash
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1
```

#### Accept source routing 

- Almost always leave off
- System will not honor the path specified by sender

```bash  
net.ipv4.conf.all.accept_source_route = 0
```

Example of source routing:

```python
from scapy.all import *

pkt = IP(dst="8.8.8.8", options=[IPOption_LSRR(["1.1.1.1","2.2.2.2"])])/ICMP()
send(pkt)
```

ICMP behaviour

# Respond to broadcast pings (disable — Smurf attack vector)
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Ignore bogus ICMP error responses
net.ipv4.icmp_ignore_bogus_error_responses = 1

# Rate limit ICMP replies (prevents ICMP flood amplification)
net.ipv4.icmp_ratelimit = 1000
net.ipv4.icmp_ratemask = 6168

ARP tuning (important on hosts with many peers)

# How long to cache ARP entries (seconds)
net.ipv4.neigh.default.gc_stale_time = 60

# ARP cache size — increase on busy hosts with many connections
net.ipv4.neigh.default.gc_thresh1 = 1024   # below this, no GC
net.ipv4.neigh.default.gc_thresh2 = 2048   # soft limit, GC kicks in
net.ipv4.neigh.default.gc_thresh3 = 4096   # hard limit, entries dropped

# Check current ARP table size
ip neigh show | wc -l

Error: “Service is unreachable from some hosts but not others”

# 1. Check if you can reach the host at all
ping -c 5 <target>

# 2. Traceroute to find where it stops
mtr --report -c 20 <target>

# 3. Check routing table on the source host
ip route get <target-ip>

# 4. Check if the target host has a route back
# (ssh to target)
ip route get <source-ip>

# 5. Check for rp_filter drops (asymmetric routing dropping packets)
# On the target:
cat /proc/net/netstat | grep -i rpf
# or check:
sysctl net.ipv4.conf.all.rp_filter

# 6. Check iptables isn't dropping at L3
iptables -L -n -v | grep DROP
iptables -t raw -L -n -v          # pre-routing drops

Error: “Connection works for small transfers, fails or stalls for large ones”

This is almost always MTU.

# 1. Confirm with sized pings
ping -c 3 -s 1472 -M do <target>  # fails = MTU problem
ping -c 3 -s 1200 -M do <target>  # works = confirms MTU is the issue

# 2. Find the path MTU
tracepath <target>                 # reports path MTU at each hop

Error: “Intermittent packet loss — hard to reproduce”

# 1. Run mtr for several minutes — get statistically meaningful loss %
mtr --report --report-cycles 120 <target>

# 2. Check interface error counters — driver-level drops
ip -s link show eth0

# 4. Check NIC ring buffer — small ring = drops under burst
ethtool -g eth0
# Increase RX ring:
ethtool -G eth0 rx 4096

# 5. Check for ARP table exhaustion (drops silent at L3)
ip neigh show | wc -l

# 6. If loss is between specific hosts only, check for duplex mismatch
ethtool eth0 | grep -i duplex

Error: “High latency — not a loss issue”

# 1. Baseline — measure RTT at different times
ping -c 100 -i 0.2 <target> | tail -1   # min/avg/max/mdev

# 2. mtr to isolate which hop adds latency
mtr --report -c 30 <target>

# 4. Check for interrupt coalescing — NIC batching ACKs adds latency
ethtool -c eth0
# For latency-sensitive workloads, lower coalescing:
ethtool -C eth0 rx-usecs 50   # default is often 100-200µs

# 5. Check IRQ affinity — all NIC interrupts on CPU 0 = bottleneck
cat /proc/interrupts | grep eth0
# Spread IRQs across CPUs:
# /etc/irqbalance — let irqbalance handle it
# or set manually via /proc/irq/<N>/smp_affinity

ethtool -S eth0

Performance Tuning
Interface level

# Check MTU
ip link show | grep mtu

# Check NIC ring buffers — increase if you see drops under load
ethtool -g eth0
ethtool -G eth0 rx 4096 tx 4096

# Check offload features — most should be on
ethtool -k eth0 | grep -E 'tcp|gso|gro|tso'
# Enable GRO (reduces CPU for bulk recv)
ethtool -K eth0 gro on

Kernel parameters

# /etc/sysctl.d/99-network-tuning.conf

# Increase netdev backlog (packet queue before kernel processing)
# NIC → (interrupt/NAPI) → netdev backlog queue → kernel network stack (This queue stores raw L2/L3 packets)
net.core.netdev_max_backlog = 5000

# Increase processing budget per NAPI poll
net.core.netdev_budget = 600

# ARP cache (increase for hosts with many peers)
net.ipv4.neigh.default.gc_thresh3 = 8192

# Ephemeral ports (increase for outbound-heavy services)
net.ipv4.ip_local_port_range = 1024 65535

# Disable slow path for local sockets
net.ipv4.conf.all.accept_redirects = 0
net.ipv4.conf.all.send_redirects = 0

Validation after tuning:

# Baseline throughput test between two hosts
# On receiver:
iperf3 -s
# On sender:
iperf3 -c <receiver-ip> -t 30 -P 4    # 4 parallel streams, 30 seconds

# Watch for drops during the test
watch -n1 'ethtool -S eth0 | grep -i drop'
watch -n1 'cat /proc/net/softnet_stat'

HTML 12997 characters 2555 words 330 paragraphs
