# New Paper Imported — Vector Policy Optimization Training For Diversity Improves Test Time Search

*Imported: 2026-05-22 14:14*

## Summary

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

---
*gbrain slug: `vector_policy_optimization_training_for_diversity_improves_test_time_search`*
