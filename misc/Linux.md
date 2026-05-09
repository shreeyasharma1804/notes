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
