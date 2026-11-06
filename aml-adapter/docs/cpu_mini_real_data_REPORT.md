# AML adapter benchmark (cpu-mini profile)

> **cpu-mini run: pipeline check only. These numbers are not a result.**

Primary metrics: T1 AUROC (van Galen, patient-held-out), T2 AUROC (Naldini NPM1 genotype, trained on van Galen only), T3 macro-F1 (van Galen cell states). 95% CIs resample patients.

## T1_AUROC

| variant        |   estimate |   ci_lo |   ci_hi |   diff_vs_scGPT-frozen |   diff_lo_vs_scGPT-frozen |   diff_hi_vs_scGPT-frozen |
|:---------------|-----------:|--------:|--------:|-----------------------:|--------------------------:|--------------------------:|
| HVG-LR         |      0.93  |   0.897 |   0.959 |                  0.047 |                     0.019 |                     0.091 |
| PCA-LR         |      0.934 |   0.885 |   0.967 |                  0.05  |                     0.026 |                     0.09  |
| scGPT-frozen   |      0.884 |   0.814 |   0.927 |                  0     |                     0     |                     0     |
| scGPT+SSL      |      0.874 |   0.799 |   0.916 |                 -0.01  |                    -0.019 |                    -0.001 |
| scGPT+task     |      0.856 |   0.765 |   0.905 |                 -0.027 |                    -0.061 |                     0     |
| scGPT+SSL+task |      0.849 |   0.714 |   0.911 |                 -0.035 |                    -0.1   |                    -0.002 |

## T1_AUROC_post

| variant        |   estimate |   ci_lo |   ci_hi |   diff_vs_scGPT-frozen |   diff_lo_vs_scGPT-frozen |   diff_hi_vs_scGPT-frozen |
|:---------------|-----------:|--------:|--------:|-----------------------:|--------------------------:|--------------------------:|
| HVG-LR         |      0.929 |   0.867 |   0.964 |                 -0.01  |                    -0.027 |                     0.039 |
| PCA-LR         |      0.943 |   0.86  |   0.971 |                  0.004 |                    -0.007 |                     0.041 |
| scGPT-frozen   |      0.94  |   0.835 |   0.968 |                  0     |                     0     |                     0     |
| scGPT+SSL      |      0.93  |   0.802 |   0.966 |                 -0.009 |                    -0.049 |                     0.001 |
| scGPT+task     |      0.917 |   0.841 |   0.956 |                 -0.023 |                    -0.046 |                     0.018 |
| scGPT+SSL+task |      0.935 |   0.875 |   0.971 |                 -0.005 |                    -0.022 |                     0.039 |

## T1_balanced_acc

| variant        |   estimate |
|:---------------|-----------:|
| HVG-LR         |      0.791 |
| PCA-LR         |      0.83  |
| scGPT+SSL      |      0.762 |
| scGPT+SSL+task |      0.779 |
| scGPT+task     |      0.777 |
| scGPT-frozen   |      0.785 |

## T3_macroF1

| variant        |   estimate |   ci_lo |   ci_hi |   diff_vs_scGPT-frozen |   diff_lo_vs_scGPT-frozen |   diff_hi_vs_scGPT-frozen |
|:---------------|-----------:|--------:|--------:|-----------------------:|--------------------------:|--------------------------:|
| HVG-LR         |      0.461 |   0.425 |   0.487 |                 -0.02  |                    -0.05  |                     0.018 |
| PCA-LR         |      0.542 |   0.482 |   0.582 |                  0.061 |                     0.029 |                     0.104 |
| scGPT-frozen   |      0.481 |   0.445 |   0.5   |                  0     |                     0     |                     0     |
| scGPT+SSL      |      0.49  |   0.451 |   0.513 |                  0.009 |                    -0.003 |                     0.027 |
| scGPT+task     |      0.342 |   0.311 |   0.362 |                 -0.138 |                    -0.172 |                    -0.1   |
| scGPT+SSL+task |      0.362 |   0.32  |   0.383 |                 -0.119 |                    -0.155 |                    -0.074 |

