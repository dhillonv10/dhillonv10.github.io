---
title: "Six months behind: How far open-weight LLMs trail the closed frontier"
author: Vik Dhillon
pubDatetime: 2026-11-23T12:00:00Z
slug: open-weight-llms-lag-closed-frontier
type: note
draft: false
takeaways:
  - "**Open weights trail the closed frontier by about six months, and have since mid-2024.** Today's best open-weight model, Kimi K3.1 Pro (ECI 161.2), matches where the closed frontier was 6.8 months ago (90% interval 5.3–8.4)."
  - "**Time-to-parity has not shrunk since 2024.** After the 15-month GPT-4 gap, every closed record-setter since 2024 was matched in 3.4–9.4 months (median 6.8). Regressing lag on release date gives +1.3 months per year (R² 0.36), so if anything the lag is growing."
  - "**2026 was a slightly worse year for open weights.** The weekly lag averaged 4.8 months in 2024, 4.9 in 2025 and 6.4 in 2026. Since January 2025 the closed frontier has climbed 18.2 ECI points a year and the open frontier 13.3."
  - "**The lag depends a lot on the task.** Agent and coding benchmarks are within 1.5–5 months. Forecasting, chess puzzles, factual recall and SimpleBench trail by about 10–17 months."
  - "**The formula:** ETA = t_last open record + (ECI_target − ECI_open now) / β_open, with β_open between 13.3 and 18.6 ECI/yr. It puts open-weight parity with Claude Fable 5.2 and GPT-6.2 Astra around **June 2027** (range April–December 2027)."
description: "I anchored every closed frontier release since GPT-4 and measured how long open-weight models took to match it. Since 2024 the answer has been about six months, and it is not shrinking."
---

## 1. The question

There is a common story about open models: they started far behind, they caught up fast, and soon they will be level with the closed labs. I wanted to check that story against the benchmark record instead of my impression of it.

The method is simple. Take every closed model that set a new state of the art when it was released. Use it as an anchor. Then measure how long it took for the first open-weight model to reach the same score. Repeat for every anchor since GPT-4, on as many benchmarks as I could find, and see which way the number moves.

A note on terms. Almost none of these models are open source in the OSI sense. They are open weights: you can download and run them, often under a license with restrictions. I use "open" to mean open weights throughout, and I follow Epoch AI's license labels.

## 2. Data

I used four sources, all downloaded on 23 November 2026.

| Source                                     | What it gives                                                | Coverage                                               |
| ------------------------------------------ | ------------------------------------------------------------ | ------------------------------------------------------ |
| Epoch AI Capabilities Index (ECI)          | One cross-benchmark score per model, with 500 bootstrap fits | 258 models (124 closed, 113 open), Mar 2023 – Nov 2026 |
| Epoch AI Benchmarking Hub                  | Per-benchmark scores, joined to open/closed labels           | 27 benchmarks, 2,639 model scores                      |
| LMArena leaderboard dataset (Hugging Face) | Arena Elo with license, every dated snapshot                 | 260 text snapshots, May 2023 – Nov 2026                |
| Artificial Analysis leaderboard            | Intelligence Index v5.0.1, per-eval scores, prices           | 126 model configurations, today only                   |

ECI is the backbone. Epoch fits it across 57 benchmarks and scales it so Claude 3.5 Sonnet = 130 and GPT-5 = 150. One composite score per model keeps a saturated or brand-new benchmark from dominating the story. Because Epoch publishes 500 bootstrap fits, every ECI lag and forecast below comes with an uncertainty band.

I measure the gap two ways:

- **Horizontal lag (months):** how long ago the closed frontier first reached today's open-frontier score. This is the number that matters for "how far behind."
- **Vertical gap (points):** closed frontier score minus open frontier score.

Two data quirks shaped the analysis. ECI has no closed model older than GPT-4, so until open models passed GPT-4 (June 2024) the horizontal lag is only a lower bound. I show it dashed and leave it out of the averages. And the LMArena snapshots on Hugging Face do not include GPT-4 until December 2023 or any Claude model until March 2024, so the arena analysis starts in December 2023 and the leaderboard-share chart in March 2024.

## 3. The staircase

![Closed and open ECI frontiers with horizontal arrows from each closed record-setter to the first open model that matched it](/figures/oss_fig01_eci_staircase_hero.webp)
_Figure F1. Closed (blue) and open-weight (orange) ECI frontiers, March 2023 to November 2026. Each grey arrow runs from a closed record-setter to the first open model that matched it. Dashed orange lines are closed records that are still unmatched._

Both frontiers climb as staircases. Each closed step is matched by an open step roughly half a year later.

