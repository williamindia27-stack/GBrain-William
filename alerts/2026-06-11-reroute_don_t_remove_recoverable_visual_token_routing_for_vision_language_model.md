# New Paper Imported — Reroute, Don'T Remove Recoverable Visual Token Routing For Vision Language Model

*Imported: 2026-06-11 11:30*

## Summary

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

---
*gbrain slug: `reroute_don_t_remove_recoverable_visual_token_routing_for_vision_language_model`*
