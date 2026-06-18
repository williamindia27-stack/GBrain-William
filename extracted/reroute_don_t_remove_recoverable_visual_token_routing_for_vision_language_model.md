---
title: "Reroute, Don'T Remove Recoverable Visual Token Routing For Vision Language Model"
type: paper
---

## Overview
Vision-language models (VLMs) project images into hundreds to thousands of tokens, making decoder inference expensive. Existing visual-token reduction methods follow a "rank-and-remove" paradigm, which can be fragile as token importance changes across decoder depth. This paper proposes a recoverable routing approach to replace irreversible removal, improving grounding accuracy under aggressive token reduction.

## Method
The proposed method, Reroute, replaces removal with recoverable routing, where selected vision tokens pass through decoder blocks, while deferred tokens bypass the stage and re-enter the candidate pool at the next routing decision. Reroute reuses existing attention-score ranking rules and stage-wise schedules, preserving the theoretical TFLOPs and KV-cache budget class of the pruning method it augments.

## Key Results
* Reroute improves grounding under 88.9% token reduction, with IoU increasing from 0.38 to 0.80 on LLaV A-1.5-7B, from 0.21 to 0.88 on Qwen2.5-VL-7B, and from 0.22 to 0.72 on Qwen3.5-9B.
* Reroute preserves general VQA performance while improving grounding accuracy.
* Reroute is a training-free plug-in that can be applied to various pruning methods, including FastV, PDrop, and Nüwa.

## Why It Matters
Reroute's recoverable routing approach improves grounding accuracy under aggressive token reduction, making it a significant contribution to the development of efficient and effective VLMs. This approach can be applied to various VLM architectures, enabling more accurate and efficient vision-language understanding.

## Limitations
The authors acknowledge that Reroute may not be suitable for all types of VLMs or pruning methods, and further research is needed to explore its applicability and limitations. Additionally, Reroute's performance may vary depending on the specific use case and dataset.

## Keywords
Vision-language models, token reduction, recoverable routing, attention mechanisms, mixture-of-depth, conditional computation, pruning methods, FastV, PDrop, Nüwa, LLaV, Qwen.

## Authors
Cheng-Yu Yang (National Yang Ming Chiao Tung University), Shao-Yuan Lo (National Taiwan University), Yu-Lun Liu (National Yang Ming Chiao Tung University)

## Research Context

**What's new:** This paper introduces a novel recoverable routing approach, Reroute, which replaces the traditional "rank-and-remove" paradigm in vision-language models, improving grounding accuracy under aggressive token reduction. The key novel element is the ability to bypass and re-enter tokens at the next routing decision, preserving theoretical TFLOPs and KV-cache budget.

**Related in brain:** 
* wiki/synthesis/2026-06-16
* omnigamearena_a_unified_ue5_benchmark_for_vlm_game_agents_with_improvement_dynam
* variance_reduction_for_expectations_with_diffusion_teachers

**Knowledge gaps:** This paper assumes a certain level of understanding of vision-language models and token reduction methods, which may not be fully covered in the brain. To fully evaluate this work, one would need to learn more about the current state of VLMs and the challenges associated with token reduction.

**Explore next:** 
* The applicability of Reroute to other types of VLMs or pruning methods
* The comparison of Reroute with other token reduction methods in terms of efficiency and accuracy
* The potential integration of Reroute with other training-free or data-efficient methods

*Generated 2026-06-17 by research-notes.py*

<!-- timeline -->

## Timeline

- **2026-06-11** — Imported to GBrain and summarized
