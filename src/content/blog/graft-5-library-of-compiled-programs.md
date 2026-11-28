---
title: "GRAFT-5: A library of compiled programs, and programs that call each other"
author: Vik Dhillon
pubDatetime: 2026-11-27T09:00:00-08:00
slug: graft-5-library-of-compiled-programs
type: feature
draft: false
takeaways:
  - "**Eighteen compiled programs now live in one model.** All 18 pass on dev and 17 of 18 on a test split scored once (mean 0.964), and the model's behaviour elsewhere is unchanged under the side-effect rule, with a maximum KL of 0.0015 on the probes. The library stopped at 18 of a planned 32 because programs that work on the same words interfere with each other, not because the model ran out of room."
  - "**Programs can call each other through registers.** A composed program takes one task from 0.49 to 1.00, and a two-level composition reaches 0.91 to 0.97 on three tasks the unedited model gets about half right."
  - "**Two limits remain.** A composed program compiled against a full library nearly coexists with it: 15 of the 18 library programs hold, but three held-out answers still change with a large shift. And compiled programs are tied to the exact prompt form they were compiled on, with accuracy falling from 0.97 to 0.62 on reworded prompts."
description: "Eighteen compiled programs installed together in one language model, programs that call each other through registers, and where both break."
---

**In short.** We installed 18 compiled programs together in one model; all 18 pass on dev, 17 of 18 on a test split scored once, and the
model's behaviour elsewhere is unchanged by the side-effect rule. The library stopped at 18 of a planned 32, not for lack of room but
because new programs interfered with installed ones that work on the same words. Programs can call each other through registers, two
levels deep in one forward pass, and the composed programs do things the model cannot (0.49 to 1.00 on one task, about 0.5 to 0.91-0.96
on three others). A composed program compiled against a full library nearly coexists with it (15 of 18 library programs held) but still
changes three held-out answers, and compiled programs are tied to the exact form of the prompt
they were compiled on. Every one of these results, good and bad, is measured below.

## 1. The question

GRAFT-4 showed that a short program can be compiled straight into the weights of a language model, with no training, and that the
compiled program adds an ability the model does not have while leaving everything else it does untouched. That result is about one program
at a time. A technique like this only becomes useful if it scales in two directions at once: many programs have to live in the same model
without getting in each other's way, and programs have to be able to use each other's results, the way functions in ordinary software call
other functions. GRAFT-5 set out to test both on Gemma-3-1B, with the same strict rule GRAFT-4 used: after every install, the whole model
must still answer 280 probe prompts and two held-out sets of 500 prompts essentially as the original model does (max KL at most 0.5 and at
most one confident answer changed), and every installed program must stay at 0.90 or better on its own dev set.

## 2. How a compiled program works

A compiled program lives entirely in new units: extra MLP neurons and attention heads that start at zero, so the grown model is exactly the
original model until something is installed. Marker units in layers 20 to 22 tag the words a program cares about, an answer flag in layer
22 marks the position where the answer is due, an attention head in layer 23 counts, compares or copies the tagged words, and units in
layers 24 and 25 compute and write the answer token. What is new in GRAFT-5 is that the intermediate values a program computes are written
to **registers**: reserved directions in the residual stream, handed out by a central allocator, that hold a typed value such as a count, a
yes / no bit or an “answer here” flag. A register is the interface through which a second program can read what a first program computed.

## 3. The library: 18 programs in one model

Why build a library at all? GRAFT-4 treated the parts we had been assembling by hand since GRAFT-3 (token markers, a counting head, a
fetch head, threshold bits, emit units) as an instruction set, and a small language exposed them to a compiler. An instruction set is only
worth having if its programs can be loaded together. A model with one compiled program is a demonstration; a model that holds dozens of
them, each one installed without disturbing the others, is closer to a machine with a standard library, where a new ability is something
you add rather than something you retrain for. So the headline goal of GRAFT-5 was a capacity curve: install programs one after another
in a fixed, pre-registered order, run the full test suite after every install, and see how far it goes. The target was 32.

