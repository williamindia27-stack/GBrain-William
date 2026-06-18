# New Paper Imported — Eevee Towards Test Time Prompt Learning In The Real World For Self Improving Age

*Imported: 2026-06-10 12:45*

## Summary

## Overview
Eevee is a test-time prompt learning framework that enables self-improving agents to adapt to heterogeneous input streams from multiple datasets and domains. This framework addresses the problem of cross-dataset interference, where updates for one task can harm another, and provides a lightweight mechanism for adapting foundation models after deployment. Eevee's approach is crucial for real-world applications where models need to handle diverse input streams.

## Method
Eevee proposes a router-prompt co-evolution strategy that interleaves router and prompt learning phases to address their mutual dependency. The framework consists of a set of specialized prompts and a router that chooses which prompt to handle each input. The router and prompt set are learned through a three-stage training process that initializes useful prompt slots, explores coupled updates efficiently, and converges under a stable router.

## Key Results
* Eevee improves average multi-benchmark scores by 10.38 and 24.32 points over Qwen3-4B-Instruct and DeepSeek-V3.2.
* Eevee surpasses SOTA methods GEPA and ACE by up to 37.2% and 48.2%.
* Eevee ends with a +41.53 cumulative retention gain after all tasks are introduced in the incremental multi-benchmark setting, while GEPA and ACE end at -15.36 and -18.58.
* Eevee's routing design remains competitive in conventional single-task settings while avoiding ACE's large prompt expansion.

## Why It Matters
Eevee's framework provides a practical solution for self-improving agents to adapt to real-world task streams, enabling them to refine their behavior through interaction with the environment. This approach has significant implications for applications where models need to handle diverse input streams and adapt to changing task distributions.

## Limitations
The authors acknowledge that designing the router is a challenging task, and a rigid or unstable router can fail to capture diverse task structures or disrupt prompt optimization. Further research is needed to improve the router-prompt co-evolution strategy and explore its applications in various domains.

## Keywords
test-time prompt learning, self-improving agents, multi-dataset learning, router-prompt co-evolution, heterogeneous input streams, foundation models, adaptive learning, natural language processing, machine learning.

---
*gbrain slug: `eevee_towards_test_time_prompt_learning_in_the_real_world_for_self_improving_age`*
