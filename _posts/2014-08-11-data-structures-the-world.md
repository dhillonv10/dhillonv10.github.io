---
layout: post
title: Data structures the world
comments: True
permalink: data-structures-the-world
---

**Software is eating the world and producing a lot of that. In turn, that data is re-structuring it. An interesting feedback loop for the age of technology.**

Marc Andreesen(@pmarca) coined the phrase software is eating the world to signify how software is seeping into our connected world and our lives. Technology has been playing a critical role in just about every industry and we will only see more of it as software is eating up the new industries. Often, new paradigms occur when someone bringing software to an industry that was not using it and almost instantly they see growth because prices drop and they can increase their market share. 

The Internet is a vast place right now. We have almost too many websites, blogs, and social media sites. The rate at which information is flowing out of these sources is absolutely unprecedented. Companies concerned with capturing as much data as they can to make better decisions are now becoming interested in creating Big Data infrastructures that can make it possible. So what is Big Data? It's a commonly used buzz-word signifying data that is characterized by the following four attributes (Also called the 4 V's): 

1. **Volume**: This represents the scale of data or just how much of it is under consideration. Big Data is at the scale of 100 Terabytes or more and this data is coming from every imaginable source, from traffic lights and music downloads to medical records. 

2. **Velocity**: This represents the speed at which the data is coming through to your organization. The speed matters here because the collected data has value during a *critical-window* of time. The amount of time it would take to capture incoming data, convert it into something more meaningful and store it in your warehouse is far longer than the critical window. By the time the data is in the warehouse, it has lost the incredible value it has during the critical window and that's why now we have tools like Storm that can do real-time analysis as the data is coming in. 

3. **Variety**: This represents the different forms of data that are collected. Some data is nice and gets collected in a form that meaningful operations can be done on it right away. Other data from a different source is all over the place and we need to pre-process it. This should seem completely natural simply because how many sources we have for all the data that we are collecting. 

4. **Veracity**: This represents the accuracy of the collected data. This is a more abstract concern where the organization collecting the data is not sure how accurately they have collected the data that they will be using to make informed decisions

![](/static/structure.jpg)

In cases of blogs, new and interesting content coming out on the Internet is like a shower that shoots jets of water from the ground. We only ever come across a small portion of all the jets of water that come up and our search queries only reveal so much that is in our attention span. But there is a lot of interesting data out there, and now we are seeing a hierarchy emerge out of this. The first level is the content itself spread everywhere on the internet. The level above this is the emergence of *organic* repositories which favor *good content* places like HN, Reddit, Quora and so on. These services gather some of the most interesting content submitted by the users and with the voting systems, we see a portion of submissions reaches the top. 

The user-base for these services keeps increasing and more and more content is being submitted every day that reaches the top. The amount of content that reaches top is so much that we are now seeing a third-level of services that pull data from central content-repositories like Twitter and make a small tailored subset of it available to the user in some form. A perfect example of this is TagAndSee which takes tweets from a specific user and converts them into a slideshow playlist so that a user can see any content from just one user. These third-level repositories can be thought of as extensions to SEO, often search is only limited to what we look for and hardly anyone goes to the second or third page on google to look for related content. To create a network-effect where we not only find what we want, but also related good content, these third-level can be incredibly useful. As the size of any of these levels increases, we see a higher level emerge tailored to just a specific subset of content from the level underneath. 

Currently there is a push for building APIs, services or infrastructure to make more and more data searchable or actionable. The idea here is that we will soon have even more data than we do now, and the more we can act on it, the better we can predict the future. This push on making the data more searchable and available creates these hierarchies whereby good content is created, then submitted to a central repository which filters a portion of it to present to users. As their size grows, other services are being built on top to filter even more content and present even smaller subset to users. 

In this sense, data is structuring the world. We are building services around data and data in-turn is presenting opportunities to structure our society around it and create those services. Data is parallel to software, as software eats the world, it craps out more and more data that we can act on. In a sense, we are trying to overcome the limitation of our own mind in terms of finding content that is helpful to us but don't necessarily occur to our brain and become searchable. The future of Big Data is very likely to be different from how we manage it today, but without a doubt:

> "It is an exciting time to be alive" - Norman MacAfee