## T3_macroF1_malignant_states

| variant        |   estimate |   ci_lo |   ci_hi |   diff_vs_scGPT-frozen |   diff_lo_vs_scGPT-frozen |   diff_hi_vs_scGPT-frozen |
|:---------------|-----------:|--------:|--------:|-----------------------:|--------------------------:|--------------------------:|
| HVG-LR         |      0.27  |   0.205 |   0.33  |                 -0.086 |                    -0.149 |                    -0.011 |
| PCA-LR         |      0.439 |   0.322 |   0.541 |                  0.082 |                    -0.008 |                     0.166 |
| scGPT-frozen   |      0.357 |   0.28  |   0.415 |                  0     |                     0     |                     0     |
| scGPT+SSL      |      0.374 |   0.292 |   0.443 |                  0.017 |                    -0.007 |                     0.047 |
| scGPT+task     |      0.173 |   0.112 |   0.239 |                 -0.184 |                    -0.25  |                    -0.099 |
| scGPT+SSL+task |      0.181 |   0.112 |   0.252 |                 -0.176 |                    -0.274 |                    -0.056 |

## T3_per_class_F1

| celltype     |   HVG-LR |   PCA-LR |   scGPT+SSL |   scGPT+SSL+task |   scGPT+task |   scGPT-frozen |
|:-------------|---------:|---------:|------------:|-----------------:|-------------:|---------------:|
| CTL          |    0.351 |    0.424 |       0.535 |            0.066 |        0.03  |          0.52  |
| GMP          |    0.495 |    0.505 |       0.328 |            0.272 |        0.182 |          0.265 |
| GMP-like     |    0.353 |    0.303 |       0.377 |            0.241 |        0.218 |          0.345 |
| HSC          |    0.326 |    0.552 |       0.529 |            0.198 |        0.234 |          0.498 |
| HSC-like     |    0.145 |    0.364 |       0.207 |            0     |        0.062 |          0.248 |
| Mono         |    0.697 |    0.747 |       0.56  |            0.677 |        0.648 |          0.551 |
| Mono-like    |    0.1   |    0.472 |       0.278 |            0.075 |        0.019 |          0.248 |
| NK           |    0.776 |    0.523 |       0.726 |            0.649 |        0.6   |          0.733 |
| Plasma       |    0.938 |    0.907 |       0.927 |            0.911 |        0.831 |          0.938 |
| ProMono      |    0.496 |    0.514 |       0.453 |            0.471 |        0.379 |          0.455 |
| ProMono-like |    0.045 |    0.302 |       0.226 |            0.043 |        0.163 |          0.149 |
| Prog         |    0.304 |    0.396 |       0.364 |            0.214 |        0.341 |          0.339 |
| Prog-like    |    0.461 |    0.491 |       0.416 |            0.191 |        0.22  |          0.473 |
| T            |    0.919 |    0.919 |       0.914 |            0.886 |        0.874 |          0.902 |
| cDC          |    0.243 |    0.528 |       0.354 |            0.303 |        0.292 |          0.375 |
| cDC-like     |    0.29  |    0.355 |       0.31  |            0.282 |        0.08  |          0.276 |
| earlyEry     |    0.472 |    0.532 |       0.43  |            0.171 |        0.156 |          0.438 |
| lateEry      |    0.876 |    0.919 |       0.884 |            0.864 |        0.835 |          0.897 |

## T2_AUROC

