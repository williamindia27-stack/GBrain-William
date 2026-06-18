# New Paper Imported — A Methodology For Selecting And Composing Runtime Architecture Patterns For Prod

*Imported: 2026-06-12 15:46*

## Summary

## Overview
The paper proposes a methodology for selecting and composing runtime architecture patterns for production large language model (LLM) agents, addressing the stochastic-deterministic boundary (SDB) that is crucial for production agent reliability. This boundary is where an LLM output becomes a system action, and its design significantly impacts the overall reliability of the system. The methodology aims to help practitioners design around the SDB explicitly, rather than rediscovering it through failure.

## Method
The core approach involves organizing three orthogonal concerns for production agent runtimes (Coordination, State, Control) and a catalog of six patterns that assemble the SDB differently across runtime classes. The authors also propose a five-step selection methodology with decision predicates and a written validation artifact, as well as a diagnostic procedure that maps observed production failures to specific patterns.

## Key Results
* 19 out of 21 LLM-to-action call sites in five widely-used open-source frameworks have explicit verifier-and-commit logic, indicating the presence of the SDB.
* 71% of 21 published agent failure post-mortems localize to weaknesses at the SDB, and 81% of the documented fixes strengthen one of its four parts.
* The proposed reliability decomposition (y(t) = µt + σξ(t)) separates per-call variance σ from architectural momentum µ, highlighting the importance of SDB strength and pattern choice in determining long-run reliability.
* The methodology is validated by applying it to five workloads spanning conversational, autonomous, and long-horizon runtimes, with one workload built out as a runnable reference implementation.
* The authors identify "replay divergence" as a failure mode that the SDB makes legible, where LLM-based consumers of a deterministic event log produce different downstream outputs under model-version change.

## Why It Matters
The proposed methodology and SDB concept have significant practical implications for designing and deploying reliable production LLM agents, as they help practitioners explicitly address the load-bearing engineering surface of the agent runtime. By designing around the SDB, teams can shape the architectural momentum and improve the overall reliability of their systems.

## Limitations
The authors acknowledge that the paper does not survey retrieval-augmented generation, evaluation harnesses, model selection, or prompt management, which are upstream of the runtime and necessary but not the focus of this work. The methodology and patterns proposed are runtime-architectural, governing what happens between the model's outputs and the world's state.

## Keywords
LLM agents, stochastic-deterministic boundary, architectural momentum, replay divergence, software architecture methodology, multi-agent systems, distributed systems, runtime architecture patterns.

---
*gbrain slug: `a_methodology_for_selecting_and_composing_runtime_architecture_patterns_for_prod`*
