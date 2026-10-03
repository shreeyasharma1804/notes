### NFS

- NFS exports on the NFS server define the client IPs which are allowed to connect to the NFS server along with read write permissions
- The active site mounts the NFS with read write permission whereas the passive site mounts with read only permission
- On DR, remount the NFS mounts with appropriate permissions and update /etc/fstab so that the changes are persistent across restarts
- TYpically, LVM is used so that the NFS storage can be expanded later

### LVM

#### Create the physical volume

Maybe: Updates the metadata of this device to support volume groups later

```bash
sudo pvcreate /dev/sda1
sudo pvcreate /dev/sda2
```

#### Create the volume group

Maybe: Creates the logical addresses space

```bash
sudo vgcreate vg1 /dev/sda1
```

#### Create the logical volume

Maybe: Assign a logical address space from the VG to the LV

```bash
 sudo lvcreate -L 50M -n data1 vg1
```

#### Create the file system

- Both ext4 and XFS are supported, which technically use block addresses only.
- Maybe the block address is a logical address, which the LVM later converts to the actual device id + block number
- Unlike BTRFS, where the filesystem handles the logical address to device id + block number, maybe with LVM the kernel calls the lvm APIs for lvm partition type instead of calling the device drivers with the block address the file system wants to address (The file system may not be aware that the block number is actually a logical address). The LVM APIs then translates the address and call the actual device driver.

```bash
sudo mkfs.ext4 /dev/vg1/data1
```

#### Mount to a directory

```bash
 mount /dev/vg1/data1 .
```
#### Verify using `lsblk`

#### Extend

- If free space exists in the VG:

```bash
sudo lvextend -L +2M /dev/vg1/data1
```

- If not, add more devices to the VG

```bash
sudo vgextend vg1 /dev/sda2
```

#### Snapshots

- Similar to BTRFS, copy on writes are used to create a snapshot
- Instead of doing a CoW on every modification, LVM only does it when a snapshot exists and a block referenced by it is being modified
- Again, might cause some slowness in a DB server, thus prefer application level backups for DBs
- Can use used for an NFS volume backup though


#### Rsync vs LVMSnapshots for NFS Backups
