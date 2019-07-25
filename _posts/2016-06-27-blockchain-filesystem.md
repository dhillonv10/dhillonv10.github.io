---
layout: post
title: Blockchain as a filesystem
comments: True
permalink: blockchain-as-a-filesystem
---

**The blockchain can be understood as a filesystem for a new kind of web**

I've always been interested in [filesystem](http://www.tldp.org/LDP/sag/html/filesystems.html) development, particularly in the context of what was happening in Linux kernel community around 2009 during the transition from ext3 to ext4. I was following some of the discussions from people like Theodore Ts'o (the developer of ext3 and ext4) about design principles and performance differences between filesystems. In this post, I want to make the case that many concepts used to describe filesystems are also describe the operations of the blockchain in a very appropriate and sophisticated manner. 

This is especially true for applications of the blockchain in domains outside of financial services, where this terminology captures not just the blockchain but also illustrates the services that can be built around it. Both technologies share a lot of the similar features, so let's go through some of them: 

* **Journaling**: A feature in most modern file systems that keeps track of changes not yet committed to the file system in a data structure known as a journal, which is usually a [ring buffer](http://c.learncodethehardway.org/book/ex44.html). In some cases, the journaling is limited only to tracking the metadata on changes in files. The blockchain does the same with the blocks that have not been yet committed to the blockchain, these blocks are kept in a pool and integrated only after verification. Also the blockchain is a decentralized data-structure so there isn't a single point of failure.

* **Snapshots**: Another feature present in most filesystems, a snapshot is the state of a system at a given point in time. Essentially, a snapshot in a filesystem is pointers to a set of files at one given time. A snapshot utility creates a snapshot of changes to stored data every time new data is entered or existing data is updated. Whenever a block of data is changed, the changed data is written to a location on disk different from the original copy. This new copy is linked to in the new snapshot. This allows rapid recovery of data in case of a disk errors or corrupted files. The blockchain allows for similar type of redundancy by making all the users download the entire blockchain locally. Any changes or inconsistencies can be immediately identified and restored from a valid chain of blocks.

* **Checksums**: A checksum is a string of data introduced in a file while it is being transmitted. This string is known ahead of time and can be used to check the integrity of the file being transferred. This can be used to detect if the file was damaged because of packets not being sent and other streaming errors. The blockchain uses a very similar system of hashes and system-wide verification of the blocks and transactions being included in the blockchain.

* **Inodes**: An inode is a data structure that represents filesystem objects which can be either a file or a directory. The inode stores data and attributes on filesystem objects. Often times, the attributes are metadata on how or when a file was edited such as the access or edit times, the ownership and permissions on that particular object. An inode is the closest data structure to a block on the blockchain, analogously, a block also contains metadata and a header. 

So why are we interested in filesystems? The features I listed out above all have analogues to blockchain constructs. Feature rich filesystem like [ZFS](https://wiki.archlinux.org/index.php/ZFS) could become the foundation for blockchain-based health infrastructure. Filesystems should be revisited by blockchain developers. They have all the necessary features that one might expect in a mature blockchain being used for healthcare applications or storing and dealing with genomic data. The current filesystems have all the necessary features of dealing with high I/O load which is analogous to a high-volume of transactions. In addition, filesystems are modeled as operational constructs that have redundance and resilience for load and network perturbations. 

New ideas and maturity in the blockchain ecosystem will come as we begin borrowing ideas from already established principles and domains. Blockchain-based data transactions transform the underlying infrastructure into a filesystem for a new type of web where data exchange will be completely trustless and decentralized. I want to point out that there is much to be learned, I have only scratched the surface. Imagine incorporating the services and design principles of ZFS into constructing a digital health exchange. We can rely on innovation in digital health driven by known models of development in existing filesystems.

---

Following this post, I had a very interesting conversation that I am adding below.

**Micah Winkelspecht (@winkelspecht):**

> Vikram: nice post, blockchains as file systems have some limitations though. as blockchains are (almost by definition) replicated across all nodes in the network, which makes them a terribly inefficient store of large quantities of data. You were correct, however, that the features of good filesystems (journaling, snapshots, checksums, etc.) are similar to features in a blockchain, but the blockchain goes a step further and provides two things that filesystems don’t: 1) no central administration required, and 2) byzantine fault tolerance (nodes are compromised by an attacker). Most file systems only support benign fault tolerance (nodes go down by accident) at best.
>
> At Gem we’ve actually modeled a file system ​*on top*​ of blockchains
> 
> But we don’t use the blockchain itself to store the contents of the files, only metadata, which includes ACLs/permissions, checksums (SHA3), versioning, and pointers to external data stores.
>
> Yet, the interface looks and feels like a file system from the user’s perspective, complete with directories, files and permissions.

**My reply:**

Thank you Micah, for reading over it. You're absolutely right about the blockchain itself not working as a filesystem. It would get bloated very fast and be incredibly inefficient. My observation was more along the lines of blockchain feeling like a filesystem for a new kind of web, maybe some of the features for health services could take inspiration from filesystems. More importantly, from a regulatory standpoint, this becomes important: We can explain filesystems easier to regulators for HIPPA compliance and so on.
