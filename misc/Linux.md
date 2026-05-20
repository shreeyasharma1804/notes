### Time Zones

- Unix Standard time: Time elapsed since 1st January, 1970. Use for removing time-zone overhead

### Memory

#### tmpfs

- This is a RAM backed file system

Create a tmpfs:

```bash
sudo mount -t tmpfs tmpfs /mnt/tmp

-t tmpfs: type of filesystem
tmpfs: Device name
mnt/tmp: Mount location of the tmpfs

Check:
df -h
```

For mounts to persist reboots:

```bash
cat /etc/fstab
```

#### LVM

```
Disk → Physical Volume → Volume Group → Logical Volumes → File systems
```

- Physical volume

A disk/ disk partition initialized by LVM

```bash
sudo pvcreate /dev/nvme1n1p1
```

- Volume group

Group multiple PV together

```bash
sudo vgcreate vg /dev/nvme1n1
```

- Logical volume

The smallest unit which is formatted to hold a file system

```bash
sudo lvcreate -L 50G -n lv1 vg
```

Check using:

```bash
sudo lvdisplay
sudo lsblk 
```

#### Disk usage

```bash
du -sh * | sort -rh | head -n 10
```

Check the usage of a partition

```bash
df -h .
```

#### Inode exhaustion

If disk space is available but the programs are still unable to create new files, the cause might be inode exhaustion

Check the usage of inodes:

```bash
df -i
```

Increase the maximum inodes:

```bash
umount <directory> # Unmoun the file system for the disk
mkfs.ext4 -i <number of inodes> /dev/sdX
mount /dev/sdX <directory>
```

#### Device data

- blkid

```bash
blkid
/dev/nvme0n1p3: UUID="a2ff4b86-0160-4eef-86f1-a1a674bd9670" BLOCK_SIZE="4096" TYPE="ext4" PARTUUID="9d190799-71f4-4c65-9db1-98d8cda6c649"
```

- Major and Minor device numbers

Major number: Used by the kernel to identify the driver for the device
Minor number: The number used by the driver to identify the device

### Files

`atime`: The last time a file was accessed

`mtime`: The last time a file content was modified

`ctime`: The last time a file meta data was modified (Example permissions, link count etc)

Check:

```bash
stat
```

Default time shown in `ls -la` is `mtime`.

For `atime`: `ls -lu`

For `ctime`: `ls -lc`

-t option sorts the file according to the mtime

Check all open files:

```bash
lsof
```

The ls -la and size field in stat command report the actual file size in bytes

To check the file disk usage:

```bash
du -h <filename>
```

### Systemctl

- List all services:

```bash
systemctl list-units --type=service
```

- List all timers:

```bash
sudo systemctl list-unit-files --type=timer
```

- Edit a service:

```bash
sudo systemctl cat <service>
sudo systemctl edit <service>
```

- Define the user of the process:

```
# /etc/systemd/system/<service>.service
[Service]
User=appuser
Group=appuser
```

- User systemd

Create a user specific systemd file:

```bash
~/.config/systemd/user/
```

Reload user systemd daemon

```bash
systemctl --user daemon-reload
```

Common operations

```bash
systemctl --user start myapp.service
systemctl --user enable myapp.service
```

User systemd stops after the user logs out. To keep the service alive:

```bash
sudo loginctl enable-linger <username>
```

- Service

