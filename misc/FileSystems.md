### General

https://internals-for-interns.com/posts/filesystems-introduction/

- The smallest unit of storage in hardware(HDDs and SSDs) is a sector
- Typical size: 512 bytes or 4096 bytes
- The APIs for SDDs and HDDs are the same
- One partition is equivalent to one file system
- A disk can be divided into several partitions, the partitioning schemes available are MBR and GPT
- A file system converts a file name to the mapped disk sectors
- A file system reads and writes to the disk in terms of blocks. Block sizes are usually greater than the sector size. Disk space is assigned to files in terms of blocks.
- Tradeoff: Less book-keeping of sector numbers vs more space allotted to a file compared to the actual bytes written (`ls -lrth` vs `du -h`)
- Each partition contains a superblock defining the partition geometry like block size, total number of blocks, number of free blocks, the block address of the root directory, partition UUID etc
- File metadata such as owner, permissions, access times, data blocks etc is stored in inodes. The inode number can be check via `ls -i`
- A hard link uses the same inode as the original file. If the original file is deleted, the data can still be accessed because the inode reference count > 0
- A soft link uses a new inode which contains the filename of the original file, thus, if the original file is deleted, the soft link also becomes invalid
- A write to a soft link writes to the original file
- A directory is a file name to inode mapping. The mapping can be stored linearly or a btree indexed on the file name
- An extent is a contiguous array of blocks


### FAT32

- cluster ~= block

#### SuperBlock

- The superblock stores the cluster size, root directory cluster location

#### Reading a file

- The root directory cluster location is found from the superblock.
- The file system stores FAT Tables, which holds a mapping of a cluster value to the next cluster value. This forms a linked list like structure for traversing directory/file data spanning across multiple clusters.
- Each directory entry is 32 bytes in size which holds the file name (11 bytes), attributes, timestamps, cluster, file size(4 bytes) resulting in a maximum file size of 4GB
- The file system is traversed based on these cluster linked lists stores in the FAT tables and the file content is read

#### Writing to a file (New cluster allocation)

- The FAT table stores all the available cluster
- Clusters belonging to file form a linked list where the key value mapping contains the next cluster value
- EOF is represented by 0xFFFFFFFF
- Empty cluster is represented as 0x00000000
- The file system scans the FAT tables to find the required number of clusters (Slow!)
- The last found free cluster is cached by the FS so that spacial locality can be used to find the next free cluster faster

#### Crash recovery

- No crash recovery
