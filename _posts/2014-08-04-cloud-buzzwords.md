---
layout: post
title: Cloud Buzzwords
comments: True
permalink: cloud-buzzwords
---

**Cloud computing as a Service. There are a lot of new acronyms becoming buzz-words, everyone is talking about a new SaaS service, or a newly deployed PaaS, but what do they mean? Beyond the hype, there's a lot of amazing technology at play here.**

So to start us off here, I thought about doing a post on some of the common buzzwords we hear when you start to talk about cloud technologies for building web or mobile apps. There are a few that have generated significant interest and market share and I primarily want to focus on SaaS, IaaS, PaaS and MaaS. Follow along to learn more:

**SaaS (Software as a Service)**:

This is a mouthful for a buzzword and somewhat intimidating but in reality this is something that most if not all of you already use. So what is SaaS that has generated so much interest and more importantly has the largest share of all could technologies? Back in the day software was sold on CDs, so if you wanted to install something, you would have to go to a vendor who was authorized to sell that product and then you would install that on your computer. This was then, but you hardly need to do that now. For most of our purposes we just follow the download and then install process and that's vastly due to how much internet has matured since then. Other software that we use is somewhat different, a prime example of this is Google Docs. It's among one of my favourites and I use it often, but here there is no downloading-install process or even a CD. You just sign in and voila it's available for you to use.

Let's take a step back and try to realize what paradigm shift happened here: When you use Google Docs, you're not actually installing anything, but what you are doing is accessing software installed on someone else's server (Google's servers in this case). This implies that for us, it's pretty much a seamless experience that avoids the hassle of having to do any of that download and install stuff, all we need to do is log in and we can go focus on using the product. Now no paradigms happen out of the blue, they all have an iterative and sequential background. As mentioned previously, software was sold on CDs and you had to go to your vendor to buy it. Your vendor provided you a *service* by selling you that software. But now the vendor is removed from this process, the server that someone else owns is providing that *service* to you. In essence, Google Docs is a SaaS wherein you as the user is using a service provided by Google, and that service happens to be a software. Now the cloud part of this comes in when you start to think about how many people use Google Docs, there isn't one server *serving* all of them but multiple servers, all of which constitute under one entity that we can call a cloud. Think about all the other SaaS that you use, they are practically everywhere!

![](/static/cloud.png)

<small>
[Photo credit: The IT DONUT](http://www.itdonut.co.uk/it/networking/essential-cloud-computing-services)
</small> 

**IaaS (Infrastructure as a Service)**:

Having understood SaaS, now let's start to add more layers of complexities or maybe generalizations to it. This first layer is actually a generalization, IaaS is not actually offering a software, but the production environment in which the software is installed as a service. More formally, IaaS abstracts hardware capabilities such as servers or storage into a pool that are delivered as services for a usage-based cost. So let me explain, very often development teams use specialized environments to code and deploy in, this includes what language/frameworks they use and their related dependencies. Generally this is all setup on a server, and if you have your own company you might want to setup your own servers and so on. But startups can't waste a lot of time on setting up and basic servers, so instead what they do is get a virtual servers that are *instantiated* and fine-tuned for them to use. The goal of IaaS is to provide a standard, virtualized operating environment that can become a foundation for all their prototypical tasks in a realistic production-like environment. The providers of infrastructure like that become IaaS, a good example of this is AWS (Amazon Web Services)

**PaaS (Platform as a Service)**:

PaaS is an interesting layer of complexity added on top of IaaS. The concept is actually fairly simple here: In IaaS, you offer the hardware resources as virtual services to the end-user but as stated previously, very often developers needed specialized environments to work in. So why not go a step further here and offer just the hardware capabilities, let's also add in all sorts of standard software that developers would want to use. That's what PaaS is all about: These are on-demand instances that are deployed to make the development environment standard for startups, if you don't want to invest in expensive tools or architecture (like servers).

**MaaS (Metal as a Service)**:

The latest and last of the bunch in the playground is MaaS, also with a fairly straight forward idea, but the market share for this is service is somewhat small. The reason lies in what MaaS is, so often when you need a dedicated server hosted by a company, they generally do all the configuration for you and start the instance. At this point when after the server has been provisioned and deployed, the user can go ahead and access it. But what if they don't want that, this could be for many reasons: Customization for speed, special installation requirements, compliance issues, or the need for custom environment that can't be provided by host. For parties/clients like that some hosts have started offering just the bare-metal, the hardware components of the server put together, without any sort of software on them . This is a little difficult to wrap your head around so let me elaborate: Generally a server rack has all the hardware components and the network cables wired up, but to physically access a particular server, as sometimes the need arises, there is a KVM which means a keyboard, video stream (a monitor) and a mouse to access the server. Now we have a new tech called IP-KVM, where you can access the KVM through an IP-connection or an internet connection. This allows you to access the server as if you were there in person, and gives you total control over everything about the server. This is probably the highest level of customization and control that you can be offered for a server that is hosted in someone's datacenter. Through the use of IP-KVM, the hosting companies offer *the bare-metal server (without anything installed on it) as a service* to the clients who want maximum control over their server.

So that's all for this time, tune in again for more cloud, tech and mobile stuff. Thanks for reading!