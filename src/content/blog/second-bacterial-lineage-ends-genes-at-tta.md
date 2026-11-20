---
title: "Codon hunting"
author: Vik Dhillon
pubDatetime: 2026-11-19T09:00:00-08:00
slug: second-bacterial-lineage-ends-genes-at-tta
type: note
draft: false
takeaways:
  - "**Two more bacterial lineages appear to end their genes at TTA,** a codon that normally encodes leucine: a family of cultured actinomycetes (Glycomycetaceae) and an uncultured Chloroflexota family. Both changed the stop-reading protein RF2 at the same positions as the one published case. This is inferred from DNA alone."
  - "**A weaker third signal:** a genus of hot-spring archaea that appears to end genes at CGA, an arginine codon."
description: "Three lineages that appear to end genes at a codon that normally encodes an amino acid."
---

Almost every organism ends its genes with one of three stop codons: TAA, TAG or TGA. A few lineages have turned a stop codon into an amino acid. The reverse, an amino-acid codon becoming a stop, was known only in mitochondria and plastids until [Ryan Xu's agent-run screen](https://github.com/ry-xu/genome-research) reported a branch of myxobacteria that ends genes at TTA (normally leucine), and [Melnykov's KACI paper](https://doi.org/10.1073/pnas.2610659123) proposed CGA as a stop in two Asgard archaea.

I ran an independent screen of bacterial and archaeal genomes. It recovered most of the known alternative codes without being told where to look, and it turned up three lineages I could not find in earlier reports. Two of them end genes at TTA and one at CGA.

## What the scan looks for

The genetic code is a lookup table: 61 codons mean an amino acid and 3 mean stop. The scan asks, for one genome at a time, whether that genome's table differs from the standard one.

It does this without trusting the genome's gene annotations, because those were made by software that assumed the standard code. Each genome's raw DNA is aligned against a reference set of well-studied proteins (DIAMOND blastx against Swiss-Prot, with frameshifts allowed). Wherever the genome encodes a relative of a known protein, the alignment shows which codon sits opposite which amino acid. From those alignments the scan asks four questions of all 64 codons:

1. **Does a codon line up with the wrong amino acid?** If CGG sits opposite tryptophan thousands of times and rarely opposite arginine, CGG has probably been reassigned.
2. **Does a stop codon line up with an amino acid?** A stop codon in the middle of hundreds of otherwise intact genes is being read as something.
3. **Does a sense codon sit exactly where related proteins end?** This is the test for a new stop codon. If genes keep reaching the point where their relatives end and the codon standing there is TTA, not TAA, TAG or TGA, then TTA may be acting as a stop.
4. **Is one base skipped at a recurring codon?** Some bacteria read through a specific codon by slipping one base.

Thresholds were tuned on seven published cases and 160 ordinary genomes, which gave no false flags. The genomes come from GTDB release 232 and include one representative of every archaeal species and a broad sample of bacteria, weighted toward lineages where codon usage looked unusual.

## How a flag becomes a finding

A flag on one genome means little. Most turned out to be contamination from another organism, a few stray contigs, decaying genes in a shrinking genome, or a statistical quirk of high-GC DNA. A flag had to pass these checks before I counted it:

- **It recurs across the clade.** Every available genome of the genus or family is scanned, not just one.
- **Sister lineages don't show it.** The nearest relatives outside the clade serve as controls.
- **The codon swaps with normal stops.** The same gene is compared across genomes. If it ends at TTA in one genome and at TAA or TGA in its relatives, TTA is behaving like a stop.
- **The translation machinery fits.** I look at the release factors that read stop codons and the tRNAs that would read the codon as an amino acid.
- **It is in the raw data.** For genomes assembled from environmental DNA, the flagged codons are checked in the original sequencing reads.

## What the scan rediscovered

Most of what the scan flagged was already known. I treat this as the positive control: none of these lineages were given to it in advance.

| Change                               | Where the scan found it                                                                                      | Reported by                                                        |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------ |
| TTA ends genes                       | Polyangiaceae (Myxococcota)                                                                                  | [Xu 2026](https://github.com/ry-xu/genome-research)                |
| TTA at gene ends                     | Streptosporangiaceae: _Trebonia_, Palsa-504 and three more genera                                            | Listed as unconfirmed candidates by Xu                             |
| CGA ends genes                       | Asgard archaeon JAMOTR01, which also reads CGG as tryptophan                                                 | [Melnykov 2026](https://doi.org/10.1073/pnas.2610659123)           |
| CGA at gene ends                     | Methanogens (_Methanoprimaticola_, _Methanomethylophilus_, _Methanofrustulum_) and the archaeal genus UBA168 | Listed by Xu                                                       |
| One base skipped at CGG              | Gut bacteria of the order TANB77                                                                             | Xu 2026                                                            |
| TGA read as glycine                  | Absconditabacterales and relatives                                                                           | NCBI translation table 25                                          |
| TGA read as tryptophan               | Mycoplasmas and insect symbionts                                                                             | NCBI translation table 4                                           |
| CGA and CGG read as tryptophan       | Absconditabacterales                                                                                         | [Shulgina and Eddy 2021](https://elifesciences.org/articles/71402) |
| CGG read as tryptophan               | _Anaerococcus_                                                                                               | Shulgina and Eddy 2021                                             |
| AGG read as methionine               | Gut bacteria of the family CAG-288 (_Enterosoma_ in current GTDB naming)                                     | Shulgina and Eddy 2021, in the same family                         |
| TAG read as pyrrolysine              | Methanosarcinales and other methanogens                                                                      | Long established                                                   |
| A selenocysteine tRNA that reads TAG | _Geodermatophilus_                                                                                           | [Mukai et al. 2016](https://doi.org/10.1002/anie.201511657)        |

Two of these go slightly beyond the earlier reports. In Streptosporangiaceae the scan sees TTA at gene ends in three genera that are not on Xu's list (DASQVO01, PALSA-505 and Bog-532). And CGG read as tryptophan shows up in JAUNAV01, a genus next to _Anaerococcus_.

Across all the archaea, the only new stop the scan finds is CGA, in six genera. Five were known or listed; the sixth is Signal 3 below.

![Across the archaea, CGA ends genes in six genera](/figures/tta_fig8_CGA_archaea.webp)

## Signal 1: TTA in a family of cultured actinomycetes

Glycomycetaceae is a small family of soil and salt-tolerant actinomycetes. Five of its six named genera have genomes in GTDB: _Glycomyces_, _Stackebrandtia_, _Haloglycomyces_, _Salininema_ and _Natronoglycomyces_. (GTDB places them inside Micromonosporaceae.) They are cultured organisms with type strains and finished genomes.

In 54 of 61 genomes, TTA sits where related proteins end 18 to 181 times more often than chance. Six of the remaining seven show the same pattern below the flagging threshold. In one genome from each of 39 other genera of the same GTDB family, none is flagged and the highest value is 12.

![A family of cultured actinomycetes ends genes at TTA](/figures/tta_fig9_TTA_Glycomycetaceae.webp)

The gene-by-gene comparison agrees. For 132 genes that end at TTA in one genome, the same gene in the other family members usually ends at a normal stop, and in sister genera it almost never ends at TTA.

![Where one genome has TTA, its relatives have a normal stop](/figures/tta_fig10_ortholog_swap_Glycomycetaceae.webp)

That is how stop codons behave: they swap with each other freely because they mean the same thing. A leucine codon has no reason to trade places with TAA.

An independent method points the same way. Melnykov's KACI infers each codon's meaning from how it is used inside genes. In its published table it assigns TTA to leucine in 20 of 21 sister genomes, and leaves TTA unassigned in all 11 Glycomycetaceae genomes I could match. A codon that has stopped appearing inside genes is what a new stop would look like to that method. KACI does not mark these genomes as unusual.

I rank this first for three reasons. It holds across 61 genomes in five genera. The genomes come from pure cultures, so contamination and assembly error are unlikely explanations. And the organisms can be grown, so the prediction can be tested in a lab.

The weak point is the count per genome. TTA is one of the rarest codons in these high-GC genomes, so each has only 4 to 41 TTA gene ends. The case rests on 61 genomes agreeing, not on any one of them.

## Signal 2: TTA in a Chloroflexota family

Family QHBQ01 has five genomes in GTDB, all assembled from environmental DNA. In every one, TTA sits where related proteins end 49 to 108 times more often than chance. In 90 neighbouring genomes (the rest of the order and seven sister orders) the figure stays under 9.

![One Chloroflexota family ends its genes at TTA](/figures/tta_fig1_clade_TTA.webp)

The gene-by-gene comparison shows the same swap as in Glycomycetaceae.

![Where one genome has TTA, its relatives have a normal stop](/figures/tta_fig2_ortholog_swap_TTA.webp)

Because these genomes were assembled from mixed environmental DNA, I checked the raw data. In the reads behind one genome (an Antarctic lake-sediment metagenome), 205 of 207 reads spanning the flagged gene ends carry TTA. The two exceptions carry TAA.

![The TTAs are in the raw sequencing reads](/figures/tta_fig4_raw_reads_TTA.webp)

This ranks second because it rests on five uncultured genomes. The per-genome signal is as clear as in Signal 1.

## The release factor changed at the same spots, three times

RF2 is the protein that recognises the stop codons TAA and TGA. A three-residue motif, SPF, sits at the point where it reads the codon. In the myxobacterial clade, Xu found two changes in this region: leucine 201 to phenylalanine, and SPF to SPY.

Both new TTA lineages changed the same two positions. QHBQ01 has methionine at 201 and SPY. Glycomycetaceae has valine at 201 and tyrosine at the end of the motif in all 60 genomes with a readable RF2: SKY in 59 and SQY in _Natronoglycomyces_. Their sister lineages have the standard leucine and SPF.

![The stop-reading protein changed at the same spots, three times](/figures/tta_fig11_RF2_three_lineages.webp)

These are three different phyla, so the changes arose independently. In all three the last residue of the motif went from phenylalanine to tyrosine. That makes RF2 a plausible part of the mechanism: a release factor that has learned to accept TTA.

Genomes alone cannot show this, and the change is not sufficient by itself. Several Streptosporangiaceae genera carry an SKY motif; some show TTA at gene ends clearly and one shows almost none. Three _Streptomyces_ species carry methionine 201 with SPY and have no TTA gene ends at all.

## Signal 3: CGA in hot-spring archaea

_Conexivisphaera_ (Thermoproteota) shows the same pattern at CGA, an arginine codon: 27 of 34 assemblies flagged, CGA swapping with normal stops in relatives, and 255 of 270 raw reads confirming the codon. A related genus, UBA168, shows it more strongly and is already listed in Xu's repository.

![Hot-spring archaea that end genes at CGA](/figures/tta_fig5_signal2_CGA.webp)

I hold this one most loosely. These genomes are 60 to 67% GC, which makes CGA rare anyway, and I found no change in their release factor. One member, _Conexivisphaera calida_ NAS-02, is a cultured strain, which makes a lab test possible.

## What this does not show

- **No protein data.** Everything here is inferred from DNA. Whether proteins really end at TTA or CGA, or the ribosome stalls there and is rescued, is unknown.
- **The tRNA is still there.** Most Glycomycetaceae genomes and three of five QHBQ01 genomes keep the leucine tRNA that reads TTA; the myxobacteria lost theirs. A codon cannot be both leucine and stop without some cost, so either the tRNA is little used or the picture is more complicated than a clean reassignment.
- **Gene matching is approximate.** I matched genes across genomes by reference-protein family, not by a full ortholog analysis.
- **Novelty is as far as I could check.** None of the three clades appears in Xu's repository, among the genomes KACI marks as unusual, or in NCBI's code tables, and a web search found no report of TTA as a stop in Glycomycetaceae.

C-terminal proteomics on a cultured member would settle it. _Stackebrandtia nassauensis_ and _Conexivisphaera calida_ are the obvious candidates.
