---
title: "Do those non-coding predictions survive a reproducibility check?"
subtitle: "Revisiting the ANKRD26, GATA2 and TERT results against a measured floor"
author: Vik Dhillon
pubDatetime: 2026-11-21T10:00:00-08:00
slug: do-those-non-coding-predictions-survive-a-reproducibility-check
type: note
draft: false
takeaways:
  - "**The headline results hold.** Every claim in the earlier post sits 14 to 80 times above the smallest predicted effect that survives a meaningless change to the model's input, including the thirteen untested GATA2 enhancer predictions and the uncertain ANKRD26 variant c.-125T>C."
  - "**One claim should be withdrawn.** The suggestion that the likely-pathogenic ANKRD26 variant c.-107C>T 'does nothing through this mechanism' was a statement about a near-zero prediction, and near zero is exactly where the model is least reproducible. A null result is not available from this method."
  - "**The megakaryocyte result cannot be checked the easy way.** Re-scoring under the model's built-in megakaryocyte cell type puts 59% of these variants below the reproducibility floor, so those scores carry no directional information and can neither confirm nor refute the published AUROC of 0.88. Only a rerun with the original single-cell conditioning can."
description: "Checking the earlier three-element results against a measured reproducibility floor: what stands, and the one line that should change"
---

## What prompted this

The [earlier post](/posts/ai-model-non-coding-variants-inherited-blood-cancers) asked whether AlphaGenome 2 recovers known non-coding biology at three regulatory elements, and concluded that it does: the ANKRD26 5′UTR silencer, the GATA2 intron-4 enhancer, the TERT promoter hotspots. It also offered thirteen predictions nobody has tested.

That post rested on predicted effect sizes. It never asked how small a predicted effect has to be before the number stops meaning anything.

[A companion note](/posts/when-alphagenome-predictions-stop-being-reproducible) answers that question directly. The method needs no ground truth: AlphaGenome 2 scores a variant inside a 1 Mb window, and where that window is centred is an implementation choice, not biology. Shift the centre by 25 kb and a real effect should not move. Across 350 variants scored three ways:

![The floor, measured two ways](/figures/Fig1_floor.webp)

Below a predicted |log fold change| of 0.01, **29% of directions flip**. Above it, 5 of 218 flip. Above 0.05, none of 69 do. Expressed as a probability, P(direction is reproducible) reaches 0.95 at |LFC| ≈ **0.015**.

The 5,100 variants in that measurement are the same scan the earlier post was built on — eight genes at 600 single-base changes each, plus the 300 in the GATA2 enhancer. So the floor applies directly to the published results rather than by analogy.

## Claim by claim

![Every headline claim clears the floor, most of them by a wide margin](/figures/Fig2_claims_vs_floor.webp)

| claim from the earlier post                 | predicted \|LFC\| | times the floor | verdict             |
| ------------------------------------------- | ----------------- | --------------- | ------------------- |
| TERT C250T raises expression                | 1.197             | 80×             | stands              |
| TERT C228T raises expression                | 0.781             | 52×             | stands              |
| ANKRD26 c.-125T>C, uncertain, raises (+79%) | 0.582             | 39×             | stands              |
| GATA2 patient deletion lowers (−47%)        | 0.385             | 26×             | stands              |
| GATA2 GATA-site changes lower (up to −41%)  | 0.344             | 23×             | stands              |
| ANKRD26 pathogenic set raises (median +25%) | 0.223             | 15×             | stands              |
| GATA2 c.1017+572C>T lowers (−19%)           | 0.211             | 14×             | stands              |
| ANKRD26 c.-107C>T "does nothing"            | 0.081             | 5×              | **needs rewording** |

Nothing in the first seven rows is close to the boundary. The smallest, the known GATA2 pathogenic variant, clears it by a factor of 14. The thirteen untested GATA2 predictions were defined as changes at least as damaging as that variant, so they clear it by construction. The weakest individual member of the ANKRD26 pathogenic set still sits at 0.081, five times the floor.

This was not guaranteed. Forty-eight per cent of the full 5,100-variant scan falls below the floor. The published results came out of the reportable half, but that was luck of the selection — they were chosen for being known, and known variants tend to have large effects.

## The two elements, redrawn with the floor

Mapping each position in the two scanned windows against the floor shows how much of each element is interpretable at all.

![ANKRD26 5′UTR, read in megakaryocytes](/figures/Fig3_ANKRD26_floor.webp)

In the ANKRD26 5′UTR, every one of the 40 positions clears the floor, and all eleven known pathogenic variants sit well clear of it. The silencer stands out as a genuine feature of the map rather than as a few points rising out of noise.

![GATA2 intron-4 enhancer, read in stem and progenitor cells](/figures/Fig4_GATA2_floor.webp)

In the GATA2 enhancer, 93% of positions clear the floor in stem and progenitor cells, the known pathogenic variant sits at the dotted line, and the peaks that exceed it — the ones the earlier post flagged at the GATA site — are comfortably in reportable territory.

Both maps survive. The ranking _within_ each element, which was the earlier post's actual contribution over CADD and conservation, is reading real structure.

## The one finding that does change

The earlier post suggested that ANKRD26 c.-107C>T, listed as likely pathogenic, "does nothing through this mechanism."