![Bar chart of time-to-parity for each closed record-setting model](/figures/oss_fig02_time_to_parity_ledger.webp)
_Figure F2. Months from each closed record-setter's release to the first open-weight model with an equal or higher ECI. Whiskers are 90% intervals over 500 bootstrap fits. Hatched bars are still unmatched, so their lag is a lower bound._

| Closed anchor     | Released | ECI   | First open match | Lag (months) |
| ----------------- | -------- | ----- | ---------------- | ------------ |
| GPT-4             | Mar 2023 | 121.6 | Qwen2-72B        | 14.8         |
| Claude 3 Opus     | Feb 2024 | 125.6 | Llama 3.1-405B   | 4.8          |
| Claude 3.5 Sonnet | Jun 2024 | 130.0 | DeepSeek-V3      | 6.2          |
| o1-mini           | Sep 2024 | 135.3 | DeepSeek-R1      | 4.3          |
| o1                | Dec 2024 | 141.2 | Kimi K2          | 6.8          |
| o3                | Apr 2025 | 147.0 | Kimi K2.5        | 9.4          |
| GPT-5             | Aug 2025 | 150.0 | GLM-5.1          | 8.0          |
| Gemini 3 Pro      | Nov 2025 | 153.0 | GLM-5.2          | 6.9          |
| GPT-5.2 Pro       | Dec 2025 | 157.4 | Kimi K3          | 7.1          |
| GPT-5.4 Pro       | Mar 2026 | 160.3 | Kimi K3.1 Pro    | 7.6          |
| GPT-5.5 Pro       | Apr 2026 | 162.8 | —                | ≥ 7.0        |
| Claude Fable 5.2  | Nov 2026 | 173.4 | —                | ≥ 0.5        |

Release dates follow Epoch's records, which can differ by a few days from announcement dates. GPT-4 is the outlier. It took open weights 15 months to reach it. After that, the gap fell to about six months.

![Scatter of time-to-parity against closed release date with a gently rising regression line](/figures/oss_fig16_lag_regression.webp)
_Figure F3. Time-to-parity against the closed model's release date. OLS on the 15 matched anchors released since January 2024: lag = 5.1 + 1.27·t (t in years since Jan 2024), R² = 0.36. GPT-4 is shown but left out of the fit._

The "catching up" story is real for 2023–2024. From 2024 on, it is not supported. The fitted lag rises by about 1.3 months a year. That fit rests on 15 points and explains about a third of the variance, so I read it as "not shrinking" rather than "clearly growing." The weekly series below points the same way.

## 4. A sawtooth, not a slide

Anchors only sample the gap at a few moments. Measuring the horizontal lag every week gives the full picture.

![Weekly horizontal lag and ECI gap over time, showing a sawtooth pattern](/figures/oss_fig03_lag_and_gap_timeseries.webp)
_Figure F4. Top: weekly horizontal lag, with a 90% bootstrap band. The dashed segment is a lower bound only. Bottom: the vertical ECI gap. Vertical lines mark Llama 3.1-405B, o1, DeepSeek-R1, Kimi K3 and Claude Fable 5.2._

The lag rises by one month every month until an open release cuts it. Then a closed release opens it up again. Since mid-2024 it has ranged from about 1 month (just after DeepSeek-R1) to about 9 months (January 2026).

![Bar chart of mean horizontal lag by year for ECI and LMArena](/figures/oss_fig18_lag_by_year.webp)
_Figure F5. Mean horizontal lag by year. Blue: ECI, with a line from the yearly minimum to the maximum. Orange: LMArena text arena. 2024 ECI counts only weeks after open models passed GPT-4._

| Year                 | ECI lag (mean) | LMArena lag (mean) |
| -------------------- | -------------- | ------------------ |
| 2024 (ECI from June) | 4.8 mo         | 4.0 mo             |
| 2025                 | 4.9 mo         | 3.4 mo             |
| 2026                 | 6.4 mo         | 6.7 mo             |

Two independent measures agree that 2026 was a slightly worse year for open weights than 2025. A linear fit to the weekly ECI lag since mid-2024 has a slope of +1.3 months per year (R² 0.32). The 2024 arena figure is approximate: a model's "release" there is its first appearance in the dataset, which starts in December 2023.

## 5. The formula

Since 2024, both frontiers rise in close to a straight line on the ECI scale. Fitting only the record-setting models, with t in years since 1 January 2024:

```
Closed frontier:  ECI_c(t) = 122.8 + 17.1·t     (R² 0.99)
Open frontier:    ECI_o(t) = 110.8 + 18.6·t     (R² 0.90)
```

