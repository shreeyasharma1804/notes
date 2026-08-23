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

### Create docker image

```
# Extract required files

# Create a new mount namespace
sudo unshare --mount bash

# Change mount propagation type to private
mount --make-rprivate /

# Convert the directory containing the docker files to a mount point
mount --rbind /opt/container-1/rootfs /opt/container-1/rootfs

# Change mount propagation of new mount point to private
mount --make-rprivate /opt/container-1/rootfs

# After mounting proc, all the processes will be displayed if the new process does not use a new PID namespace
mount -t proc proc /proc
```