```bash
# /etc/systemd/system/myapp.service

[Unit]

# Human-readable description of the service
Description=My Example Application

# Optional documentation/reference URL
Documentation=https://example.com/docs

# Start this service only after network.target is reached
# (ordering dependency)
After=network.target

# Soft dependency:
# systemd will also try to start network.target
Wants=network.target


[Service]

# Service startup type
#
# simple  -> process runs in foreground (most common)
# forking -> daemon forks itself
# oneshot -> short-lived command
# notify  -> service sends readiness notification
Type=simple

# Run service as this user/group instead of root
User=myuser
Group=myuser

# Working directory before starting process
WorkingDirectory=/opt/myapp

# Main command to start service
ExecStart=/usr/bin/python3 /opt/myapp/app.py

# Command executed on:
# systemctl reload myapp
ExecReload=/bin/kill -HUP $MAINPID

# Graceful stop command
ExecStop=/bin/kill -TERM $MAINPID

# Restart policy
#
# no          -> never restart
# always      -> always restart
# on-failure  -> restart only on nonzero exit
Restart=on-failure

# Wait 5 seconds before restarting
RestartSec=5

# Environment variables passed to process
Environment="PORT=8080"
Environment="ENV=production"

# Send stdout/stderr logs to journald
StandardOutput=journal
StandardError=journal

# Maximum startup/shutdown wait times
TimeoutStartSec=30
TimeoutStopSec=15


# ----------------------------
# Security Hardening Options
# ----------------------------

# Prevent privilege escalation
NoNewPrivileges=true

# Give service its own isolated /tmp
PrivateTmp=true

# Mount much of filesystem read-only
ProtectSystem=full


[Install]

# Start during normal multi-user boot
WantedBy=multi-user.target
```

- Timer

```bash
# /etc/systemd/system/health.timer

[Unit]

# Human-readable description of the timer
Description=Run health check every 10 seconds


[Timer]

# Run the timer 10 seconds after system boot
OnBootSec=10s

# Run again 10 seconds after the last successful activation
#
# This creates a recurring timer.
OnUnitActiveSec=10s

# Service unit triggered by this timer
#
# When the timer fires, systemd starts:
# health.service
Unit=health.service

# Optional:
# If the system was powered off during a scheduled run,
# execute missed runs immediately on next boot.
Persistent=true


[Install]

# Start this timer automatically during boot
WantedBy=timers.target
```

### Networking

- Hosts which are mapped in `/etc/hosts`can be resolved without dns.
- `/etc/resolv.conf`:

```bash
nameserver 127.0.0.53 # 127.0.0.53:53 is the local DNS server which returns cached responses
options edns0 trust-ad
search .
```

- To check the cache hits and misses

```bash
resolvectl statistics
```

- The lookup order /etc/hosts and then dns is defined in nsswicth.conf

```bash
cat /etc/nsswicth.conf

hosts:          files dns
```

### Sudo

- Sudo determines the user and group id of the iser running the comamand using `id`
- Parse the sudoers policy in `/etc/sudoers`

```bash
alice ALL=(ALL) ALL
user host = (runas) command
%sudo ALL=(ALL:ALL) ALL %sudo: any member of group sudo
```

- If the user can execute the command, execute it.
- Check if the user belongs to the sudo group.
- Use NOPASSWD to allow executing a command without sudo password

### umask

- The default permissions of a file are 666 for owner, group and other.
- Check the umask value: `umask`
- The umask value is deleted from 666 to get the file permissions of a new file

### Misc

- Crons are user specific and stored at `/var/spool/cron/crontabs/<username>`. System wide crons are defined at /etc/cron.d, /etc/cron/hourly etc
- `sort`: Sort in ascending order based on ascii
- `uniq -c`: Outputs the count of every adjacent occurrence, {count: value} map.
- Update the binary to be used when multiple versions exist: `sudo update-alternatives --config java`
- Check the OOM score of a process: `cat /proc/<pid>/oom_score`
- Apparmour: Define all files a process can access, overriding the linux permissions
- Nohup: When a shell is closed, the SIGHUP signal is sent to all the processes who started it, even in the backgroup. Due to this, any process started by ansible immediately exists. `nohup` handles the SIGHUP so that the process does not exit after the shell is closed
- `setsid`: Creates a new session, starts the process and detaches from the controlling terminal.
- `open`: Open a file and return its file descriptor
- `read`: Read a fd
- `futex`: Faster locking in user space
- `sendfile`: Send a file from file descriptor to socket directly from the kernel buffer instead of read + send. This reduces the overhead of copying data twice and 2 system call.

```bash
# Instead of Disk -> page cache -> User buffer(read) -> Kernel socket buffer(write) -> NIC

Disk -> kernel buffer -> socket buffer -> NIC
```
