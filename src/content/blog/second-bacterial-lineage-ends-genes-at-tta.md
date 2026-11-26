---
title: "Codon hunting"
author: Vik Dhillon
pubDatetime: 2026-11-19T09:00:00-08:00
slug: second-bacterial-lineage-ends-genes-at-tta
type: note
draft: false
takeaways:
  - "**Two more bacterial lineages appear to end their genes at TTA,** a codon that normally encodes leucine: a family of cultured actinomycetes (Glycomycetaceae) and an uncultured Chloroflexota family. Both changed the stop-reading protein RF2 at the same positions as the one published case, and a second, larger run finds both again. This is inferred from DNA alone."
  - "**A whole class of gut bacteria carries an altered stop-reading protein and has nearly stopped using the stop codon it reads.** In Coriobacteriia, RF2 has SPT where almost all bacteria have SPF, and TGA ends 6% of genes where relatives use it for half."
  - "**A weaker third signal:** a genus of hot-spring archaea that appears to end genes at CGA, an arginine codon."
description: "Three lineages that appear to end genes at a codon that normally encodes an amino acid, and a class of bacteria that is abandoning one of its stop codons."
---

Almost every organism ends its genes with one of three stop codons: TAA, TAG or TGA. A few lineages have turned a stop codon into an amino acid. The reverse, an amino-acid codon becoming a stop, was known only in mitochondria and plastids until [Ryan Xu's agent-run screen](https://github.com/ry-xu/genome-research) reported a branch of myxobacteria that ends genes at TTA (normally leucine), and [Melnykov's KACI paper](https://doi.org/10.1073/pnas.2610659123) proposed CGA as a stop in two Asgard archaea.

I ran an independent screen of bacterial and archaeal genomes. It recovered most of the known alternative codes without being told where to look, and it turned up three lineages I could not find in earlier reports. Two of them end genes at TTA and one at CGA. A second, larger run found all three again and added a fourth result: a class of gut bacteria whose stop-reading protein has changed and which has almost abandoned the stop codon TGA.

## What the scan looks for

The genetic code is a lookup table: 61 codons mean an amino acid and 3 mean stop. The scan asks, for one genome at a time, whether that genome's table differs from the standard one.

It does this without trusting the genome's gene annotations, because those were made by software that assumed the standard code. Each genome's raw DNA is aligned against a reference set of well-studied proteins (DIAMOND blastx against Swiss-Prot, with frameshifts allowed). Wherever the genome encodes a relative of a known protein, the alignment shows which codon sits opposite which amino acid. From those alignments the scan asks four questions of all 64 codons:

1. **Does a codon line up with the wrong amino acid?** If CGG sits opposite tryptophan thousands of times and rarely opposite arginine, CGG has probably been reassigned.
2. **Does a stop codon line up with an amino acid?** A stop codon in the middle of hundreds of otherwise intact genes is being read as something.
3. **Does a sense codon sit exactly where related proteins end?** This is the test for a new stop codon. If genes keep reaching the point where their relatives end and the codon standing there is TTA, not TAA, TAG or TGA, then TTA may be acting as a stop.
4. **Is one base skipped at a recurring codon?** Some bacteria read through a specific codon by slipping one base.

Thresholds were tuned on seven published cases and 160 ordinary genomes, which gave no false flags. The genomes come from GTDB release 232 and include one representative of every archaeal species and a broad sample of bacteria, weighted toward lineages where codon usage looked unusual.

The scan also records each genome's tRNAs, its release factors (the proteins that read stop codons) and which codons its genes actually end with.

A second run repeated the whole screen with a rewritten pipeline on a different machine, this time on one genome for each of the 199,865 bacterial and archaeal species in GTDB release 232. Where a number below comes from that run, I say so.

## How a flag becomes a finding

A flag on one genome means little. Most turned out to be contamination from another organism, a few stray contigs, decaying genes in a shrinking genome, or a statistical quirk of high-GC DNA. A flag had to pass these checks before I counted it:

- **It recurs across the clade.** Every available genome of the genus or family is scanned, not just one.
- **Sister lineages don't show it.** The nearest relatives outside the clade serve as controls.
- **The codon swaps with normal stops.** The same gene is compared across genomes. If it ends at TTA in one genome and at TAA or TGA in its relatives, TTA is behaving like a stop.
- **The translation machinery fits.** I look at the release factors that read stop codons and the tRNAs that would read the codon as an amino acid.
- **It is in the raw data.** For genomes assembled from environmental DNA, the flagged codons are checked in the original sequencing reads.

## What the scan rediscovered

Most of what the scan flagged was already known. I treat this as the positive control: none of these lineages were given to it in advance.

| Change                               | Where the scan found it                                                                                      | Reported by                                                             |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------ | ----------------------------------------------------------------------- |
| TTA ends genes                       | Polyangiaceae (Myxococcota)                                                                                  | [Xu 2026](https://github.com/ry-xu/genome-research)                     |
| TTA at gene ends                     | Streptosporangiaceae: _Trebonia_, Palsa-504 and three more genera                                            | Listed as unconfirmed candidates by Xu                                  |
| CGA ends genes                       | Asgard archaeon JAMOTR01, which also reads CGG as tryptophan                                                 | [Melnykov 2026](https://doi.org/10.1073/pnas.2610659123)                |
| CGA at gene ends                     | Methanogens (_Methanoprimaticola_, _Methanomethylophilus_, _Methanofrustulum_) and the archaeal genus UBA168 | Listed by Xu                                                            |
| One base skipped at CGG              | Gut bacteria of the order TANB77                                                                             | Xu 2026                                                                 |
| TGA read as glycine                  | Absconditabacterales and relatives                                                                           | NCBI translation table 25                                               |
| TGA read as tryptophan               | Mycoplasmas and insect symbionts                                                                             | NCBI translation table 4                                                |
| TGA read as tryptophan               | _Equivita_ (Eggerthellaceae)                                                                                 | [Parks et al. 2026](https://pmc.ncbi.nlm.nih.gov/articles/PMC13462651/) |
| TGA read as tryptophan               | Two families of Minisyncoccia                                                                                | Noted in Xu's repository                                                |
| CGA and CGG read as tryptophan       | Absconditabacterales                                                                                         | [Shulgina and Eddy 2021](https://elifesciences.org/articles/71402)      |
| CGG read as tryptophan               | _Anaerococcus_                                                                                               | Shulgina and Eddy 2021                                                  |
| AGG read as methionine               | Gut bacteria of the family CAG-288 (_Enterosoma_ in current GTDB naming)                                     | Shulgina and Eddy 2021, in the same family                              |
| TAG read as pyrrolysine              | Methanosarcinales and other methanogens                                                                      | Long established                                                        |
| A selenocysteine tRNA that reads TAG | _Geodermatophilus_                                                                                           | [Mukai et al. 2016](https://doi.org/10.1002/anie.201511657)             |

Two of these go slightly beyond the earlier reports. In Streptosporangiaceae the scan sees TTA at gene ends in three genera that are not on Xu's list (DASQVO01, PALSA-505 and Bog-532). And CGG read as tryptophan shows up in JAUNAV01, a genus next to _Anaerococcus_.

Across all the archaea, the only new stop the scan finds is CGA, in six genera. Five were known or listed; the sixth is Signal 4 below.

![Across the archaea, CGA ends genes in six genera](/figures/tta_fig8_CGA_archaea.webp)

## Signal 1: TTA in a family of cultured actinomycetes

Glycomycetaceae is a small family of soil and salt-tolerant actinomycetes. Five of its six named genera have genomes in GTDB: _Glycomyces_, _Stackebrandtia_, _Haloglycomyces_, _Salininema_ and _Natronoglycomyces_. (GTDB places them inside Micromonosporaceae.) They are cultured organisms with type strains and finished genomes.

In 54 of 61 genomes, TTA sits where related proteins end 18 to 181 times more often than chance. Six of the remaining seven show the same pattern below the flagging threshold. In one genome from each of 39 other genera of the same GTDB family, none is flagged and the highest value is 12.

![A family of cultured actinomycetes ends genes at TTA](/figures/tta_fig9_TTA_Glycomycetaceae.webp)

The gene-by-gene comparison agrees. For 132 genes that end at TTA in one genome, the same gene in the other family members usually ends at a normal stop, and in sister genera it almost never ends at TTA.

![Where one genome has TTA, its relatives have a normal stop](/figures/tta_fig10_ortholog_swap_Glycomycetaceae.webp)

That is how stop codons behave: they swap with each other freely because they mean the same thing. A leucine codon has no reason to trade places with TAA.

The genes involved are ordinary working genes. The 876 TTA gene ends in these genomes fall in 568 protein families, among them arginine tRNA ligase, ribonuclease HI and GMP reductase, so decaying genes are not the explanation. And TTA has to be the end of these proteins: after the TTA, the next standard stop codon in the same reading frame is a median of 35 codons away, and more than 50 codons away for 41% of the genes. If TTA were still read as leucine, hundreds of proteins would carry long extra tails.

![If TTA were still leucine, these proteins would grow long tails](/figures/tta_fig17_TTA_next_stop_Glycomycetaceae.webp)

An independent method points the same way. Melnykov's KACI infers each codon's meaning from how it is used inside genes. In its published table it assigns TTA to leucine in 20 of 21 sister genomes, and leaves TTA unassigned in all 11 Glycomycetaceae genomes I could match. A codon that has stopped appearing inside genes is what a new stop would look like to that method. KACI does not mark these genomes as unusual.

The second run finds the family again. With a rewritten pipeline on different hardware, TTA stands alone at gene ends in 27 of 33 _Glycomyces_ species and 8 of 8 _Stackebrandtia_ species. No genus outside the known and reported ones passed the same test.

![A second, larger run finds the same lineages](/figures/tta_fig18_replication_full_run.webp)

I rank this first for three reasons. It holds across 61 genomes in five genera. The genomes come from pure cultures, so contamination and assembly error are unlikely explanations. And the organisms can be grown, so the prediction can be tested in a lab.

The weak point is the count per genome. TTA is one of the rarest codons in these high-GC genomes, so each has only 4 to 41 TTA gene ends. The case rests on 61 genomes agreeing, not on any one of them.

## Signal 2: TTA in a Chloroflexota family

Family QHBQ01 has five genomes in GTDB, all assembled from environmental DNA. In every one, TTA sits where related proteins end 49 to 108 times more often than chance. In 90 neighbouring genomes (the rest of the order and seven sister orders) the figure stays under 9. The second run flags all five again.

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

The second run puts a limit on that argument. The tyrosine alone is not distinctive: SPY is the usual motif in 11,657 complete genomes across 65 phyla, most of them Alphaproteobacteria with no TTA gene ends. What is rare is the Glycomycetaceae form, SKY. It occurs in 201 complete genomes, 195 of them actinomycetes, and those include Glycomycetaceae and the Streptosporangiaceae genera with TTA at gene ends. So the case for RF2 rests on SKY and on position 201, not on the tyrosine.

![Two rare forms of the motif, each confined to one group](/figures/tta_fig16_RF2_motif_census.webp)

Genomes alone cannot show this, and the change is not sufficient by itself. Several Streptosporangiaceae genera carry an SKY motif; some show TTA at gene ends clearly and one shows almost none. Three _Streptomyces_ species carry methionine 201 with SPY and have no TTA gene ends at all.

## Signal 3: a class that is abandoning TGA

The census of RF2 motifs turned up a second rare form, SPT, and it belongs almost entirely to one class of bacteria. Coriobacteriia are actinomycetes of the gut and of anoxic sediments, and include _Collinsella_, _Eggerthella_ and _Atopobium_.

Of 1,376 complete Coriobacteriia genomes, 1,346 carry RF2 with SPT in place of SPF. In most of the remaining 30 the motif could not be read; one has SPF. None of the 15,454 complete genomes from the other classes of the phylum has SPT, and in all other bacteria there are six. The change is present in both orders of the class, so it arose once, in their common ancestor.

I looked at the protein directly in nine genomes from both orders. It is a full-length RF2 with its catalytic motif intact, and the loop that reads the codon differs from other bacteria at the same four positions in all nine: the motif itself and three residues next to it.

![The codon-reading loop of RF2 changed in every one of them](/figures/tta_fig15_RF2_loop_alignment.webp)

TGA is the one stop codon that only RF2 can read, and this class has nearly stopped using it. Coriobacteriia end a median of 46% of genes at TAA, 48% at TAG and 6% at TGA. Other actinomycetes in the same GC range, with the standard motif, end 17% at TAA, 31% at TAG and 53% at TGA.

![One class of bacteria has almost stopped ending genes at TGA](/figures/tta_fig12_TGA_vs_GC_Actinomycetota.webp)

Stop-codon use depends strongly on GC content, so I compared every class with genomes of the same GC that carry the standard motif. Coriobacteriia sit 40 percentage points below expectation for TGA. That is the lowest of 177 bacterial classes; the next is 24 points below.

![No other class of bacteria avoids TGA this much](/figures/tta_fig13_class_ranking_TGA.webp)

Inside the class there is a gradient. Every family carries the changed RF2 and uses TAG for about half its gene ends. But TGA use runs from 35–45% in the families of the order Anaerosomatales down to 5% in Coriobacteriaceae. The motif change is shared by all of them; the loss of TGA has gone further in some than in others.

![Every family has the changed release factor; TGA loss varies](/figures/tta_fig14_Coriobacteriia_families_stops.webp)

Two things from the literature connect to this. First, [Parks and colleagues](https://pmc.ncbi.nlm.nih.gov/articles/PMC13462651/) showed that two genera inside this class, _Equivita_ and _Gorillivita_, have gone all the way: they lost RF2 and read TGA as tryptophan. They also reported that the family around those genera uses TGA less than the other stops. What the scan adds is one level up: the whole class shares a changed RF2 and a shift away from TGA, which would explain why the reassignment happened there.

Second, SPT is a known laboratory mutation. [Ito and colleagues](https://doi.org/10.1038/35001115) identified SPF as the part of RF2 that reads the codon, and a [later study in _Bacillus subtilis_](https://www.nature.com/articles/s41467-019-13408-7) changed SPF to SPT specifically to switch off termination by RF2; the mutant could still rescue stalled ribosomes. So a thousand species carry, as their natural RF2, a motif used in the lab to disable stop-codon reading.

That cannot be the whole story in these organisms. _Parvivirga hydrogeniphila_, a cultured member of the Anaerosomatales, has the SPT motif and still ends about 60% of its genes at TGA, so its RF2 must still read that codon. The three neighbouring changes in the loop may compensate; the genomes cannot say.

As an observation this is the best supported result here: it holds across more than a thousand species. As an explanation it is less certain than the TTA signals, because the motif change happened once. However many genomes carry it, that is a single instance of "release factor changes, then a stop codon declines", and some clades with the standard motif avoid TGA strongly too (Hymenobacteraceae end 12% of genes at TGA).

## Signal 4: CGA in hot-spring archaea

_Conexivisphaera_ (Thermoproteota) shows the same pattern at CGA, an arginine codon: 27 of 34 assemblies flagged, CGA swapping with normal stops in relatives, and 255 of 270 raw reads confirming the codon. A related genus, UBA168, shows it more strongly and is already listed in Xu's repository.

![Hot-spring archaea that end genes at CGA](/figures/tta_fig5_signal2_CGA.webp)

I hold this one most loosely. These genomes are 60 to 67% GC, which makes CGA rare anyway, and I found no change in their release factor. One member, _Conexivisphaera calida_ NAS-02, is a cultured strain, which makes a lab test possible.

## What the second run did not find

The second run was also a search for more, and on three counts it found nothing.

- **No further lineage with a new stop codon.** Across 199,865 species, every genus where TTA or CGA stands alone at gene ends is one of those above or one already published.
- **No new kind of codon change.** Every reassignment that recurs in a clade is of a kind already in the table of rediscoveries.
- **No 23rd amino acid.** Two amino acids beyond the standard twenty, selenocysteine and pyrrolysine, are each inserted at a stop codon by a dedicated tRNA. I looked for a third such system: a tRNA that reads a stop codon, in a genome where that stop has not been reassigned, and that is neither of the two known tRNAs. The search recovered the known systems at scale (selenocysteine tRNAs in 45,830 genomes, pyrrolysine in 838). Of the unexplained tRNAs, most did not survive a second tRNA-finding program, which showed the first had often read the anticodon one base off. The 1,837 genomes that did survive are scattered across at least fifteen phyla. The largest group sharing one is _Nostoc_, where 66 of 127 species carry a tRNA that reads TAG, and those genomes have no more in-frame TAG codons than _Nostoc_ genomes without it (a median of 17 against 16).

![The search for a 23rd amino acid came back empty](/figures/tta_fig19_stop_tRNA_search.webp)

This last search only sees a new amino acid that is inserted at a stop codon, and only inside proteins that have a well-studied relative.

## What this does not show

- **No protein data.** Everything here is inferred from DNA. Whether proteins really end at TTA or CGA, or the ribosome stalls there and is rescued, is unknown. So is what the SPT form of RF2 does in a living cell.
- **The tRNA is still there.** Most Glycomycetaceae genomes and three of five QHBQ01 genomes keep the leucine tRNA that reads TTA; the myxobacteria lost theirs. A codon cannot be both leucine and stop without some cost, so either the tRNA is little used or the picture is more complicated than a clean reassignment. Two genera of the family, _Salininema_ and _Haloglycomyces_, have lost that tRNA entirely, as the myxobacteria did, yet they still have 18 to 52 TTA codons inside conserved genes and I cannot say what reads them. In _Glycomyces_ the tRNA's stems carry paired changes, the mark of a tRNA still in use.
- **The Coriobacteriia change happened once.** A thousand genomes share it, but it is one evolutionary event, so it cannot show that the release factor change caused the move away from TGA. The laboratory result on SPT comes from model bacteria, not from Coriobacteriia.
- **Gene matching is approximate.** I matched genes across genomes by reference-protein family, not by a full ortholog analysis.
- **Novelty is as far as I could check.** None of the three clades appears in Xu's repository, among the genomes KACI marks as unusual, or in NCBI's code tables, and a web search found no report of TTA as a stop in Glycomycetaceae. I also found no report of a natural SPT form of RF2 or of the class-wide pattern in Coriobacteriia.

C-terminal proteomics on a cultured member would settle it. _Stackebrandtia nassauensis_ and _Conexivisphaera calida_ are the obvious candidates. For Coriobacteriia, the direct test is whether RF2 from _Collinsella_ or _Parvivirga_ terminates at TGA in a purified translation system.

## Methods in brief

- **Genomes.** GTDB release 232, with its taxonomy and CheckM2 completeness. Assemblies were downloaded from NCBI. The first run covered every archaeal species and a sample of bacteria; the second covered one genome for each of 199,865 species.
- **Alignment.** Each genome's DNA was aligned to a reduced set of Swiss-Prot prokaryotic proteins with DIAMOND blastx, with frameshifts allowed. Gene annotations were not used.
- **The four tests.** For each of the 64 codons: the amino acid it aligns to, whether a stop codon aligns to an amino acid inside genes, whether the codon sits where the reference protein ends, and whether one base is skipped there.
- **Gene-end test.** In the second run a codon counts when it stands at gene ends at least 15 times more often than its use inside genes predicts, and at least 3 times more than the next amino-acid codon. A clade counts when two or more species pass.
- **Follow-up of a flag.** All genomes of the clade and its nearest relatives were scanned. Genes were compared across genomes by reference-protein family. For genomes assembled from environmental DNA, flagged positions were checked in the raw reads.
- **Release factors.** RF1 and RF2 were found by alignment and the codon-reading motif read from the best match. For nine Coriobacteriia genomes and six others, genes were predicted with Pyrodigal and the full RF2 protein compared.
- **Stop-codon use.** The share of gene ends at TAA, TAG and TGA, from the same alignments. Expected use is the median for genomes in the same 2% GC band that carry the standard SPF motif. Classes with at least 20 genomes that are at least 90% complete were compared.
- **tRNAs.** Found with ARAGORN. Any tRNA that appeared to read a stop codon was checked with tRNAscan-SE and kept only if both programs agreed.
- **Controls.** Thresholds were set on seven published cases and 160 ordinary genomes. The published code changes in the table above were not given to the scan in advance.
