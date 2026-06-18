# New Paper Imported — A Methodology For Selecting And Composing Runtime Architecture Patterns For Prod

*Imported: 2026-05-22 14:14*

## Summary

## Overview
This paper proposes a methodology for selecting and composing runtime architecture patterns for production large language model (LLM) agents, focusing on the stochastic-deterministic boundary (SDB) as the load-bearing engineering surface. The SDB is a four-part contract that specifies how an LLM output becomes a system action, and its strength and pattern choice dominate model selection as the dominant lever on long-run reliability. The paper aims to help practitioners design around the SDB explicitly, rather than rediscovering it through failure.

## Method
The core approach proposed is to organize three orthogonal concerns (Coordination, State, Control) and a catalog of six patterns that assemble the SDB differently across runtime classes. The paper also specifies a five-step selection methodology with decision predicates and a written validation artifact, and a diagnostic procedure that maps observed production failures to specific patterns through a failure-signature catalog.

## Key Results
* 19 of 21 LLM-to-action call sites in five widely-used open-source frameworks instantiate the SDB in some form, with explicit verifier-and-commit logic.
* 71% of 21 published agent failure post-mortems localize to weaknesses at the SDB, and 81% of the documented fixes strengthen one of its four parts.
* The paper applies the methodology end-to-end to five workloads spanning conversational, autonomous, and long-horizon runtimes, with one built out as a runnable reference implementation.
* The reliability decomposition (µt+σξ(t)) separates per-call variance σ from architectural momentum µ, grounding the claim that SDB strength and pattern choice dominate model selection.
* The paper identifies one failure mode made legible by the SDB: replay divergence, where LLM-based consumers of a deterministic event log produce different downstream outputs under model-version change.

## Why It Matters
The proposed methodology and SDB primitive help teams shape the architectural momentum (µ) of their production agent systems, which becomes the dominant lever on aggregate reliability as per-call variance (σ) compresses with each model generation. This allows for more reliable and efficient production LLM agents.

## Limitations
The paper acknowledges that the patterns in the catalog are not exhaustive, and that the discovery procedure is positioned to admit new patterns. Additionally, the paper does not survey retrieval-augmented generation, evaluation harnesses, model selection, or prompt management, as these are upstream of the runtime.

## Keywords
LLM agents, stochastic-deterministic boundary, architectural momentum, replay divergence, software architecture methodology, multi-agent systems, distributed systems, runtime architecture patterns.

---
*gbrain slug: `a_methodology_for_selecting_and_composing_runtime_architecture_patterns_for_prod`*
