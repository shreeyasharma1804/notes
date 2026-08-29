## Internals

### Mount Namespace

- When a new process is started inside a mount namespace, all the mounting operations performed by it are isolated from the other mount namespace (including the host namespace)
- Start a process inside a new mount namespace:

```bash
sudo unshare --mount bash
```

- Mount one directory inside another:

```bash
sudo mount --bind /tmp /mnt

# Check the mounting table
findmnt

# Check the current mount namespace
readlink /proc/self/ns/mnt
```

- Mount propagation: Mounting events propagating between the caller and callee
- Types:
    - Private: No mount event propagation between namespaces
    - Shared: Mount events are propagated in both ways
    - Slave: Mount events are propagated from the caller's namespace to the new one (but not backward):

What setting is used in docker: Slave

### /dev

Good to have character devices:
- /dev/null
- /dev/zero
- /dev/random


Good to have subordinate filesystems
- /dev/shm: (Provide shared memory for multiple processes)
- /dev/pts: (Pseudo terminals)
- /dev/mqueue: (Provide shared queue for multiple processes)

Required links:
```bash
ln -sf /proc/self/fd   /dev/fd
ln -sf /proc/self/fd/0 /dev/stdin
ln -sf /proc/self/fd/1 /dev/stdout
ln -sf /proc/self/fd/2 /dev/stderr
ln -sf /proc/kcore     /dev/core
```

### /etc files
- /etc/hosts
- /etc/hostname
- /etc/resolv.conf
- 

### pivot_root

Change the root mount in the mount namespace of the calling process

### UTS and Network namespace

- For the container to have its own hostname, the container needs to use a new network and UTS namespaces
- If we forget to use a new UTS namespace, setting the hostname in the new container will overwrite the host's hostname, which is something we definitely don't want. And without a new network namespace, the container simply cannot have its own hostname, because then it technically has the same network stack as the host

#### Create a new network namespace:

```bash
ip netns add netns0
```

#### List the available network namespaces

```bash
# Similar to: docker list network
ip netns list
```

#### Enter a network namespace

```bash
nsenter --net=/run/netns/netns0 bash
```

#### What changes after I enter a new network namespace

```bash
ip link list (Only loopback interface initially)
ip route list (Empty)
iptables --list-rules (Empty)
```

#### veth

- veth devices are virtual Ethernet devices. They can act as tunnels between network namespaces to create a bridge to a physical network device in another namespace, but can also be used as standalone network devices

- Create a veth interface, both peers are initially created in the same namespace

```bash
ip link add veth0 type veth peer name ceth0

# Creates:
5: ceth0@veth0: <BROADCAST,MULTICAST,M-DOWN> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether 6a:a2:c8:cf:5e:14 brd ff:ff:ff:ff:ff:ff
6: veth0@ceth0: <BROADCAST,MULTICAST,M-DOWN> mtu 1500 qdisc noop state DOWN mode DEFAULT group default qlen 1000
    link/ether ca:68:0c:9d:6c:da brd ff:ff:ff:ff:ff:ff

# Turn on
ip link set veth0 up
```

- Move one of the peers to the other network namespace

```bash
ip link set ceth0 netns netns0

# Turn on
ip link set ceth0 up
```

- Assign a network address to the interfaces

```bash
# Linux allows multiple addresses for one interface
ip addr add 172.18.0.10/16 dev ceth0

# same for veth0
```

### PID

### IPC

#### System V IPC

- shmget() → shmat()
- Requires shared IPC namespace

```c
// Container A

int shmid = shmget(
    key,
    sizeof(struct shared_data),
    IPC_CREAT | 0666
);

struct shared_data *data =
    shmat(shmid, NULL, 0);

// Container B

int shmid = shmget(
    key,
    sizeof(struct shared_data),
    0666
);

struct shared_data *data =
    shmat(shmid, NULL, 0);
```

#### /dev/shm / tmpfs

- file → mmap()
- Requires both containers to access the same mounted filesystem

### Create docker image


## Image Management

### OCI Image Configuration

Defines the OS, architecture and uncompressed layer hash values

```json
{
    "architecture": "amd64",   // required field
    "os": "linux",             // required field

    "rootfs": {                // required field
      "type": "layers",        // required value
      "diff_ids": [
          "sha256:c6f988f4874bb0add23a778f753...b66bbd1",
          "sha256:5f70bf18a086007016e948b04ae...ce3c6ef",
          ...
      ]
    },

    "config": {                // optional but usually present
        "Cmd": ["/bin/my-app"],
        "Env": [
            "PATH=/usr/local/sbin:/usr/local/bin:...",
            "FOO=bar"
        ],
        "User": "alice"
    }
}
```

