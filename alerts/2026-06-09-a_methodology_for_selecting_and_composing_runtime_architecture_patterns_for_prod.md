# New Paper Imported — A Methodology For Selecting And Composing Runtime Architecture Patterns For Prod

*Imported: 2026-06-09 10:56*

## Summary

## Overview
This paper proposes a methodology for selecting and composing runtime architecture patterns for production large language model (LLM) agents, focusing on the stochastic-deterministic boundary (SDB) as the load-bearing engineering surface. The SDB is a four-part contract that specifies how an LLM output becomes a system action, and its strength and pattern choice dominate model selection as the dominant lever on long-run reliability. The paper aims to provide a framework for designing production agent runtimes that can mitigate failures and improve reliability.

## Method
The core approach proposed in this paper is the identification of the stochastic-deterministic boundary (SDB) as a named primitive, with a four-part contract (proposer, verifier, commit, reject) and an empirical inventory of how five widely-used open-source agent frameworks instantiate it. The paper also organizes three orthogonal concerns (Coordination, State, Control) and a catalog of six patterns that compose the boundary differently for different runtime classes.

## Key Results
* 19 of 21 LLM-to-action call sites in five widely-used open-source frameworks have explicit verifier-and-commit logic, indicating the presence of the SDB.
* 71% of 21 published agent failure post-mortems localize to weaknesses at the SDB, and 81% of the documented fixes strengthen one of its four parts.
* The paper proposes a five-step selection methodology with decision predicates and a written validation artifact, and a diagnostic procedure that maps observed production failures to specific patterns via a failure-signature catalog.
* The reliability decomposition (µt+σξ(t)) separates per-call variance σ from architectural momentum µ, and grounds the claim that SDB strength and pattern choice dominate model selection as the dominant lever on long-run reliability.
* The methodology is validated by applying it end-to-end to five workloads spanning conversational, autonomous, and long-horizon runtimes.

## Why It Matters
The proposed methodology is significant because it provides a framework for designing production agent runtimes that can mitigate failures and improve reliability, which is critical for the widespread adoption of LLM agents in real-world applications. By identifying the SDB as a named primitive and providing a catalog of patterns that compose the boundary, the paper enables practitioners to design around it explicitly and make informed decisions about runtime architecture.

## Limitations
The authors acknowledge that the paper does not survey retrieval-augmented generation, evaluation harnesses, model selection, or prompt management, which are upstream of the runtime and necessary but not the focus of this paper. Additionally, the paper's scope is limited to runtime-architectural patterns that govern what happens between the model's outputs and the world's state.

## Keywords
LLM agents, stochastic-deterministic boundary, architectural momentum, replay divergence, software architecture methodology, multi-agent systems, distributed systems, runtime architecture patterns.

---
*gbrain slug: `a_methodology_for_selecting_and_composing_runtime_architecture_patterns_for_prod`*
