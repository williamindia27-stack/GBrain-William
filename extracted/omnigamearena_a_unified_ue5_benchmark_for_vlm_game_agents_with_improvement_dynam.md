---
title: "Omnigamearena A Unified Ue5 Benchmark For Vlm Game Agents With Improvement Dynam"
type: paper
---

## Overview
The paper introduces OmniGameArena, a unified benchmark for vision-language model (VLM) game agents that addresses the gaps in current game benchmarks by providing a real-time environment with twelve newly built Unreal Engine 5 games spanning Solo, PvP, and Coop regimes. This benchmark matters because it enables the evaluation of VLM agents in a more comprehensive and realistic setting, beyond single-agent Solo play. The OmniGameArena benchmark is significant because it allows for the assessment of VLM agents' abilities to adapt and improve under repeated interaction with the same task.

## Method
The core approach proposed in the paper is the use of the Improvement Dynamics Curve (IDC) harness, which refines a bounded skill prompt across multiple rounds using an autonomous tool-use reflector. The IDC harness runs each (agent, game) instance for multiple rounds, with the agent playing K episodes under a current skill prompt, followed by refinement of the skill for the next round. The OmniGameArena benchmark provides a unified action interface for heterogeneous agents, including commercial VLMs, open-weight VLMs, and specialized game policies.

## Key Results
* Twelve VLM agents are evaluated on the cold-start leaderboard, with no single agent dominating across all games.
* Four top agents are run through the IDC harness, with all four improving over their cold-start baseline through reflection.
* Peak performance is typically reached mid-curve rather than at the final round, indicating that VLM agents can adapt and improve under repeated interaction.
* Origin-task improvement and held-out variant transfer can diverge in the experiments, highlighting the importance of evaluating VLM agents in a more comprehensive setting.

## Why It Matters
The OmniGameArena benchmark and the IDC harness provide a more comprehensive and realistic evaluation of VLM game agents, enabling the assessment of their abilities to adapt and improve under repeated interaction with the same task. This has significant implications for the development of more effective VLM agents in real-world applications.

## Limitations
The authors acknowledge that the current implementation of the IDC harness has limitations, such as the use of a bounded skill prompt and the reliance on a specific reflector LLM. Further research is needed to address these limitations and improve the robustness and generalizability of the OmniGameArena benchmark.

## Keywords
Vision-language models, game benchmarks, Improvement Dynamics Curve, autonomous reflection, Unreal Engine 5, Solo, PvP, Coop, heterogeneous agents, commercial VLMs, open-weight VLMs, specialized game policies.

## Authors

- [[people/mingxian-lin|Mingxian Lin]] — [[companies/the-university-of-hong-kong|The University of Hong Kong]]
- [[people/shengju-qian|Shengju Qian]] — [[companies/lightspeed|LIGHTSPEED]]
- [[people/yuqi-liu|Yuqi Liu]] — [[companies/the-chinese-university-of-hong-kong|The Chinese University of Hong Kong]]
- [[people/yi-hua-huang|Yi-Hua Huang]] — [[companies/the-university-of-hong-kong|The University of Hong Kong]]
- [[people/yiyu-wang|Yiyu Wang]] — [[companies/lightspeed|LIGHTSPEED]]
- [[people/wei-huang|Wei Huang]] — [[companies/the-university-of-hong-kong|The University of Hong Kong]]
- [[people/yitang-li|Yitang Li]] — [[companies/tsinghua-university|Tsinghua University]]
- [[people/fan-zhang|Fan Zhang]] — [[companies/the-chinese-university-of-hong-kong|The Chinese University of Hong Kong]]
- [[people/zeyu-hu|Zeyu Hu]] — [[companies/lightspeed|LIGHTSPEED]]
- [[people/lingting-zhu|Lingting Zhu]] — [[companies/lightspeed|LIGHTSPEED]]
- [[people/xin-wang|Xin Wang]] — [[companies/lightspeed|LIGHTSPEED]]
- [[people/xiaojuan-qi|Xiaojuan Qi]] — [[companies/the-university-of-hong-kong|The University of Hong Kong]]

**Year:** 2024 · **Domain:** computer science


## Research Context

**What's new:** This paper introduces OmniGameArena, a unified benchmark for vision-language model (VLM) game agents, which provides a more comprehensive and realistic evaluation of VLM agents. The key novel element is the use of the Improvement Dynamics Curve (IDC) harness to refine a bounded skill prompt across multiple rounds.

**Related in brain:** 
* None are truly related, as no related pages were found in the brain.

**Knowledge gaps:** This paper assumes a certain level of understanding of VLM game agents and their applications, which may not be covered in the brain. To fully evaluate this work, one would need to learn about the current state of VLM game agents and their limitations.

**Explore next:** 
* The development of more advanced IDC harnesses that can refine skill prompts without relying on bounded prompts or specific reflector LLMs.
* The application of OmniGameArena to real-world scenarios, such as game development or robotics.
* The comparison of OmniGameArena with other benchmarks for VLM game agents to assess its effectiveness and generalizability.

*Generated 2026-06-09 by research-notes.py*

<!-- timeline -->

## Timeline

- **2026-06-09** — Imported to GBrain and summarized
