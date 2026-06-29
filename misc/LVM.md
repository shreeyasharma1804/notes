- Create the physical volume

```bash
sudo pvcreate /dev/sda1
sudo pvcreate /dev/sda2
```

- Create the volume group

```bash
sudo vgcreate vg1 /dev/sda1
```

- Create the logical volume

```bash
 sudo lvcreate -L 50M -n data1 vg1
```

- Create the file system

```bash
sudo mkfs.ext4 /dev/vg1/data1
```

- Mount

```bash
 mount /dev/vg1/data1 .
```

- Verify using `lsblk`

- Extend

If free space exists in the VG:

```bash
sudo lvextend -L +2M /dev/vg1/data1
```

Extend the VG from a PV

```bash
sudo vgextend vg1 /dev/sda2
```
