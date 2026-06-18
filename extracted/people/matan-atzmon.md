---
title: "Matan Atzmon"
type: person
tags: [researcher]
---

## Overview



<!-- bio-agent -->
Matan Atzmon is a computer scientist at NVIDIA focused on improving the computational efficiency of machine learning models through variance reduction techniques. His work addresses the high computational costs associated with using pretrained diffusion models as teachers in downstream tasks, developing the CARV method that combines hierarchical Monte Carlo estimation, timestep importance sampling, and stratified-inverse-CDF construction. In text-to-3D distillation and attribution experiments, his approach achieves 2-3× effective compute multipliers, with the majority of gains derived from amortized reuse of expensive upstream computations over cheap diffusion-noise resamples. He demonstrates that importance sampling using explicit teacher weights reduces variance by approximately 1.2× compared to uniform sampling, though he also identifies scenarios where variance reduction alone does not guarantee improved downstream performance. His research contributes practical solutions for making diffusion model-based systems more scalable and cost-effective across a broader range of applications.
**Affiliation:** [[nvidia|NVIDIA]]

## Timeline


- **2026-05-29** — Bio enriched by bio-agent (Claude claude-haiku-4-5)
- **2026-05-22** ? Discovered via build-research-graph.py
