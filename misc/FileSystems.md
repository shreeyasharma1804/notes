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
