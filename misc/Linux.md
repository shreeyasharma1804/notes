### Time Zones

- Unix Standard time: Time elapsed since 1st January, 1970. Use for removing time-zone overhead

### Physical Memory

#### tmpfs

Create a tmpfs:

```bash
sudo mount -t tmpfs tmpfs /mnt/tmp

-t tmpfs: type of filesystem
tmpfs: Device name
mnt/tmp: Mount location of the tmpfs
```
