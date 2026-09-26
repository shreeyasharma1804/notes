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

### EXT4

#### Superblock

- Defines block size, total number of blocks
- Replicated across interleaving block groups

#### Block Groups

- The blocks are divided into groups
- Each group is defined by a group descriptor containing

```
location_block_bitmap
location_inode_bitmap
location_inode_table
number_free_blocks
number_free_inodes
```

- Group descriptor table holds the group number: descriptor location mapping for all the groups
- A file can span across multiple block groups

#### Inode

- The inode is 256 byte entry and stores everything we need to know about a file/directory: the file type and permissions, the owner’s user ID and group ID, the file size in bytes, last access, last modification, last status change, creation time, the number of hard links pointing to this inode, and a compact structure that tells us where the file’s actual data blocks live on disk

- All the inodes are stored in a inode table which is fixed-size array of inode structures stored in contiguous filesystem blocks. The array is fixed size because one block can contain only x number of inodes.

- An inode is referenced via calculating the index position in the array

- Free inodes are tracked via a bitmap

#### Data blocks

- The data blocks store the actual file/directory content
- Data block usage is also tracked via bitmaps

#### Extents

- An extent is a continuous set of blocks
- An extent is identified by the starting block number + number of blocks
- The purpose is to optimize the spacial locality of file blocks

#### Inode to data block mapping

- The file content is stored in an extent btree
- The extent btree is indexed on the block numbers of the starting block of the extent, and the node also contains the number of blocks
- The leftmost block number is the initial block number of the file

#### Preallocation and delayed allocation

- Preallocation: When you write to a file, ext4 quietly reserves more disk space than you actually asked for. That way, if you keep writing, the next chunk of data lands right next to the previous one instead of wherever happened to be free at that moment
- Delayed allocation: Rather than finding blocks every time you call write(), ext4 waits until the operating system is about to flush your data to disk. By then it knows how much you’ve written in total and can make one smart allocation for the whole batch.

#### Journaling

- WAL logs of metadata such as assigned inodes, updating bitmaps, assigned blocks etc are stored to ensure that the root data structures remain consistent

### XFS


#### Superblock

- No global superblock
- The file system is divided in allocation groups, which contains all the information similar to ext4 group descriptor
- Both allocation groups and group descriptors provide parallelism in file system operations such as assigning a new inode, block etc

#### Inodes

- Managed via BTree rather than arrays for faster traversal
- Each Btree node contains 64 inodes
- If a node has atleast one free inode, it ilso tracked in the Free Inode Btree
- If a file is small, a map of all the blocks are tracked via the inode itself
- Similarly, if a directory is very small, all of its entries are stored in the inode itself

#### Data Blocks

- Similar to ext4, huge directories and files are stores in extents whose block numbers are discovered via BTrees
- Directory BTrees are indexed via filename hashes
- File BTrees are indexed via byte offset
- Preallocation and delayed allocation is also supported

#### Journaling

- Similar to EXT4
