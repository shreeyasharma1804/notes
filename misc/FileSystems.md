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

- Since the FS tree traversal always starts from /, the inode of the root directory is fixed to 2 in ext4. Check it: `ls -id /` 

#### Data blocks

- The data blocks store the actual file/directory content
- Data block usage is also tracked via bitmaps

#### Extents

- An extent is a continuous set of blocks
- An extent is identified by the starting block number + number of blocks
- The purpose is to optimize the spacial locality of file blocks
- Extents are used for huge files and may not be associated with how the blocks are referenced in the inode

#### Inode to data block mapping

- The file content can be referenced via direct pointers, 1st indirect pointer, 2nd indirect pointer, 3rd indirect pointer or btrees
- For btrees, the leftmost block number is the initial block number of the file

#### Preallocation and delayed allocation

- Preallocation: When you write to a file, ext4 quietly reserves more disk space than you actually asked for. That way, if you keep writing, the next chunk of data lands right next to the previous one instead of wherever happened to be free at that moment
- Delayed allocation: Rather than finding blocks every time you call write(), ext4 waits until the operating system is about to flush your data to disk. By then it knows how much you’ve written in total and can make one smart allocation for the whole batch.

#### Journaling

- WAL logs of metadata such as assigned inodes, updating bitmaps, assigned blocks etc are stored to ensure that the root data structures remain consistent

#### Inode exhaustion

- When a file system runs out of inodes for assigning to a new file

```bash
df -i
```

### XFS


#### Superblock

- No global superblock
- The file system is divided in allocation groups, which contains all the information similar to ext4 group descriptor
- Both allocation groups and group descriptors provide parallelism in file system operations such as assigning a new inode, block etc

#### Inodes

- EXT4 uses preallocated blocks for inodes. The retrieval of an inode is o(1), getting a new inode requires traversing the bitmap array which is o(n). But this system suffers from inode exhaution. XFS does not preallocate a set of block for inodes. Instead it allocates inodes in chunks (to avoid fragmentation) of 64 inodes and tracks them using a Btree.
- The index of the btree can be the block number + offset of the chunk
- If a node has atleast one free inode, it also tracked in the Free Inode Btree
- If a file is small, a map of all the blocks are tracked via the inode itself

#### Data Blocks

- Unlike EXT4, data blocks are only managed via extents. If the number of extents are small, they can be tracked inside the inode itself. FOr a large number of extents a Btree is used.
- Free data blocks(extents) are tracked via 2 BTrees, one indexed on the block number, and the 2nd indexed on the block size. This allows searching based on locality and size
- Preallocation and delayed allocation is also supported

Note: Extents can be variable sized and can be allocated based on the file size requirements. They are typically used for avoiding fragmentation

#### Journaling

- Similar to EXT4

#### xfs_repair

#### Why does XFS scale better than ext4:

- The system does not suffer from inode exhaustion
- Free inodes and data blocks are also tracked through Btrees instead of bitmaps
- All the files are tracked using extents

### BTRFS

- Runs on a pool of devices instead of just one device, thus eliminates the requirement of using opnelvm. To enable this, logical addresses are used which are translated to block numbers (Juts assume for now that block numbers are what's exposed by the device drivers)
- A chunk tree maps the logical address to the disk + block number
- Subvolume: An independent file system tree. A snapshot can be taken of a subvolume

#### SuperBlock

- Every device has its own superblock with backups
- It holds the metadata such as total file system UUID, device ID, pointers to the chunk_root tree, root tree and log_root tree

#### Chunk Tree

- Since the pointer to the chunk tree is also a logical address, a direct mapping for the chunk tree root to its block address is stored to load the chunk tree
- Its called a chunk tree because a BTRFS file system is divided into 3 chunks: DATA, METADATA and SYSTEM
- This tree is indexed on the logical address
- The payload in the leaf defines the device id and the block address

#### Root Tree

- This is a directory of the root pointers of all the essential trees of the file system
- It contains the root id and its logical address
- All subvolumes and their snapshots are also tracked here meaning that subvolumes and their snapshots are different FS trees altogether. A snapshot can be mounted on a direcotry using /etc/fstab

#### FS Trees

- Each subvolume has its own FS tree
- The inodes, directories, file data etc everything is stored in this tree
- This tree is indexed on the inode number + item type
- The leaf key associated with the inode has the key (inode_number, INODE_ITEM, 0) and the payload contains standard data held by an inode but not the data block locations
- Data leaf nodes have the key (inode_number, EXTENT_DATA, byte_offset_in_file) and the payload contains the logical address
- Available inodes and data extents are tracked seperately

#### Copy On Write

- Essential for snapshots
- Blocks are never modified in place, instead of copy of the block is created and that copy is edited
