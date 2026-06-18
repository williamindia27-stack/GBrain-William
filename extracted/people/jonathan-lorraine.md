---
title: "Jonathan Lorraine"
type: person
tags: [researcher]
---

## Overview



<!-- bio-agent -->
Jonathan Lorraine is a computer scientist at NVIDIA whose research focuses on improving the computational efficiency of machine learning systems, particularly in the context of diffusion model applications. His work on variance reduction for expectations with diffusion teachers introduces the CARV method, which combines hierarchical Monte Carlo estimation, timestep importance sampling, and stratified-inverse-CDF construction to achieve 2-3× effective compute multipliers in downstream tasks like text-to-3D distillation and attribution experiments. He employs a compute-aware variance-accounting framework that systematically addresses the high computational costs associated with using pretrained diffusion models as teachers, demonstrating that amortization of expensive upstream computations over cheap diffusion-noise resamples yields substantial practical gains. His research reveals important insights about the conditions under which variance reduction translates to improved performance, as exemplified by findings that gradient variance reduction does not always improve downstream metrics like FID in certain regimes. Lorraine's work aims to make diffusion model-based systems more scalable and accessible by enabling significant cost savings that expand deployment possibilities across diverse applications.
**Affiliation:** [[nvidia|NVIDIA]]

## Timeline


- **2026-05-29** — Bio enriched by bio-agent (Claude claude-haiku-4-5)
- **2026-05-22** ? Discovered via build-research-graph.py
