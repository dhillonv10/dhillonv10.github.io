---
layout: post
title: Blockchain-executable code
comments: True
permalink: blockchain-executable-code
---

**Balaji (@balajis) describes his take on limiting blockchain-executable code in a tweetstorm.**

> On the other hand, this really does make one question (again) whether full Turing completeness is desirable in a blockchain itself.

> My take is: eventually we'll try to limit blockchain-executable code as much as possible to just the most necessary primitives.

> That might be something intermediate between Bitcoin opcodes and Solidity. But most program logic probably should be outside the blockchain.

> Thesis: the only things you want in a blockchain language are tools to update distributed state. Everything else should be outside.

> A blockchain is a special type of database. So perhaps we eventually build a BQL. A SQL subset or augmentation, just for distributed state.

> Our school of thought with [21](https://github.com/21dotco/two1-python): make Bitcoin micropayments easy, but keep all other logic in Python.

I agree with almost everything here - It's important to realize that if the blockchain becomes the [filesystem](http://opsbug.com/blockchain-as-a-filesystem) of the web, then execution permissions will matter more. Keeping code-based logic out of the blockchain allows us to streamline development and stick to what I think is one of the most important principles in UNIX: One tool for one job. 