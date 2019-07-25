---
layout: post
title: Small changes
comments: True
permalink: small-changes
---

**Small ripples set the tide.** 

Hardly anyone starts with a bang, start small but start something. Then move on to do bigger and better things. We need those small changes, and the people who grew up on them too. Linus Torvalds replied to an [email](https://lkml.org/lkml/2004/12/20/255) of a contributor who wanted to know if he should still be working on things because his work was trivial. 

The email is a bit technical so I'll break it for the interested reader: 

> On Tue, 21 Dec 2004, Jesper Juhl wrote:
> 
> Should I just stop attemting to make these trivial cleanups/fixes/whatever patches? are they more noice than gain? am I being a pain to more skilled people on lkml or can you all live with my, sometimes quite ignorant, patches?
>
> I do try to learn from the feedback I get, and I like to think that my patches are gradually getting a bit better, but if I'm more of a bother than a help I might as well stop.

This developer submitted a patch, patches are generally small changes in code. Generally the email is sent out to the public list. When the dev. sent his patch, Linus pointed out that his patch had a mistake. So he replied to Linus in private asking for some guidance. Basically in this little segment, the developer is asking if he should continue doing what he is doing or stop because his patches might seem like a nuisance. 

![](/static/linux.jpg)

Linus's reply starts from here: 

> To me, the biggest thing with small patches is not necessarily the patch itself. I think that much more important than the patch is the fact that people get used to the notion that they can change the kernel - not just  on an intellectual level ("I understand that the GPL means that I have the right to change my kernel"), but on a more practical level ("Hey, I did that small change").

Linux kernel is the biggest open-source project. What does open-source mean? It means that anyone can edit and contribute to a project as vast and complicated as the kernel. Doesn't that sound crazy? The code that powers your computer, anyone can change it... 

Of course there are rules around who can do what: All changes are transparent and get reviewed by a LOT of eyes. That way, no crap changes make it past. Here Linus is saying that the small patches are like rite of passage: They help people get used to the processes that exist in the community. 

> And whether it ends up being the right thing or not, that's how everybody starts out. It's simply not possible to "get into" the kernel without starting out small, and making mistakes. So I very much encourage it, even if I often don't have the time to actually worry about small patches, and I try to get suckers err other developers like Rusty to try to acts as quality control and a "gathering place".

Linus emphasizes the importance of starting small but starting somewhere. You can't simply hope to read a few books and then jump into writing a whole device driver for the kernel. It doesn't work like that, you have to spend a lot of time understanding it and the best way to understand is to work on those small problems. 

> So at one level I absolutely *hate* trivial patches: they take time and effort to merge, and individually the patch itself is often not really obviously "worth it". But at the same time, I think the trivial patches are among the most important ones - exactly because they are the "entry" patches for every new developer. I just try really hard to find somebody else to worry about them ;) 

Linus points out what we feel as developers when we submit those small insignificant changes. To us, it's like wasting their precious time but there's no other way around it. This applies not just to code but any other area of life too. You'll be surprised how helpful people are when you ask them to walk you through some basics. For most open source projects, there are a lot of blogs around that can help you out. Greg-Kroah Hartman (@gregkh) has a lot of talks on youtube showing how to contribute and so on. 

> So please don't stop. Yes, those trivial patches *are* a bother. Damn, they are *horrible*. But at the same time, the devil is in the detail, and they are needed in the long run. Both the patches themselves, and the people that grew up on them.

This is the most important piece of the email: Try and keep trying. Never stop improving and especially if you're a developer, making mistakes and learn from them. Over the time, they will get better as long as you don't take any of that feedback personally and more importantly, if you use it to improve yourself. 

I thought the last sentence that Linus wrote was just so incredibly powerful: The small changes are like ripples that set the tide, in the long term, when the same new developers learn, they make up some of the best contributors. So we absolutely need them, and the small changes that helped them grow up!