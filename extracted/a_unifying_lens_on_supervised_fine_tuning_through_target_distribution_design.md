---
title: "A Unifying Lens On Supervised Fine Tuning Through Target Distribution Design"
type: paper
---

## Overview
Supervised fine-tuning (SFT) is a crucial stage in post-training large language models, but its standard approach can be suboptimal due to noisy or non-unique observed tokens. This paper proposes a new perspective on SFT, focusing on target distribution design to address these limitations. By reinterpreting SFT as target distribution design, the authors aim to improve the fine-tuning process and provide a more fundamental design principle for SFT training.

## Method
The authors introduce the Q-target framework, which decomposes SFT supervision into two explicit choices: how strongly to rely on the observed token and how to allocate the remaining probability mass over alternatives. This framework is based on the Q-target distribution, defined as Qt = γtδyt + (1−γt)˜πt, where γt controls the target probability assigned to the observed token and ˜πt specifies the plausible alternatives.

## Key Results
* The Q-target framework unifies many existing SFT variants as implicit choices of the target distribution Q.
* TARGET-SFT, a method based on the Q-target framework, consistently outperforms across 10 dataset-model settings.
* The Q-target perspective provides a unifying lens in SFT objective design, exposing a general design space for balancing dataset imitation, prior preservation, and alternative supervision.
* The authors empirically validate the performance of TARGET-SFT, demonstrating its effectiveness in improving SFT.
* The Q-target framework can be used to understand and improve existing SFT variants, such as token-level reweighting and distribution-level prior methods.

## Why It Matters
The proposed Q-target framework and TARGET-SFT method have practical significance, as they can improve the fine-tuning process of large language models and provide a more fundamental design principle for SFT training. This can lead to better performance and more efficient training of language models.

## Limitations
The authors acknowledge that their work focuses on the objective level and does not address dataset-level curations, which can also improve SFT by changing the training trajectories. Additionally, the Q-target framework and TARGET-SFT method may have limitations in certain scenarios, such as when the observed token is highly uncertain or when the model prior is not well-defined.

## Keywords
Supervised fine-tuning, target distribution design, Q-target framework, language models, post-training, token-level reweighting, distribution-level prior, dataset imitation, prior preservation, alternative supervision.

## Authors

- [[people/tong-xie|Tong Xie]] — [[companies/university-of-california-los-angeles-ucla|University of California, Los Angeles (UCLA)]]
- [[people/yuanhao-ban|Yuanhao Ban]] — [[companies/university-of-california-los-angeles-ucla|University of California, Los Angeles (UCLA)]]
- [[people/yunqi-hong|Yunqi Hong]] — [[companies/university-of-california-los-angeles-ucla|University of California, Los Angeles (UCLA)]]
- [[people/sohyun-an|Sohyun An]] — [[companies/university-of-california-los-angeles-ucla|University of California, Los Angeles (UCLA)]]
- [[people/yihang-chen|Yihang Chen]] — [[companies/university-of-california-los-angeles-ucla|University of California, Los Angeles (UCLA)]]
- [[people/cho-jui-hsieh|Cho-Jui Hsieh]] — [[companies/university-of-california-los-angeles-ucla|University of California, Los Angeles (UCLA)]]

**Year:** 2026 · **Domain:** computer science


## Research Context

**What's new:** This paper introduces a new perspective on supervised fine-tuning (SFT) through target distribution design, proposing the Q-target framework as a unifying lens for SFT objective design. The key novel element is the reinterpretation of SFT as target distribution design, which improves the fine-tuning process of large language models.

**Related in brain:** 
* No related pages are found in the brain, indicating that this paper covers new ground not previously addressed.

**Knowledge gaps:** This paper assumes a certain level of understanding of large language models and SFT, which may not be fully covered in the brain. To fully evaluate this work, one would need to learn about the current state of SFT and its limitations.

**Explore next:** 
* The application of the Q-target framework to other areas of natural language processing
* The comparison of TARGET-SFT with other SFT methods in various dataset-model settings
* The potential limitations and extensions of the Q-target framework in scenarios with uncertain observed tokens or poorly defined model priors

*Generated 2026-06-10 by research-notes.py*

<!-- timeline -->

## Timeline

- **2026-06-10** — Imported to GBrain and summarized
