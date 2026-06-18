---
title: "Vector Policy Optimization Training For Diversity Improves Test Time Search"
type: paper
aliases:
  - "vector policy optimization diversity"
  - "VPO diversity test time search"
---

## Overview
The paper addresses the problem of training language models to produce diverse solutions for downstream search procedures, which is crucial for tasks that require exploration and exploitation. The proposed approach, Vector Policy Optimization (VPO), aims to improve test-time search performance by training models to anticipate diverse reward functions and produce diverse solutions. This is important because standard post-training methods often lead to low-entropy response distributions, making it difficult for search procedures to find optimal solutions.

## Method
The core approach proposed is Vector Policy Optimization (VPO), which combines multi-answer generation with stochastic reward scalarizations to train models to produce sets of candidates that span the Pareto frontier of possible solutions. VPO exploits the fact that rewards can be naturally decomposed into a vector of components, providing a natural axis for diversity.

## Key Results
* VPO matches or beats the strongest scalar baselines on test-time best@k across four benchmarks, with the gap widening as the candidate budget grows.
* On LiveCodeBench, a VPO-trained model improves both pass@k and best@k over a matched-compute GRPO checkpoint.
* VPO unlocks problems that GRPO cannot solve at any candidate budget inside the OpenEvolve search loop.
* VPO-trained models outperform GRPO models on multi-hop question answering, logic reasoning, navigation, tool use, and coding tasks.

## Why It Matters
The proposed approach has practical significance because it can improve the performance of language models in tasks that require exploration and exploitation, such as test-time search. By training models to produce diverse solutions, VPO can unlock problems that cannot be solved by standard post-training methods.

## Limitations
The authors acknowledge that the proposed approach may have limitations, such as the need for careful tuning of hyperparameters and the potential for increased computational cost due to the generation of multiple candidates.

## Keywords
Reinforcement learning, language models, test-time search, Vector Policy Optimization, diversity, Pareto frontier, multi-answer generation, stochastic reward scalarizations, exploration, exploitation.

## Authors

- [[people/ryan-bahlous-boldi|Ryan Bahlous-Boldi]] — [[companies/mit|MIT]]
- [[people/isha-puri|Isha Puri]] — [[companies/mit|MIT]]
- [[people/idan-shenfeld|Idan Shenfeld]] — [[companies/mit|MIT]]
- [[people/akarsh-kumar|Akarsh Kumar]] — [[companies/mit|MIT]]
- [[people/mehul-damani|Mehul Damani]] — [[companies/mit|MIT]]
- [[people/sebastian-risi|Sebastian Risi]] — [[companies/sakana-ai|Sakana AI]]
- [[people/omar-khattab|Omar Khattab]] — [[companies/mit|MIT]]
- [[people/zhang-wei-hong|Zhang-Wei Hong]] — [[companies/mit|MIT]]
- [[people/pulkit-agrawal|Pulkit Agrawal]] — [[companies/mit|MIT]]

**Year:** 2026 · **Domain:** computer science


## Research Context

**What's new:** This paper contributes a novel approach called Vector Policy Optimization (VPO) that improves test-time search performance by training models to produce diverse solutions. The key novel element is the combination of multi-answer generation with stochastic reward scalarizations to train models to anticipate diverse reward functions.

**Related in brain:** 
* None, as no related pages were found in the brain.

**Knowledge gaps:** This paper assumes a certain level of understanding of language models and reinforcement learning, which may not be fully covered in the brain. To fully evaluate this work, one would need to learn about the current state of language models and their applications in search procedures.

**Explore next:** 
* The application of VPO in other areas beyond language models, such as recommender systems or game playing
* The comparison of VPO with other diversity-promoting methods in reinforcement learning
* The potential of VPO to improve performance in multi-objective optimization problems

*Generated 2026-05-22 by research-notes.py*

<!-- timeline -->

## Timeline

- **2026-05-22** — Imported to GBrain and summarized
