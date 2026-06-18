---
type: paper
title: >-
  Quantifying Hyperparameter Transfer And The Importance Of Embedding Layer
  Learni
---

## Overview
This paper addresses the problem of hyperparameter transfer in large language models, which is crucial for training these models efficiently. Hyperparameter transfer allows extrapolating optimal optimization hyperparameters from small to large scales, reducing the need for expensive hyperparameter searches at scale. The paper proposes a framework to quantify hyperparameter transfer and investigates the importance of embedding layer learning rate in this process.

## Method
The core approach proposed in this paper is to develop a framework to quantify hyperparameter transfer through three metrics: the quality of the scaling law fit, the robustness to extrapolation errors, and the asymptotic loss penalty due to choice of parameterization. The authors also investigate the importance of embedding layer learning rate by comparing Maximal Update Parameterization (µP) with standard parameterization (SP) and examining all 16 ablations that distinguish µP from SP.

## Key Results
* The embedding layer learning rate is the primary factor in achieving high-quality hyperparameter transfer, with µP having a much larger embedding layer learning rate compared to SP.
* Increasing the embedding layer learning rate in SP by a factor of width to match µP dramatically smooths out training and improves hyperparameter transfer.
* Weight decay improves the scaling law fit quality, but hurts the robustness of the extrapolation in the fixed token-per-parameter setting.
* The authors develop three metrics to quantify hyperparameter transfer: the quality of the scaling law fit (error E), a transfer robustness exponent (κ), and the asymptotic loss degradation (R(∞)).

## Why It Matters
The findings of this paper have practical significance, as they can help improve the efficiency of training large language models by reducing the need for expensive hyperparameter searches at scale. The importance of embedding layer learning rate can also inform the design of more effective hyperparameter tuning strategies.

## Limitations
The authors acknowledge that the theoretical derivation of µP and its variants make several assumptions that do not hold in practice, such as assuming a finite number of training steps in the infinite width limit. The paper also notes that the results are specific to the AdamW optimizer and may not generalize to other optimizers.

## Keywords
Hyperparameter transfer, large language models, Maximal Update Parameterization, embedding layer learning rate, scaling law, robustness, asymptotic loss degradation, weight decay, AdamW optimizer, neural network parameterization.

## Authors

- [[people/dayal-singh-kalra|Dayal Singh Kalra]] — [[companies/university-of-maryland-college-park|University of Maryland, College Park]]
- [[people/maissam-barkeshli|Maissam Barkeshli]] — [[companies/university-of-maryland-college-park|University of Maryland, College Park]]

**Year:** 2026 · **Domain:** computer science


## Research Context

**What's new:** This paper contributes a framework to quantify hyperparameter transfer in large language models, focusing on the importance of embedding layer learning rate. The key novel element is the proposal of a set of metrics to evaluate hyperparameter transfer, including the quality of the scaling law fit and the robustness to extrapolation errors.

**Related in brain:** There are no related pages in the brain that overlap with this paper.

**Knowledge gaps:** This paper assumes a specific optimizer (AdamW) and makes theoretical derivations that may not hold in practice, which are not covered in the brain. To fully evaluate this work, one would need to learn about the theoretical foundations of hyperparameter transfer and the limitations of the proposed framework.

**Explore next:** 
* Theoretical foundations of hyperparameter transfer in large language models
* Comparison of different optimizers for hyperparameter transfer
* Applications of the proposed framework to other machine learning models beyond language models

*Generated 2026-05-22 by research-notes.py*

<!-- timeline -->

## Timeline

- **2026-05-21** ? Imported to GBrain and summarized