| variant        |   estimate |   ci_lo |   ci_hi |   diff_vs_scGPT-frozen |   diff_lo_vs_scGPT-frozen |   diff_hi_vs_scGPT-frozen |
|:---------------|-----------:|--------:|--------:|-----------------------:|--------------------------:|--------------------------:|
| HVG-LR         |      0.809 |   0.702 |   0.922 |                  0.101 |                     0.033 |                     0.186 |
| PCA-LR         |      0.811 |   0.709 |   0.914 |                  0.103 |                     0.043 |                     0.196 |
| scGPT-frozen   |      0.708 |   0.587 |   0.838 |                  0     |                     0     |                     0     |
| scGPT+SSL      |      0.713 |   0.576 |   0.839 |                  0.005 |                    -0.017 |                     0.03  |
| scGPT+task     |      0.683 |   0.566 |   0.83  |                 -0.025 |                    -0.07  |                     0.022 |
| scGPT+SSL+task |      0.695 |   0.56  |   0.849 |                 -0.013 |                    -0.062 |                     0.038 |

## T2_AUROC_post

| variant        |   estimate |   ci_lo |   ci_hi |   diff_vs_scGPT-frozen |   diff_lo_vs_scGPT-frozen |   diff_hi_vs_scGPT-frozen |
|:---------------|-----------:|--------:|--------:|-----------------------:|--------------------------:|--------------------------:|
| HVG-LR         |      0.645 |   0.511 |   0.871 |                  0.055 |                    -0.021 |                     0.125 |
| PCA-LR         |      0.642 |   0.477 |   0.858 |                  0.052 |                    -0.031 |                     0.155 |
| scGPT-frozen   |      0.591 |   0.448 |   0.831 |                  0     |                     0     |                     0     |
| scGPT+SSL      |      0.595 |   0.442 |   0.833 |                  0.004 |                    -0.022 |                     0.049 |
| scGPT+task     |      0.578 |   0.441 |   0.787 |                 -0.013 |                    -0.083 |                     0.056 |
| scGPT+SSL+task |      0.581 |   0.451 |   0.777 |                 -0.01  |                    -0.075 |                     0.056 |

## T2_FPR_at_TPR90

| variant        |   estimate |   ci_lo |   ci_hi |   diff_vs_scGPT-frozen |   diff_lo_vs_scGPT-frozen |   diff_hi_vs_scGPT-frozen |
|:---------------|-----------:|--------:|--------:|-----------------------:|--------------------------:|--------------------------:|
| HVG-LR         |      0.735 |   0.243 |   0.894 |                  0.071 |                    -0.153 |                     0.145 |
| PCA-LR         |      0.725 |   0.23  |   0.884 |                  0.061 |                    -0.198 |                     0.096 |
| scGPT-frozen   |      0.664 |   0.369 |   0.887 |                  0     |                     0     |                     0     |
| scGPT+SSL      |      0.624 |   0.33  |   0.887 |                 -0.04  |                    -0.084 |                     0.043 |
| scGPT+task     |      0.707 |   0.396 |   0.913 |                  0.043 |                    -0     |                     0.111 |
| scGPT+SSL+task |      0.694 |   0.357 |   0.898 |                  0.03  |                    -0.021 |                     0.086 |

## T2_FPR_at_TPR90_post

| variant        |   estimate |   ci_lo |   ci_hi |   diff_vs_scGPT-frozen |   diff_lo_vs_scGPT-frozen |   diff_hi_vs_scGPT-frozen |
|:---------------|-----------:|--------:|--------:|-----------------------:|--------------------------:|--------------------------:|
| HVG-LR         |      0.795 |   0.522 |   0.9   |                 -0.028 |                    -0.066 |                     0.21  |
| PCA-LR         |      0.82  |   0.452 |   0.943 |                 -0.003 |                    -0.082 |                     0.162 |
| scGPT-frozen   |      0.823 |   0.398 |   0.938 |                  0     |                     0     |                     0     |
| scGPT+SSL      |      0.857 |   0.33  |   0.979 |                  0.034 |                    -0.088 |                     0.055 |
| scGPT+task     |      0.882 |   0.454 |   0.987 |                  0.059 |                    -0.008 |                     0.162 |
| scGPT+SSL+task |      0.901 |   0.468 |   0.982 |                  0.078 |                    -0.05  |                     0.142 |

## T2_counts

