# New Paper Imported — Omnigamearena A Unified Ue5 Benchmark For Vlm Game Agents With Improvement Dynam

*Imported: 2026-06-09 12:00*

## Summary

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

---
*gbrain slug: `omnigamearena_a_unified_ue5_benchmark_for_vlm_game_agents_with_improvement_dynam`*
