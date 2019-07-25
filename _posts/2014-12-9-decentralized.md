---
layout: post
title: Decentralized command and control
comments: True
permalink: decentralized-command-and-control
---

**Worms using the blockchain for command and control**

Historical analysis of modern computer-worms is incredibly exciting. There are several reasons for this, a particular one for me is that the viruses that we create are taking on more and more qualities that would resemble bacterial-life. They have become incredibly sophisticated and instead of just having a central command and control (C&C) server, most worms use peer-to-peer approach. A lot of them have a reinfection capability so long as other hosts in the local network are infected. 

A recent paper by Roffel and Garret showed up on [pdfy](https://pdf.yt/d/E2ZwuLAVfC44kEQk) talked about various peer-to-peer attacks wich are much harder to control and shut down, worms like [Slapper](https://www.f-secure.com/v-descs/slapper.shtml) take advantage of those networks. One possible progression discussed by Roffel et al. is that of evolving beyond peer-to-peer to completely decentralized systems. This may not seem like a big logical jump however the big difference is that in peer-to-peer, there was still some need for human input but in decentralized systems, one can get away completely with the need for any trust. This can be illustrated by the use of smart-contracts which facilitate resource allocation. Here's how it can work: A virus is copied over to another system, this virus has a counter like metered-parking that only works once it has been given some money. A bitcoin transaction of a few Satoshis is carried out which allows the virus to run a module for certain amount of time (This can search for a particular vulnerability for instance) and then the virus self-destructs disappearing from the new system entirely. 

![](/static/stuxnet.png)

This is scary. Even though this sounds like something out of science-fiction but so did Stuxnet when the analysis behind it came out. The whole idea of smart contracts that auto-execute being used to allocate resources is completely automated and pretty darn scary. On the upside, this all can be used for some great things like vending machines can use a system of this sort to automatically pay rent and so on. The downside is that it can be all used for horrible things. The paper by Roffel et al. describes a very similar idea: A completely automated C&C system based on crypto-backends and the code with the paper can be found on their [GitHub](https://github.com/pzuraq/InChain).