![Figure F1](/figures/g5_F1_library_dev_test.webp)
_Figure F1. Dev and test accuracy of the 18 installed programs, measured together in the final model._

The library reached 18 programs. They span every operation the compiler supports: counting the items of one class in a list, asking whether
any item of a class is present, comparing two classes, fetching the first item of a class, and the derived questions “are all of these X”,
“are there at least two (three) X” and “which class is there more of”. Together they take 244 units, 226 neuron pairs and 18 heads. On
the final model every program scores 0.91 or better on dev, and on its test split, scored exactly once at the end, 17 of 18 score 0.90 or
better, with a mean of 0.964. The one exception is count.symbols.T1, the last program the curve installed, at 0.855 on test against 0.91 on
dev. Dev re-measured on the final model reproduced the last suite pass exactly for all 18, and the whole model still passed the side-effect
rule with room to spare: max KL 0.0015 on the probes, 0.0095 and 0.0215 on the two held-out sets, and no answer changed.

![Figure F2](/figures/g5_F2_capacity_curve.webp)
_Figure F2. The capacity curve, position by position, coloured by what happened to each program._

![Figure F3](/figures/g5_F3_growth.webp)
_Figure F3. The lowest dev score among installed programs, and the whole model's side effects, after every install._

The first 16 positions all ended up installed: 14 by the curve itself (two of them, both compare programs, on a
second attempt), and the two remaining “at least N” programs after a fix to a failure we found along the way, where a new program's answer flag fired again right after another program's
first answer token and appended a second answer. As the library grew from 1 to 18 programs, the lowest dev score among the installed
programs never fell below 0.91, and the whole model's max KL never rose above 0.07, a seventh of the limit. Block 3, positions 17 to 32,
went very differently: 2 of 16 programs installed on their first attempt and none of the 6 re-attempts succeeded, so the curve stopped at 18.

## 4. Why the library stopped at 18, and what that means

The block-3 failures fall into four groups, and none of them is “the model ran out of room”. Four programs landed just under the bar on
their own dev set (0.88 to 0.89). Three passed on their own but pushed an already-installed program below the bar. Five passed on dev but
failed the side-effect rule, four of them on the held-out set H1 and one on the probes. Two scored far below what the compiler predicted
(0.16 and 0.75), which we did not diagnose.

![Figure F4](/figures/g5_F4_collateral_markers.webp)
_Figure F4. Collateral damage, with the new program installed, with its markers removed, and with its answer flag removed._

The collateral damage has a clear mechanism. When compare.body-fruits.K1 was installed, compare.fruits-body.K1 fell from 0.99 to 0.62;
removing only the new program's marker units restored it to 0.99, while removing its answer flag changed nothing. The same held for
compare.colors-animals.K1 and compare.animals-colors.K1 (0.51 with the markers, 0.98 without). The new program's answer never fired on
the victim's prompts. Its markers did, because the two programs mark the same words.

![Figure F5](/figures/g5_F5_marker_dilution.webp)
_Figure F5. Each program's key-image signal at the tokens it marks, on tokens only it marks and on tokens a second program also marks._

A diagnostic run showed why shared words are a problem. Each program writes a key image on the words it marks, and its counting head
reads that image. On words only one program marks, the image arrives intact (ratio 1.00). On words two programs both mark, the layer norms
before the head shrink each program's share, and the image arrives at 0.47 to 0.76 of its size. A control program that shares no words
with the others was unaffected. Re-linking the damaged program, which means recompiling it with the new one in place, did not help: it moved
the damage to a third program on the same word list.

![Figure F6](/figures/g5_F6_budget_used.webp)
_Figure F6. How much of the grown model's spare capacity the 18 programs use._

