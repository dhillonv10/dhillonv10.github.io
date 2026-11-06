"""AML adapter for single-cell foundation models (scGPT backbone).

Modules
-------
data       : download + load van Galen 2019 (GSE116256) and Naldini 2023 (GSE185991) into AnnData
backbone   : scGPT loading, tokenisation, cell embedding
adapters   : bottleneck adapters injected into a frozen scGPT (zero-init => identical to base at start)
train      : self-supervised AML adaptation (masked expression) and supervised task adapters
baselines  : HVG / PCA logistic-regression baselines
benchmark  : task definitions T1-T3, metrics, patient-level bootstrap, report
"""
__version__ = "0.1.0"
