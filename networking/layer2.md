### Layer 2

- Switch is a Layer 2 Ethernet device with no console and no operating system.

- Layer 2 networks can be categorized by assigning VLAN IDs to each interface.

- 2 switches with different VLAN IDs cannot connect with each other.

- VLAN ID maximum value is 4096 bits.

### GNS3 Layer2 Network

![alt text](image.png)

On PC1:

```bash
ip 192.168.1.1/24
show ip
```

On PC2:

```bash
ip 192.168.1.2/24
show ip
```

Add both the PCs to the same subnet and run the ping command.

### Switch Loops

Since switches use unicast flooding with no maximum hop number, it's possible for a packet to be lost due to a loop in the graph. This is a layer 2 limitation.

![alt text](image-1.png)

In this setup, with an aditional router, most of the ping packets timeout

```bash
PC1> ping 192.168.1.3 -c 50

192.168.1.3 icmp_seq=1 timeout
192.168.1.3 icmp_seq=2 timeout
192.168.1.3 icmp_seq=3 timeout
192.168.1.3 icmp_seq=4 timeout
192.168.1.3 icmp_seq=5 timeout
192.168.1.3 icmp_seq=6 timeout
```

### ARP

- Layer 2 networks work using MAC address and not IP-addres
- ARP is a broadcasting protocol which uses `Unicast Flooding` i.e; the packet is sent to all the devices connected to the switch for finding the MAC address of a machine with a  given IP address.
- The switch caches these port -> mac address mapping for further usage.

- To find the MAC address of a given IP address
```bash
arping -I <interface> <IP-address>
```

- To check the local ARP cache table
```bash
ip neigh
```

### VRRP (Virtual Router Redundancy Protocol)

Implement using `keepalived`

https://keepalived.readthedocs.io/en/latest/case_study_mixing.html

The VRRP instance associated with the virtual IP and marked as MASTER responds to the ARP request in the local network.

In the below config all requests for the virtual IP are to MAC(wlo1).

```nginx
vrrp_instance VI_1 {
    state MASTER
    interface wlo1
    virtual_router_id 51                 # Cluster ID
    priority 150                         # Determines MASTER election
    advert_int 1                         # Multicast Broadcast interval (heartbeat)

    nopreempt                            # If the MASTER is alive again, the current MASTER is not changed

    authentication {                     # Authenticate the server
        auth_type PASS
        auth_pass k@l!ve1
    }

    virtual_ipaddress {
        192.168.31.160/32
    }

    garp_master_delay 1                  # Wait 1 second after sending the GARP to become MASTER
    garp_master_repeat 5                 # Send 5 GARP after becoming MASTER
    garp_master_refresh 60               # Resend GARP every **60 seconds** while MASTER.
    garp_master_refresh_repeat 2         # Number of GARPs per refresh event.
}
``` ### VRRP



Sending GARP request:

```
 sudo arping -U -I enp2s0 192.168.1.181
```
