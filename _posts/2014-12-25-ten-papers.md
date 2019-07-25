---
layout: post
title: 10 papers for programmers
comments: True
permalink: ten-papers-for-programmers
---

**10 papers every developer should read, twice.**

Over the past 20 years or so, software engineering has had some incredible changes and people are joining the field from all sorts of different directions. Academically, a few papers are classics that everyone should give a read. Not only will they give the reader a concrete theoritical background, but also fill any gaps in knowledge about the theory behind a certain concept. I took these from a [blog](http://web.archive.org/web/20121024173845/http://blog.objectmentor.com/articles/2009/02/26/10-papers-every-programmer-should-read-at-least-twice) that isn't there anymore, so I provided the ten papers and the non-paywalled sources with them here.


* **On the criteria to be used in decomposing systems into modules – David Parnas**

This is a very old paper, but it is more than a classic. In in it, Parnas introduces a forerunner to the Single Responsibility Principle. He introduces the idea that we should use modularity to hide design decisions – things which could change. People still don’t consider this as often as they should.

[PDF](/static/pdf/Parnas.pdf)  
PDF [source](http://repository.cmu.edu/cgi/viewcontent.cgi?article=2979&context=compsci)

* **A Note On Distributed Computing – Jim Waldo, Geoff Wyant, Ann Wollrath, Sam Kendall**

Abstraction is great but it can only go so far. In this paper, the authors lay to rest what was once a pervasive myth – that we could design a distributed system and make distribution transparent. Ever wonder why you had to implement specific interfaces to do remoting in Java? This is why.

In the aftermath it might seem hard to believe that people thought this was possible. I think we can we partially thank this paper for that.

[PDF](/static/pdf/Waldo.pdf)  
PDF [source](http://web.archive.org/web/20121126000533/http://labs.oracle.com/techrep/1994/smli_tr-94-29.pdf)

* **The Next 700 Programming Languages – P. J. Landin**

Most of us have spent a lot of time working in traditional programming languages, but functional programming languages are slowly seeing an uptick and many OO languages are gaining functional features. This paper (which reads like a tutorial) makes an argument for an expression-oriented style of programming. It also lays the foundation for lazy evaluation.

One of the other neat things about this paper, from a historical point of view, is that there is a discussion section at the end in which there a number of questions and comments about whether making indentation significant in a language is a good idea. I was thrown to see people asking whether or not this would be a problem for functions which span over several pages(!).

[PDF](/static/pdf/Landin.pdf)  
PDF [source](http://www.math.bas.bg/bantchev/place/iswim/next700.pdf)

* **Can Programming Be Liberated from the von Neumann Style? – John Backus**

John Backus is known for a number of achievements in computer science. He received the ACM Turing Award for his work on Fortran. This paper, which he presented at the award ceremony was rather shocking at the time because it said, in essence, “we got it wrong.” Backus took the opportunity to make a plea for pure functional programming. His arguments were convincing and they helped to set a research agenda which is just now starting to make some waves in the mainstream.

[PDF](/static/pdf/Backus.pdf)  
PDF [source](http://web.stanford.edu/class/cs242/readings/backus.pdf)


* **Reflections on Trusting Trust – Ken Thompson**

I once heard that when this paper was presented, people in attendance rushed back to de-compile their C compilers and look for, er, problems. This paper unveiled a hard problem at the heart of computer security. If you’ve spent any time at all thinking about security, you need to read it.

[PDF](/static/pdf/Thompson.pdf)  
PDF [source](https://www.ece.cmu.edu/~ganger/712.fall02/papers/p761-thompson.pdf)

* **Lisp: Good News, Bad News, How to Win Big – Gabriel**

This paper is a bit atypical in this list. It’s aimed at the Lisp community and it comes off as a bit of a lament. But, hidden deep within it is the Gabriel’s description of the ‘Worse is Better’ philosophy – an idea with profound implications for the acceptance and spread of technology.

[PDF](/static/pdf/Gabriel.pdf)  
PDF [source](http://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=995931189EABE60E764720C2BD1B6D64?doi=10.1.1.50.6083&rep=rep1&type=pdf)

* **An experimental evaluation of the assumption of independence in multiversion programming – John Knight and Nancy Leveson**

Behind this dry title lies something very interesting. I first heard about this paper from Ralph Johnson in a newsgroup discussion about program correctness. It turns out that one of the avenues that engineers in other disciplines take to make their products stronger – redundancy – doesn’t really work in software. Multi-version programming was the idea that you could decrease faults in critical systems by handing the spec to several teams, having them develop the software independently, and then having the systems run in parallel. A monitoring process verifies their results and if there is any discrepancy it picks the most common result. Sounds like it should work, right? Well..

[PDF](/static/pdf/Knight.pdf)  
PDF [source](http://sunnyday.mit.edu/papers/nver-tse.pdf)

* **Arguments and Results – Noble**

I think that all of the other papers in this list are rather well known in some circles. This one isn’t, or if it is, I just haven’t found that circle yet. What I like about this paper is that it takes something which we deal with every day – the set of arguments and results of functions – and it works them through a series of variations which just don’t occur to many people. The fact is, every function that you work with has a number of possible directions if could evolve in. Not all of them are appropriate, but if you know the possible directions, you’re richer for it.

[PDF](/static/pdf/Noble.pdf)  
PDF [source](http://www.laputan.org/pub/patterns/noble/noble.pdf)

* **A Laboratory For Teaching Object-Oriented Thinking – Beck, Cunningham**

There are an incredible number of papers about there about object orientation. The thing which makes this one great is its directness. OO went through a number of stages. It was once fresh and novel, then it was ornate, and then it became matter-of-fact. This paper hits upon key ideas which many people don’t talk about much any more: anthropomorphism and dropping the top/down perspective. It also shows you how you can design with index cards. It may not sound cool but it is incredibly effective.

[PDF](/static/pdf/Beck.pdf)  
PDF [source](http://www.itu.dk/people/hesj/CRC1989.pdf)

* **Programming as an Experience: the inspiration for Self – Ungar, Smith**

How many people know about the Self Project? Not enough in my opinion. Self was an attempt to take two ideas in computing and push them as far as humanly possible. The first was minimalism: the Self programming language was thoroughly in the Lisp and Smalltalk vein – everything was defined in terms of the smallest number of primitives possible. The other idea was direct manipulation – the idea that the object metaphor could be pushed all the way in the user interface – the programmer and user sit with a mouse in a sea of directly clickable objects and use them for everything. If they could’ve gotten away with dropping the keyboard, I think they would’ve.

The amount of technology which the Self project threw off is terrifying also. Self broke ground in dynamic language optimization and VM design. Chances are, your VM uses technology it pioneered. It’s also one of the more perverse ironies that the most widely distributed programming language today (JavaScript) is a prototype-based programming language which borrowed ideas from the hyper-research-y Self.

[PDF](/static/pdf/Self.pdf)  
PDF [source](http://billmaya.net/wp-content/uploads/Programming-as-an-Experience-The-Inspiration-for-Self.pdf)