![ECI frontiers with linear trend lines projected to the end of 2027](/figures/oss_fig04_frontier_trends_formula.webp)
_Figure F6. Linear fits to the closed and open record-setters since January 2024, extended through 2027. The dotted orange line is the slower 2025+ open pace, started from today's open level._

With two straight lines, the horizontal lag follows directly:

```
lag(t) = 12 · [(α_c − α_o) + (β_c − β_o)·t] / β_c     months
```

On the 2024+ fit this gives 5.4 months today (90% interval 3.9–6.6). Because β_o is slightly larger than β_c on this window, the lag would shrink by about 1.1 months per year and the lines would cross at the end of 2031.

That conclusion is fragile. It depends on when you start counting:

![Bar charts of frontier slopes and implied lag drift by fit window](/figures/oss_fig06_slope_window_sensitivity.webp)
_Figure F7. Left: frontier pace (ECI points per year) for fits starting at four dates. Right: the implied change in lag per year._

| Fit window starts | Closed β | Open β | Lag drift (months/yr) |
| ----------------- | -------- | ------ | --------------------- |
| Jan 2024          | 17.1     | 18.6   | −1.1 (closing)        |
| Jul 2024          | 18.5     | 16.3   | +1.4 (widening)       |
| Jan 2025          | 18.2     | 13.3   | +3.2 (widening)       |
| Jul 2025          | 18.2     | 14.7   | +2.3 (widening)       |

Only the window that starts in January 2024 shows open weights gaining. It starts while open models were still climbing up to GPT-4's level, and that early catch-up steepens the open line. Every window that starts mid-2024 or later shows the closed frontier pulling away, even though the July 2024 window still contains Llama 3.1-405B and DeepSeek-R1. That matches the anchor regression and the weekly series. Even on the January 2024 window, open is faster than closed in 91% of bootstrap samples, not all of them.

For forecasting I start from where open weights actually are today, not from where the fitted line says they should be:

```
ETA(M) = t_last_open_record + (ECI_M − ECI_open_now) / β_open
       = 23 Oct 2026 + (ECI_M − 161.2) / β_open,   β_open ∈ [13.3, 18.6] ECI/yr
```

I compute ETA with both slopes, add a third estimate (release date + the mean 2025–26 lag of 5.6 months), and report the median of the three. The range runs from the earliest to the latest of these, including the 5th percentile of the fast-slope bootstrap and the 95th percentile of the slow-slope bootstrap.

## 6. When will open weights catch today's flagships?

![Timeline of projected open-weight parity dates for current closed flagships](/figures/oss_fig05_parity_forecasts.webp)
_Figure F8. Projected open-weight parity for each lab's current flagship. Blue dot = closed release. Orange diamond = median of three methods. Shaded bar = range including the 90% bootstrap._

| Closed model          | Lab       | ECI           | Gap now | Projected parity             | Range          |
| --------------------- | --------- | ------------- | ------- | ---------------------------- | -------------- |
| Claude Fable 5.2      | Anthropic | 173.4         | 12.2    | **Jun 2027**                 | Apr – Dec 2027 |
| GPT-6.2 Astra         | OpenAI    | 172.8         | 11.6    | **Jun 2027**                 | Apr – Nov 2027 |
| Gemini 4 Carbon       | Google    | 169.7         | 8.5     | **Apr 2027**                 | Mar – Aug 2027 |
| GPT-6 Astra           | OpenAI    | 169.2         | 8.0     | **Mar 2027**                 | Feb – Jul 2027 |
| Claude Opus 5.5       | Anthropic | 168.7         | 7.5     | **Mar 2027**                 | Feb – Jul 2027 |
| Gemini 4 Hydrogen     | Google    | 166.8         | 5.6     | **Mar 2027**                 | Jan – May 2027 |
| Muse Wonder           | Meta      | 161.7         | 0.5     | statistical tie now          | —              |
| Grok 4.6 / 4.7        | xAI       | 157.8 / 156.4 | —       | matched by Kimi K3, Jul 2026 | —              |
| Qwen 3.8 Max (hosted) | Alibaba   | 157.6         | —       | matched by Kimi K3, Jul 2026 | —              |
| Muse Spark 1.3        | Meta      | 158.2         | —       | matched by Kimi K3, Jul 2026 | —              |

Two caveats matter. First, this forecasts parity with today's models, not with the frontier. If the closed trend holds, the closed frontier will be near ECI 182 by June 2027, still about six months ahead. Second, on the slower 2025+ pace, parity with Fable 5.2 slips to September 2027. Given everything in section 5, I would lean toward the later end of these ranges.

## 7. Who holds the open crown

