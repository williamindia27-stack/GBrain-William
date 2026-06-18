---
type: paper
title: Architecture Patterns For Prod Llmagents
---

## Overview
The paper proposes a methodology for selecting and composing runtime architecture patterns for production large language model (LLM) agents, focusing on the stochastic-deterministic boundary (SDB) where an LLM output becomes a system action. This boundary is crucial as LLM agents fail in ways that look like model failures but are actually architectural choices. The paper aims to provide a framework for designing around the SDB explicitly, rather than rediscovering it through failure.

## Method
The core approach proposed is the stochastic-deterministic boundary (SDB), a four-part contract among a proposer (the LLM), a verifier (a deterministic check on the proposal), a commit step (the durable write that follows acceptance), and a reject signal (the typed response back to the proposer when verification fails). The paper also organizes three orthogonal concerns for production agent runtimes (Coordination, State, Control) and a catalog of six patterns that assemble the boundary differently across runtime classes.

## Key Results
* 19 of 21 LLM-to-action call sites in five widely-used open-source frameworks instantiate the SDB in some form.
* 71% of 21 published agent failure post-mortems localize to weaknesses at the SDB, and 81% of the documented fixes strengthen one of its four parts.
* The paper proposes a reliability decomposition (µt+σξ(t)) that separates per-call variance σ from architectural momentum µ, and grounds the claim that SDB strength and pattern choice dominate model selection as the dominant lever on long-run reliability.
* The methodology is validated by applying it end-to-end to five workloads spanning conversational, autonomous, and long-horizon runtimes.
* The paper identifies one failure mode the boundary makes legible: replay divergence, where LLM-based consumers of a deterministic event log produce different downstream outputs under model-version change.

## Why It Matters
The paper's methodology and framework are crucial for designing production LLM agents that are reliable and efficient, as they provide a structured approach to selecting and composing runtime architecture patterns. By focusing on the SDB and its surrounding patterns, teams can shape the architectural momentum of their systems, which becomes the dominant lever on aggregate reliability as per-call model quality improves.

## Limitations
The paper acknowledges that the proposed methodology and framework are not exhaustive, and that there are other aspects of production LLM agents that are not addressed, such as retrieval-augmented generation, evaluation harnesses, model selection, and prompt management. The paper also notes that the patterns in the catalog are runtime-architectural and do not cover upstream aspects of LLM agents.

## Keywords
LLM agents, stochastic-deterministic boundary, architectural momentum, replay divergence, runtime architecture patterns, conversational runtimes, autonomous runtimes, long-horizon runtimes, distributed systems, software architecture methodology.

## Authors

- [[people/vasundra-srinivasan|Vasundra Srinivasan]] — [[companies/stanford-school-of-engineering|Stanford School of Engineering]]

**Year:** 2026 · **Domain:** computer science


## Research Context

**What's new:** This paper contributes a novel methodology for selecting and composing runtime architecture patterns for production large language model (LLM) agents, focusing on the stochastic-deterministic boundary (SDB). The key novel element is the proposed framework for designing reliable and efficient production LLM agents.

**Related in brain:** There are no brain pages that directly overlap with this paper, as no related pages were found in the brain.

**Knowledge gaps:** This paper assumes a certain level of understanding of LLM agents and their architectural patterns, which may not be fully covered in the brain. To fully evaluate this work, one would need to learn more about the current state of LLM agent design and the challenges associated with their deployment in production environments.

**Explore next:** 
* The application of the stochastic-deterministic boundary (SDB) in other areas of artificial intelligence
* The integration of retrieval-augmented generation and other missing aspects into the proposed framework
* The evaluation of the proposed reliability decomposition (µt+σξ(t)) in real-world production LLM agent deployments

*Generated 2026-05-22 by research-notes.py*

<!-- timeline -->

## Timeline

- **2026-05-21** — Reprocessed by fix-raw-dumps.py