That sentence should go, for a reason that applies well beyond this one variant. It is a claim built on a small predicted effect, and a small predicted effect is precisely where the model is least reproducible. **This method cannot produce a negative result.** A score near zero is indistinguishable from a score the model could not compute reliably, and the earlier post had no way to tell those apart.

What can honestly be said is narrower: the model predicts c.-107C>T **lowers** ANKRD26 in megakaryocytes by about 8%, the opposite direction to the silencer mechanism and to the other ten pathogenic variants. That is a reportable observation — 0.081 is five times the floor — and it is a more interesting statement than "does nothing." But it is a positive claim about an opposite direction, not evidence of absence.

The same caution applies to the earlier post's gnomAD analysis. Finding that high-impact predictions were not depleted from the population was reported as a negative result; about half the variants in that comparison were below the floor, so a good part of that test was run on numbers with no directional content.

## The cell-state problem, which is the real finding

Setting up the reproducibility test turned up something that was not being looked for. Fresh scores would not match the values in the published scan, and the reason is that the published scan conditioned the model on single-cell RNA profiles from public marrow datasets, while the fresh scores used the model's own built-in reference cell types.

![The same variant, two reasonable choices of cell state](/figures/Fig5_conditioning.webp)

| cell state        | n   | directions that agree             | median size ratio |
| ----------------- | --- | --------------------------------- | ----------------- |
| stem / progenitor | 76  | **95%** (100% above \|LFC\| 0.05) | 0.88              |
| monocyte          | 132 | 78%                               | 0.29              |
| megakaryocyte     | 142 | **47%**                           | 0.19              |

For stem and progenitor cells the two approaches are interchangeable, which means every GATA2 enhancer result in the earlier post — the element where the mechanism operates in stem and progenitor cells — is reproducible under either choice. That is the strongest single piece of support the earlier post has gained.

Megakaryocytes are a different matter, and the explanation matters more than the number. Under the built-in megakaryocyte condition the model produces almost nothing for these loci: the median predicted effect is **0.011**, and **59% of the variants fall below the floor**. Predictions below the floor have no directional content, so agreement with any fixed set of signs should land near 50%, and it does — 47%, unchanged at every effect size including the largest.

So the 47% is not evidence that the published megakaryocyte result is wrong. It is the floor behaving exactly as it should on a cell state where the built-in condition yields no signal. The correct reading is that **the built-in megakaryocyte condition cannot be used to check the ANKRD26 result**, in either direction. The AUROC of 0.88 was earned under custom marrow conditioning and replicated across two independent marrow datasets at 0.91; the only test that can confirm or break it is the same perturbation run under that same conditioning.

That run is cheap — 120 variants, a few minutes — and it is the obvious next thing to do.

## What I would change in the earlier post

1. **Add the floor to the methods**, and state that effects below |LFC| 0.015 are not reported in either direction.
2. **Replace the c.-107C>T sentence** with the opposite-direction reading above, and drop the implication that the model found a null.
3. **Qualify the gnomAD negative result**: roughly half of the variants in that comparison were below the floor.
4. **Say which cell state each number came from**, and record the conditioning alongside the score. A predicted effect belongs to a (variant, cell state) pair; quoting one without the other is quoting half a result. Not recording ours cost a day of work to reconstruct.
5. **Keep everything else.** The three mechanisms, the thirteen GATA2 predictions, the ANKRD26 map, the TERT ranks and the conclusion that this is a triage tool rather than evidence for classification all survive unchanged.

## What this does and does not add

It does not make the predictions more likely to be true. Reproducibility is a necessary condition, not a sufficient one: a prediction that survives a window shift can still be biologically wrong, and the GATA-site variants are still predictions awaiting a reporter assay.

What it adds is a boundary. The earlier post said the model should be used for triage. It could not say which of its own outputs were inside the range where triage means anything. Now it can, for every variant in the scan, as a calibrated probability rather than a threshold someone picked by eye.

## Methods in brief

- **Model and scan:** as in the earlier post. AlphaGenome 2 via the public API, 1 Mb context, gene-level natural-log fold change. The variant set is the same 5,100 single-base changes: 600 per gene across eight myeloid predisposition genes, plus 300 in the GATA2 intron-4 enhancer (chr3:128,483,260–128,483,359) and the ANKRD26 5′UTR window (chr10:27,100,429–27,100,468), GRCh38.
- **Reproducibility test:** 350 variants scored at window centres of 0 and ±25 kb, 1,050 calls, with Jeffreys 95% intervals and a bootstrapped logistic calibration. Full method in the companion note.
- **Cell-state comparison:** fresh scores under the model's built-in reference conditions for stem/progenitor, megakaryocyte and monocyte, matched variant by variant against the values in the published scan.
- **Effect sizes in the table** were recovered from the percentages reported in the earlier post, inverting the fold-change transform used to produce them.

## Limits

- The floor was measured under built-in reference conditions. It has not been measured under custom single-cell conditioning, which is the configuration the earlier post used. The mechanism is sequence-context handling rather than conditioning, so it should transfer, but that is an expectation and not a measurement — and it is the reason the ANKRD26 rerun matters.
- ±25 kb is one perturbation among several that could be tested. The operating floor is the worst of them, and the others have not been run.
- Reliability varies by gene. Above the floor, GATA2 showed no direction flips in 37 variants and TERT 2.6% in 39, but ANKRD26 showed 3.7% in 27 and TP53 7.3% in 41. Those sample sizes are small and the intervals wide.