| stage   |   malignant |   cells |
|:--------|------------:|--------:|
| dx      |           0 |      68 |
| dx      |           1 |     452 |
| post    |           0 |     322 |
| post    |           1 |     172 |
| relapse |           0 |       6 |
| relapse |           1 |     154 |

## PROMISE

| task       | variant        |   estimate |   vs_frozen |   vs_frozen_lo | best_conventional   |   vs_conv |   vs_conv_lo | promise   |
|:-----------|:---------------|-----------:|------------:|---------------:|:--------------------|----------:|-------------:|:----------|
| T1_AUROC   | scGPT+SSL      |      0.874 |      -0.01  |         -0.019 | PCA-LR              |    -0.06  |       -0.101 | False     |
| T1_AUROC   | scGPT+task     |      0.856 |      -0.027 |         -0.061 | PCA-LR              |    -0.077 |       -0.139 | False     |
| T1_AUROC   | scGPT+SSL+task |      0.849 |      -0.035 |         -0.1   | PCA-LR              |    -0.085 |       -0.177 | False     |
| T2_AUROC   | scGPT+SSL      |      0.713 |       0.005 |         -0.017 | PCA-LR              |    -0.098 |       -0.185 | False     |
| T2_AUROC   | scGPT+task     |      0.683 |      -0.025 |         -0.07  | PCA-LR              |    -0.128 |       -0.211 | False     |
| T2_AUROC   | scGPT+SSL+task |      0.695 |      -0.013 |         -0.062 | PCA-LR              |    -0.116 |       -0.223 | False     |
| T3_macroF1 | scGPT+SSL      |      0.49  |       0.009 |         -0.003 | PCA-LR              |    -0.052 |       -0.089 | False     |
| T3_macroF1 | scGPT+task     |      0.342 |      -0.138 |         -0.172 | PCA-LR              |    -0.2   |       -0.252 | False     |
| T3_macroF1 | scGPT+SSL+task |      0.362 |      -0.119 |         -0.155 | PCA-LR              |    -0.18  |       -0.238 | False     |

## Training logs (SSL held-out masked loss should fall)

```
{
 "ssl_fold0": {
  "label": "ssl_fold0",
  "heldout_loss_before": 443.230224609375,
  "heldout_loss_after": 321.6386980329241,
  "minutes": 2.1082942962646483
 },
 "scGPT+task_fold0": {
  "label": "scGPT+task_fold0",
  "minutes": 2.690920579433441
 },
 "scGPT+SSL+task_fold0": {
  "label": "scGPT+SSL+task_fold0",
  "minutes": 2.6241463899612425
 },
 "ssl_fold1": {
  "label": "ssl_fold1",
  "heldout_loss_before": 442.7879115513393,
  "heldout_loss_after": 321.52662440708707,
  "minutes": 2.038973069190979
 },
 "scGPT+task_fold1": {
  "label": "scGPT+task_fold1",
  "minutes": 2.5439802249272665
 },
 "scGPT+SSL+task_fold1": {
  "label": "scGPT+SSL+task_fold1",
  "minutes": 2.5816572427749636
 },
 "ssl_fold2": {
  "label": "ssl_fold2",
  "heldout_loss_before": 433.6950901576451,
  "heldout_loss_after": 321.4200875418527,
  "minutes": 2.064404245217641
 },
 "scGPT+task_fold2": {
  "label": "scGPT+task_fold2",
  "minutes": 2.6575613300005596
 },
 "scGPT+SSL+task_fold2": {
  "label": "scGPT+SSL+task_fold2",
  "minutes": 2.5828385233879088
 },
 "ssl_all": {
  "label": "ssl_all",
  "heldout_loss_before": 433.4119873046875,
  "heldout_loss_after": 315.6445617675781,
  "minutes": 1.9848957101504008
 },
 "scGPT+task_all": {
  "label": "scGPT+task_all",
  "minutes": 2.5495298425356547
 },
 "scGPT+SSL+task_all": {
  "label": "scGPT+SSL+task_all",
  "minutes": 2.596031991640727
 }
}
```