So is 18 an upper bound? On this design, under this rule, it is where we stopped, but it is not a capacity limit. The library uses 94 of
512 available neuron pairs in its busiest layer, 18 of 32 attention heads, and 77 of 1,152 residual dimensions as registers. In
60 allocation checks no two programs ever collided on an address. What ran out is not space but isolation: programs that
work on the same word lists share the tokens their markers write to, and the more of them there are, the more they dilute each other.
Block 3 was also designed with more overlapping word lists than blocks 1 and 2, which makes it harder, so “a bigger library” and “a harder
block” cannot be fully separated from this run alone. The practical implication is concrete: the next library needs markers that do not
share a token's budget, for example one shared marker per word class that every program reads, rather than one per program.

![Figure F7](/figures/g5_F7_precision_vs_data.webp)
_Figure F7. Count precision against the amount of build-only data used to fit the count read._

The “just under the bar” failures point the same way. A program's count read is a linear fit on a few hundred build examples, and its
precision rises with data: in the fan-out experiment, the same read went from 0.85 to 0.92 exact-count accuracy as the build set grew from
460 to 2,060 items, and in the two-level experiment below, more build-only data took the weakest comparison from 0.900 to 0.920 on its
own build items, enough for the whole task to pass. Inside the capacity curve, the same fix ran out of memory twice on our 14 GB machine
and never produced a result. The ceiling here is the fitting data, not the model.

The side-effect failures are the most worrying group, because the build-side checks cannot see them. We recompiled four of the five and
measured them on every build-side text bank at every position: all four were exactly silent, with zero change to the model's output. Their
failures appear only on the held-out set, which the compiler never sees by design. One of them, a probe failure, did not reproduce at all
when recompiled. A build-side bank that covers what the held-out set covers is the missing piece.

## 5. Is the library really silent?

A compiled unit is “silent” when its output is exactly zero, not just small. Silence is the property that makes grafting different from
fine-tuning. A fine-tuned model changes a little everywhere, so every answer it gives is in principle different from the original's.
A silent program changes nothing at all on inputs that are not its task, so the model on those inputs is, to the last bit of the MLP
output, the original model. That gives three things at once. It makes side effects predictable rather than statistical: if a unit is zero
on an input, it cannot have changed the answer. It makes programs composable, because two programs that are each silent on the other's
inputs cannot interfere through those inputs. And it makes the check cheap and exhaustive: you can verify exact zeros at every position of
every prompt, instead of sampling answers and hoping the sample covers the failure.

![Figure F8](/figures/g5_F8_silence.webp)
_Figure F8. The share of positions where every non-head unit of all 18 programs is exactly zero, and the max next-token KL against the model with nothing installed, on five build-side text banks._

We measured it directly on 13,508 positions of build-side text. The library's MLP units are exactly zero at 97.6 % of positions, and the
remainder is a first-token artifact with write sizes below 5e-5. The heads are never exactly silent (attention always writes a tiny
amount), but on chat-formatted text, which is how the model is used, the library changes the next-token distribution by at most 1e-6 in
KL. Raw text, outside the chat format, is different: at 11 of 6,009 raw-text positions the library changes the next token noticeably (KL
above 0.5, at most 11.6).

![Figure F9](/figures/g5_F9_raw_leaks.webp)
_Figure F9. The 11 raw-text positions, coloured by what fired._

Three of these are a single program's markers firing on an ordinary word in the text and nudging the next token. Seven are a chain inside
one text, a list of colour codes, where the markers of atleast2.animals-colors fire on colour words, a downstream unit of
allx.animals-colors fires, and the library writes “No” in the middle of the hex codes; removing atleast2.animals-colors alone removes all
of it. The last is a piece of Python code where two programs' answer flags open together and the library writes “No”. The pass rule never
sees these, because it measures the last position of each prompt. We report them as measured and did not change the rule. The lesson is
that markers, which act before the answer position, need a gate of their own, not only the answer flag.

![Figure F10](/figures/g5_F10_invariance.webp)
_Figure F10. Accuracy of the 18 programs on reworded versions of their own dev prompts, and what they do when they get it wrong._