![ECI frontiers for closed, China-based open and non-China open models, with a timeline of open-weight leaders](/figures/oss_fig07_open_crown_by_country.webp)
_Figure F9. Top: frontiers for closed models, open models from Chinese labs, and open models from everyone else. Bottom: which model held the open-weight ECI record, coloured by the lab's country._

Labs outside China held the open crown for most of 2023 and 2024: Meta's LLaMA and Llama models, Stability's Stable Beluga 2 and Mistral's Mixtral. Alibaba's Qwen2-72B held it briefly in June 2024, and Microsoft's Phi-4 for two weeks in December 2024. Since DeepSeek-V3 at the end of December 2024, every open-weight ECI record has come from a Chinese lab: DeepSeek, Alibaba, Moonshot or Z.ai. The best non-Chinese open model today is Meta's Muse Spark Open at ECI 155.5, about six points behind Kimi K3.1 Pro.

![Open-weight frontiers by license category against the closed frontier](/figures/oss_fig17_license_frontiers.webp)
_Figure F10. Open-weight frontiers split by license: unrestricted (MIT/Apache), restricted use, and non-commercial._

License terms barely matter at the top. The best model under an unrestricted license is DeepSeek V4.1 Flash 1017 at 159.4, only 1.8 points behind Kimi K3.1 Pro, which carries usage restrictions.

## 8. It depends on the task

ECI averages everything. Individual benchmarks tell different stories.

![Small multiples of closed and open frontiers on 16 benchmarks](/figures/oss_fig08_benchmark_small_multiples.webp)
_Figure F11. Closed and open frontiers on 16 benchmarks. The label in each panel is the current horizontal lag._

![Ranked bar chart of current lag on each benchmark](/figures/oss_fig09_lag_by_benchmark.webp)
_Figure F12. Current horizontal lag on each benchmark, measured as of the last date both an open and a closed model were evaluated. Diamonds are the median lag over 2025–26. Grey bars are retired benchmarks with no 2026 results._

| Domain    | Median current lag | Closest          | Furthest               |
| --------- | ------------------ | ---------------- | ---------------------- |
| Agents    | 3.9 mo             | APEX-Agents 1.5  | Terminal-Bench 5.0     |
| Coding    | 3.7 mo             | WebDev Arena 1.9 | ALE-Bench 6.0          |
| Math      | 6.1 mo             | ProofBench 4.5   | FrontierMath T1-3 7.6  |
| Science   | 7.8 mo             | HLE 5.7          | GPQA Diamond 8.3       |
| Reasoning | 8.7 mo             | LMCA 4.5         | ForecastBench 16.6     |
| Knowledge | 10.4 mo            | —                | SimpleQA Verified 10.4 |

Knowledge has only one live benchmark (SimpleQA Verified), so treat that row as a single data point. My guess at the pattern, which the data does not test: agent and coding tasks have clear reward signals and are where open labs have put a lot of post-training effort, while factual recall depends more on pretraining scale, where closed labs spend more compute.

![Heatmap of horizontal lag by benchmark and half-year](/figures/oss_fig10_lag_heatmap.webp)
_Figure F13. Mean horizontal lag by benchmark and half-year. Blank cells are periods when the benchmark had not been run on both sides._

![Median lag across benchmarks over time with interquartile band and the ECI lag overlaid](/figures/oss_fig11_cross_benchmark_consensus.webp)
_Figure F14. Median horizontal lag across all benchmarks with results that month (at least 5), with the interquartile range. The ECI lag is overlaid._

No benchmark shows a steady march to zero. The cross-benchmark median rose from about 2–4 months in late 2024 to 6–8 months in 2026, matching the ECI result.

## 9. What human raters say

LMArena is a different kind of measurement: blind head-to-head votes from users. Each snapshot is its own Elo scale, so I compare the best closed and best open model within each snapshot.

![Best closed and best open Arena Elo over time and the Elo gap](/figures/oss_fig12_lmarena_gap.webp)
_Figure F15. Top: best closed and best open-weight Elo on the LMArena text leaderboard, December 2023 to November 2026. Bottom: the Elo gap, labelled with the head-to-head win rate it implies. Green: the WebDev arena._

In votes, the gap is small. Today it is 46 Elo (Gemini 4 Carbon vs MiMo-V2.6-Pro), which implies the closed model wins about 57% of head-to-head votes. The mean gap was 67 Elo in 2024, 34 in 2025 and 40 in 2026. Open weights led outright from late January to the end of February 2025, after DeepSeek-R1. The WebDev arena tells a harsher story: a 139-point gap today, with Claude Fable 5.2 well ahead of Kimi K3.1 Pro.

