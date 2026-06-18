# New Paper Imported — An Agency Transferring Model Free Policy Enhancement Technique

*Imported: 2026-06-09 12:00*

## Summary

## Overview
The proposed method addresses the problem of training reinforcement learning (RL) policies from scratch, which can be costly and time-consuming. It leverages a pre-existing baseline policy to improve training efficiency and produce a policy that outperforms the baseline. This approach is particularly useful in control problems where a functional but suboptimal policy is already available.

## Method
The core approach involves embedding the baseline policy into the RL training process using an arbitration module that governs two policies: the learning policy and the baseline policy. The arbitration module determines whether the executed action is supplied by the learning policy or the baseline policy, initially favoring the baseline policy and gradually transferring agency to the learning policy.

## Key Results
* The proposed method achieves returns that match or exceed those of competitive approaches, including SAC, PPO, and TD3, on continuous-control benchmarks.
* The method maintains the highest goal-reaching rates throughout training, including in the final stage where the learning policy operates without any baseline support.
* The approach yields a standalone neural network that operates without baseline policy support, with explicit lower bounds derived for the goal-reaching probability.
* Empirical results show that the proposed method outperforms residual reinforcement learning (residual RL) in terms of goal-reaching rates and returns.
* The method demonstrates improved training efficiency compared to vanilla from-scratch methods, such as SAC, PPO, and TD3.

## Why It Matters
The proposed method has practical significance as it can improve the efficiency and effectiveness of RL training in various applications, such as robotics, logistics, and finance, where a functional but suboptimal policy is already available. The approach can also lead to better performance and faster training times, making RL more accessible and useful in real-world scenarios.

## Limitations
The authors acknowledge that the proposed method relies on the quality of the baseline policy and the design of the arbitration module, which can be challenging to optimize. Additionally, the method may not be suitable for all types of RL problems, particularly those where a good baseline policy is not available.

## Keywords
Reinforcement learning, policy arbitration, policy switching, continuous-control benchmarks, SAC, PPO, TD3, residual reinforcement learning, neural networks, goal-reaching rates, training efficiency.

---
*gbrain slug: `an_agency_transferring_model_free_policy_enhancement_technique`*