Silence has a second side: what does a program do on a prompt that asks for its task in a form it was not compiled on? We tested that with
four rewrites of each program's dev items that keep the answer the same: the question reworded, an irrelevant line added, the list moved
before the question, and the list written with commas. The answer is sobering. On the prompts as compiled, the library scores 0.97 on
average against the unedited model's 0.49. Reworded, it falls to 0.62 (4 of 18 programs still at 0.90), with an extra line to 0.80 (9 of
18), with commas to 0.80 (7 of 17), and with the list moved first to 0.53, no better than the unedited model. When a program gets a
rewritten prompt wrong, it falls back to the model's own answer about half the time and gives its own wrong answer the other half. Before
the run we expected rewording and the extra line to mostly hold; they did not. Compiled programs are tied to the form of the prompt they
were compiled on, and widening that form is now a first-order problem.

## 6. Message passing: programs calling programs

A library of independent programs is useful, but software gets its power from composition: one function computes a value, another uses it.
For grafts, that means one compiled program writes a value into a register and another reads it, inside a single forward pass. The rule
that makes this work is simple: a value can only be read at a layer after the one that writes it, so the callee always sits below the
caller. With the layers available, one forward pass holds two levels of calls.

The first test was a pilot. “Are there more animals than colours in this list?” was built from three separately compiled parts: two count
programs that write only a count register and never answer, and a compare program that reads only those two registers and writes the
answer. The unedited model answers this question at 0.49, a coin flip. The composed program scores 1.00 on dev and 1.00 on test, gives
exactly the same answers as a compare program compiled in one piece, and keeps side effects at max KL 0.0021 with no answer changed. The parts did not just coexist: put together, they produced
an ability none of them has alone and the model did not have.

The second test went two levels deep. Four count programs write count registers; three compare programs read them and write yes / no
registers (“more animals than colours”, “more fruits than shapes”, “fewer fruits than shapes”); and three logic programs read only those
bits and answer questions that combine them with and, or and but, such as “Are there more animals than colours and more fruits than shapes
in this list?”. This took three attempts. The first leaked (held-out max KL 8.1), the second was clean but reached 0.90 on only one of the
three tasks, and the third passed on all three: dev 0.96, 0.91 and 0.91, test 0.97, 0.91 and 0.96, max KL 0.0053. The change between
the second and third attempts was the data lesson from section 4: the middle comparison was right on only 90 % of its own build items,
and fitting it on 1,800 more build-only items fixed it.

The obvious next question is whether a composed program can join a library that is already full of programs, because that is how a
standard library would actually be used. We tested it directly: we installed the 18-program library first, compiled the same two-level
program on top of it with the allocator keeping every register and unit separate, and measured everything again.

![Figure F11](/figures/g5_F11_mp_in_library.webp)
_Figure F11. The composed and / or / but tasks, the 18 library programs' dev and the whole model's side effects: the library alone, with the composed program compiled on its own, and with the composed program compiled against the library._

The first time, the composed program still did its job but the library did not survive it. On its three tasks it scored 0.88, 0.85 and
0.89, where the unedited model scores 0.51, 0.43 and 0.49 and the library alone 0.51, 0.55 and 0.67. No unit or register was shared: the
allocator found 40 free neuron pairs and four free heads and nothing collided. Yet nine of the 18 library programs fell below 0.90, down to
0.20 for one of the “at least two” programs, and the model failed the side-effect rule badly, with max KL of 15 on the probes and over 20
on both held-out sets. The programs that broke ask questions that look like the composed program's own (counts and comparisons of animals,
colours, fruits and shapes); the ones on other word lists held.

![Figure F11b](/figures/g5_F11b_mp_diagnostic.webp)
_Figure F11b. The library and the probes with one part of the first composed program removed at a time._

We expected the cause to be the composed program's markers, by analogy with section 4, and we were wrong. Removing its markers changed
nothing, and removing its count heads changed nothing. Removing its callers, the compare and logic units and their task flags, brought the
probes back to exactly the library-alone value, so the side effects came from the callers, as they did in fan-out; the damage to the
library came from the callers and the count modules' answer flags together. The procedural cause was clear in hindsight. Every program in
the capacity curve was compiled with the installed programs' prompts as negatives, so it learned to stay quiet on them. The composed program
had been compiled with the standard negative banks only, so its flags and callers had never seen a library prompt.

