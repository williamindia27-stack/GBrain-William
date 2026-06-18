---
title: "Jesse Bettencourt"
type: person
tags: [researcher]
---

## Overview



<!-- bio-agent -->
Jesse Bettencourt is a machine learning researcher at NVIDIA focused on computational efficiency and variance reduction techniques in deep generative models. His work addresses the high computational costs associated with using pretrained diffusion models as teachers in downstream tasks through novel variance reduction methods. In "Variance Reduction For Expectations With Diffusion Teachers," Bettencourt introduces CARV, a hierarchical Monte Carlo estimator that combines amortized upstream computations with timestep importance sampling and stratified-inverse-CDF construction to achieve 2-3× effective compute multipliers in text-to-3D distillation and attribution tasks. His approach is grounded in a compute-aware variance-accounting framework that enables practical estimator design choices, with importance sampling techniques reducing variance by approximately 1.2× over uniform sampling at equal computational cost. Bettencourt's research demonstrates the potential for significant cost savings—estimated in the six to seven figure range at lab scale—in deploying diffusion model-based systems across a wider range of applications.
**Affiliation:** [[nvidia|NVIDIA]]

## Timeline


- **2026-05-29** — Bio enriched by bio-agent (Claude claude-haiku-4-5)
- **2026-05-22** ? Discovered via build-research-graph.py