### Image ID

- The sha value of the OCI Image Configuration
- Uniquely identifies an image

### Image manifest

- The layer blobs are compressed and stored in the registry, thus the manifest and not the image configuration is not used to define the image in the registry
- The manifest contains the image configuration + the sha value of compressed layer blobs

```json
docker buildx imagetools inspect --raw registry.iximiuz.com/single:latest
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.oci.image.manifest.v1+json",
  "config": {
    "mediaType": "application/vnd.oci.image.config.v1+json",
    "digest": "sha256:68838b1e71a48b104cc2cd697c9928cf0620c0b170600263a76146c435a4c9af",
    "size": 5410
  },
  "layers": [
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest": "sha256:589002ba0eaed121a1dbf42f6648f29e5be55d5c8a6ee0f8eaa0285cc21ac153",
      "size": 3861821
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest": "sha256:0805a1082be0eb6421d4e4ea162883988394d156972333fe3818728bf2e0416f",
      "size": 460948
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest": "sha256:3566efde290bd04ef1658d390fe2c17f4a9fdf47499f81e1e52f4ecccec500e6",
      "size": 13370946
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest": "sha256:2800a7aef8b136106b41f5cd30530992ed6ad5f3b48b1ce9516084d69ba3cea3",
      "size": 248
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest": "sha256:6836738ade129bf2e9840be0fab56664da5c79f814f8d550df79cba4734e5f6e",
      "size": 93
    },
    {
      "mediaType": "application/vnd.oci.image.layer.v1.tar+gzip",
      "digest": "sha256:7a5fde85eaf677c156cec2a70642211fe5f981a483ed6c0a6482209a612f37b8",
      "size": 394
    }
  ]
```

### Image index

- Used for multi platform image management

```json
docker buildx imagetools inspect --raw registry.iximiuz.com/multi:latest
{
  "schemaVersion": 2,
  "mediaType": "application/vnd.oci.image.index.v1+json",
  "manifests": [
    {
      "mediaType": "application/vnd.oci.image.manifest.v1+json",
      "digest": "sha256:141e52ec9b7b941c48f98af1ce545897caab91d2fe74a247c3f344fc6a9c85ea",
      "size": 480,
      "platform": {
        "architecture": "amd64",
        "os": "linux"
      }
    },
    {
      "mediaType": "application/vnd.oci.image.manifest.v1+json",
      "digest": "sha256:65a8bbc6a0b500a9cb45af57d4bacff3ac7b4dbed8f7bad92f03a84f23a180d4",
      "size": 480,
      "platform": {
        "architecture": "arm64",
        "os": "linux"
      }
    }
  ]
```

### Image digest

- The SHA value of the topmost image identifier (manifest/index)
- 2 different image digests do not necessarily mean 2 different images. For example, different compression types could lead to 2 different image manifests which ultimately create the same image

### Registry

#### Login

```bash
docker login <registry> -u user
```

#### List all tags

```bash
curl -v registry.iximiuz.com/v2/<repo>/tags/list
```

#### Tag to manifest mapping

```
docker manifest inspect <registry>/<repository>:<tag>
```

#### Pull

- If I run:

```
registry.iximiuz.com: registry domain
acme: namespace
widget: repository
v1.2.0: tag

docker pull registry.iximiuz.com/acme/widget:v1.2.0
```

- docker runs a GET request to the endpoint

```
GET /v2/acme/widget/manifests/v1.2.0
Host: registry.iximiuz.com
```

- Docker pull automatically pulls the image of the correct architecture of the host machine based on the image index.
- docker tags are mutable pointer to the latest manifest pushed under that tag name
- docker images can be pulled both based on the tag and the digest of the index/manifest file

```
docker pull registry.iximiuz.com/acme/app@sha256:76d822da72eca8d151be12322d54f9ee5ffc330b74f0da29344f06d85761d114
```

#### OverlayFS

```bash
sudo mount -t overlay overlay -o lowerdir=/home/shreeya/Documents/overlayfs_test/lower/,upperdir=/home/shreeya/Documents/overlayfs_test/upper/,workdir=/home/shreeya/Documents/overlayfs_test/work/ /home/shreeya/Documents/overlayfs_test/merged/
```


#### What if I call fork inside a container ?

- Docker allows it
- Since the PIDs are isolated, the child process might have PID 2
- cgroups can enforce PID limits `docker run --pids-limit=100`
