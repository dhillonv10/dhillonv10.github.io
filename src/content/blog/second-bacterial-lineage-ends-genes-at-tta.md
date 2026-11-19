---
title: "Codon hunting"
author: Vik Dhillon
pubDatetime: 2026-11-19T09:00:00-08:00
slug: second-bacterial-lineage-ends-genes-at-tta
type: note
draft: false
takeaways:
  - "**A second bacterial lineage appears to end its genes at TTA,** a codon that normally encodes leucine. A Chloroflexota family shows it, with the same two changes in the stop-reading protein RF2 as the myxobacterial case. This is inferred from DNA alone."
description: "A second bacterial lineage that appears to end genes at TTA."
---

Almost every organism ends its genes with one of three stop codons: TAA, TAG or TGA. A few lineages have turned a stop codon into an amino acid. The reverse, an amino-acid codon becoming a stop, was known only in mitochondria and plastids until [Ryan Xu's agent-run screen](https://github.com/ry-xu/genome-research) reported a branch of myxobacteria that ends genes at TTA (normally leucine), and [Melnykov's KACI paper](https://doi.org/10.1073/pnas.2610659123) proposed CGA as a stop in two Asgard archaea.

I ran an independent screen and found what looks like a second bacterial case of TTA as a stop, in a different phylum, with the same change in the protein that reads stop codons. I also found a weaker archaeal case at CGA.

## The screen

Each genome gets one protein-alignment pass (DIAMOND blastx against Swiss-Prot, with frameshifts allowed). From the alignments I ask four questions of every codon: does it line up with the wrong amino acid, does a stop codon line up with an amino acid, does a sense codon sit exactly where related proteins end, and is a base skipped at a recurring codon? Thresholds were tuned on seven known cases and 160 ordinary genomes, which gave zero false flags.

So far it has covered 18,047 of 46,153 queued genomes from GTDB R232. Most flags were rediscoveries: TGA as glycine or tryptophan, the CGG skip in gut bacteria, the myxobacterial TTA. A handful were not in any published table, and most of those fell apart when I checked their relatives.

![From 18,000 genomes to two candidates](/figures/tta_fig6_funnel.webp)

## Signal 1: TTA in a Chloroflexota family

Family QHBQ01 has five genomes in GTDB, all assembled from environmental DNA. In every one, TTA sits where related proteins end 49 to 108 times more often than chance. In 90 neighbouring genomes (the rest of the order and seven sister orders) the figure stays under 9.

![One Chloroflexota family ends its genes at TTA](/figures/tta_fig1_clade_TTA.webp)

The more direct test compares the same gene across genomes. When a gene ends at TTA in one family member, the same gene in another member usually ends at a normal stop.

![Where one genome has TTA, its relatives have a normal stop](/figures/tta_fig2_ortholog_swap_TTA.webp)

That is how stop codons behave: they swap with each other freely because they mean the same thing. A leucine codon has no reason to trade places with TAA.

The TTAs are also in the raw data. In the reads behind one genome (an Antarctic lake-sediment metagenome), 205 of 207 reads spanning the flagged gene ends carry TTA. The two exceptions carry TAA.

![The TTAs are in the raw sequencing reads](/figures/tta_fig4_raw_reads_TTA.webp)

## The release factor changed the same way twice

RF2 is the protein that recognises the stop codons TAA and TGA. In the myxobacterial clade, Xu found two changes in its codon-reading region: leucine 201 to phenylalanine, and the SPF motif to SPY. QHBQ01 has leucine 201 to methionine, and SPF to SPY. Its sister families have neither.

![The stop-reading protein changed at the same two spots, twice](/figures/tta_fig3_RF2_motif.webp)

These are different phyla, so the changes arose independently. Methionine 201 with SPY occurs in 54 of 161,077 genomes with an RF2 call (Xu's count). Two unrelated lineages that end genes at TTA both altering the same two residues suggests the release factor is involved, although genomes alone cannot show that.

## Signal 2: CGA in hot-spring archaea

_Conexivisphaera_ (Thermoproteota) shows the same pattern at CGA, an arginine codon: 27 of 34 assemblies flagged, CGA swapping with normal stops in relatives, and 255 of 270 raw reads confirming the codon. A related genus, UBA168, shows it more strongly and is already listed in Xu's repository.

![A second case: hot-spring archaea that end genes at CGA](/figures/tta_fig5_signal2_CGA.webp)

I hold this one more loosely. These genomes are 60 to 67% GC, which makes CGA rare anyway, and I found no change in their release factor. One member, _Conexivisphaera calida_ NAS-02, is a cultured strain, which makes a lab test possible.

## What this does not show

- **No protein data.** Everything here is inferred from DNA. Whether proteins really end at TTA, or the ribosome stalls there and is rescued, is unknown.
- **The tRNA is still there.** Three of five QHBQ01 genomes keep the leucine tRNA that reads TTA; the myxobacteria lost theirs.
- **Gene matching is approximate.** I matched genes across genomes by reference-protein family, not by a full ortholog analysis.

C-terminal proteomics on a cultured member would settle it.