So we compiled it again, this time against the library: the same recipe as the curve, with 20 build prompts from each of the 18 library
programs added as negatives for every part of the composed program. (A first try with 40 per program ran out of memory on our machine.)
The difference is large. The composed program now passes two of its three tasks, at 0.88, 0.94 and 0.92. Fifteen of the 18 library programs
stay at the bar instead of nine, and only one falls far, compare.animals-colors.K1 at 0.67, the program whose questions are closest to the
composed program's own. The probes are back to exactly the library-alone value, and the number of answers changed on the held-out sets
falls from 50 to 3. But those three are confident changes, with max KL of 23 and 9 on the two held-out sets, so the model still fails the
side-effect rule. This is the same gap that stopped the library in section 4: compiling against the library's own prompts and our
build-side banks removes nearly all of the interference we can see, and what remains shows up only on held-out text. Message passing works,
it creates abilities the model does not have, and linking a composed program to the library it joins is what makes the difference between
breaking half the library and nearly coexisting with it; closing the last part of that gap needs negatives that cover what the held-out
sets cover.

## 7. Fan-out: where message passing broke

Message passing has a harder version: one callee read by many callers. We built four count programs and twelve caller tasks over them in
one model, from “how many animals?” to “are there exactly two animals?” and “which is there more of?”. This is where the approach reached
its limit.

![Figure F12](/figures/g5_F12_fanout.webp)
_Figure F12. Fan-out over six attempts: caller tasks at the bar, and the whole model's side effects._

Over six attempts the callers got steadily better, reaching 11 of 12 at the bar in attempt 5, but accuracy and clean side effects never
arrived together. The problem is arithmetic. A caller unit writes its answer with a gain of about a hundred, so off its own task it has to be
silent to about one part in a thousand, and the per-task gates we built were not that clean on general text:
attempt 5 changed the probes by KL 20.9. Removing only the callers took that to zero on every chat-formatted bank, so the callees and registers were not the
problem.
The final attempt added a single shared gate that opens only at an answer position of one of the twelve tasks, plus a guard that holds the
callers exactly at zero everywhere else. The side effects disappeared (probes 1e-5), but the guard's small noise on real answers, multiplied
by its large gain, pulled the two count callers down from 0.94 and 0.83 to 0.70 and 0.65. Attempts 3 and 6 are the two clean ones, each at
9 of 12. Fan-out is closed at that result.

## 8. Harder components that did not pass

Two new kinds of component did not pass: “the item after X” and key-to-value lookup. Their copy heads worked, with 0 to 1 errors in 200
build items, but the markers they needed depend on context in a way the others do not, and they failed the held-out side-effect checks,
with KL up to 19.4.

## 9. What we took from Weight-Space Micromachines

Midway through the project we read “Weight-Space Micromachines: Brain Implants for LLMs” (papail.io/papers/wsm), in which an agent writes
small exact programs as separate implants in a frozen model, each one reading hidden states, computing, and writing its result back, and
each one staying off until it is needed so that the model is “bit-for-bit unchanged” otherwise. Three of its ideas went into GRAFT-5. The
first was to measure exact silence instead of inferring it from side-effect checks; that is the measurement in section 5, and it showed
that our library is silent on chat text but not bit-for-bit silent, because heads always write and markers fire on raw text. The second
was a single gate that blocks all of a set of programs when no task applies; that became the shared gate of the final fan-out attempt,
which removed the side effects but cost the count callers. The third was to test whether a program holds up when the prompt changes form;
that is the invariance check in section 5, and it showed that ours mostly do not.

## Appendix: process

Every procedure change in GRAFT-5 was written down as a dated amendment before the result it could affect (33 in all), and every
diagnostic was pre-registered before it ran. No pass rule was changed, no test split was scored twice, and the held-out sets were never
opened. Four count programs had no test split; one was generated before any scoring, with every build and dev prompt excluded.