![Open-weight share of the arena top 10 and top 25, and rank of the best open model](/figures/oss_fig13_lmarena_share_and_rank.webp)
_Figure F16. Left: share of open-weight models in the arena top 10 and top 25 (60-day mean), from March 2024. Right: overall rank of the best open model._

The share view is more striking. In late 2025, open-weight models made up as much as 38% of the top 10. In the latest snapshot there are none, and the best open model ranks #14. Part of that is bookkeeping: closed labs now list several reasoning-effort variants of each model. Counting each closed model once, the best open model still ranks #12.

## 10. Today's snapshot: price and evals

![Artificial Analysis Intelligence Index against blended price for open and closed models](/figures/oss_fig14_aa_price_vs_intelligence.webp)
_Figure F17. Artificial Analysis Intelligence Index v5.0.1 against blended price ($ per 1M tokens, 3:1 input:output). Step lines show the best score available at or below each price._

Artificial Analysis only gives me today, but it adds price. Its Intelligence Index v5.0.1 includes several evals built on private datasets. The best closed configuration, Claude Fable 5.2 (Max), scores 64.6. The best open model, Kimi K3.1 Pro, scores 46.5, and 31 closed configurations score higher. At or below $1 per million tokens the two are close: the best closed option scores 36.5 and the best open option 32.6. Above that price, closed models pull far ahead.

![Per-eval ratio of best open score to best closed score](/figures/oss_fig14b_aa_per_eval_ratio.webp)
_Figure F18. Best open-weight score as a percentage of the best closed score on each Artificial Analysis eval._

Open weights match or beat closed on 8 of 35 evals, mostly tool use, terminal tasks and instruction following. They are within 1% on GPQA Diamond and AIME 2025. The large gaps are on HLE Diamond (47%), Terminal-Bench Science (44%) and Harvey's legal eval (4%).

## 11. Compute

![ECI against estimated training compute for open and closed models](/figures/oss_fig15_compute_efficiency.webp)
_Figure F19. ECI against estimated training compute, for models with ECI ≥ 95 and a public compute estimate. Dashed lines are log-linear fits._

Open weights do more with less. Kimi K3.1 Pro reaches ECI 161.2 on an estimated 2.0×10²⁵ FLOP. GPT-5 reached 150 on 6.6×10²⁵, and GPT-6 Astra 169.2 on 9.4×10²⁶, about 47 times Kimi's compute. On the log-linear fits, open models reach the same ECI with roughly 10–25 times less training compute. Only 12 closed models have public compute estimates, so this is indicative, not precise. Whether that efficiency is why the gap stays at months rather than years is a reasonable guess, but nothing here tests it.

## 12. Limits

- **Benchmark coverage is uneven.** Closed flagships get evaluated faster and more often than open models. Some per-benchmark lags are measured as of an older date (for example SWE-bench Verified as of May 2026 and Terminal-Bench as of April 2026).
- **ECI before mid-2024 is incomplete.** It has no closed model older than GPT-4, so open-weight lags from 2023 to June 2024 are lower bounds only.
- **Point estimates vs statistical ties.** I use strict point estimates for parity. If a match counts when the open model's upper interval reaches the closed score, the median lag since 2024 drops from 6.8 to 4.4 months.
- **The arena dataset has gaps.** The Hugging Face snapshots have no GPT-4 before December 2023 and no Claude before March 2024. Elo gaps are comparable within a snapshot, not across snapshots.
- **Artificial Analysis is a single snapshot** and lists several reasoning-effort settings per model, which inflates the closed count at the top.
- **Straight lines are an assumption.** A single DeepSeek-R1-style jump would move the forecasts by months. The window sensitivity in Figure F7 is the honest error bar.
- **I did not test for benchmark contamination.** If open models have seen public test sets during training, their public-benchmark scores flatter them, and the true lag would be larger than reported here.

## Appendix

- **Data:** Epoch AI Capabilities Index and Benchmarking Hub (CC-BY 4.0), `lmarena-ai/leaderboard-dataset` on Hugging Face, and the artificialanalysis.ai leaderboard page. All were retrieved 23 November 2026.
- **Pipeline:** `01_build_data.py` (tidy tables), `02_analysis.py` (lags, bootstrap, fits, forecasts), `03_figures.py` (figures plus an automatic text-collision check).
- **Key outputs:** `summary.json` (all fitted parameters), `eci_anchor_lags.csv`, `eci_parity_forecasts.csv`, `benchmark_lag_summary.csv`, `lmarena_gap_by_snapshot.csv`, `eci_slope_window_sensitivity.csv`.

The code, processed data and every figure are in the accompanying bundle.
