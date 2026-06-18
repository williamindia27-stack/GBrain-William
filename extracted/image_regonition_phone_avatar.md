---
type: paper
title: MUA (Mobile Avatars)
---

## Overview
The paper proposes a novel approach to creating photorealistic, animatable full-body digital humans, addressing the longstanding challenge of achieving both high fidelity and low computational complexity. Existing methods either prioritize fidelity or efficiency, but not both. The proposed approach, MUA (Mobile Ultra-detailed Animatable Avatars), aims to bridge this gap. This is crucial for immersive applications, such as virtual and mixed reality, where vivid and realistic experiences can enhance decision-making and education.

## Method
The core approach proposed is a wavelet-guided multi-level spatial factorized blendshape representation, which decomposes the full-resolution Gaussian splat texture into multi-level wavelet subbands and models each subband with a tailored representation. This allows for expressive modeling of both large-scale motion-driven deformations and fine-grained details at low computational cost. A distillation pipeline is also introduced to transfer motion-dependent geometric deformations and appearance details from a high-fidelity teacher model into the proposed compact student representation.

## Key Results
* Achieves up to 2000× lower computational cost and a 10× smaller model size than the original high-quality teacher avatar model
* Preserves visually plausible dynamics and appearance details closely resembling those of the teacher model
* Outperforms mobile-based approaches by a clear margin and achieves performance comparable to, or even better than, server-based approaches
* Enables real-time on-device inference at 24 FPS on a standalone Meta Quest 3 headset and over 180 FPS on a desktop PC

## Why It Matters
The proposed approach has significant practical implications for immersive applications, such as virtual and mixed reality, by enabling the deployment of high-fidelity animatable avatars on mobile devices, including VR headsets. This can enhance the sense of immersion and realism in these applications.

## Limitations
The authors acknowledge that the proposed approach may still have limitations in terms of capturing extremely complex clothing dynamics or fine-grained details, and that further research is needed to address these challenges. Additionally, the approach relies on a pre-trained ultra-high-quality teacher avatar model, which may require significant computational resources to train.

## Keywords
animatable avatars, neural rendering, 3D Gaussian splatting, mobile deployment, wavelet-guided multi-level spatial factorized blendshapes, distillation pipeline, virtual reality, mixed reality, computer graphics, computer vision

## Authors

- [[people/heming-zhu|Heming Zhu]] — [[companies/mpi|MPI]]
- [[people/guoxing-sun|Guoxing Sun]] — [[companies/mpi|MPI]]
- [[people/marc-habermann|Marc Habermann]] — [[companies/mpi|MPI]]

**Domain:** computer science


## Research Context

**What's new:** This paper contributes a novel approach to creating photorealistic, animatable full-body digital humans, achieving both high fidelity and low computational complexity. The key novel element is the wavelet-guided multi-level spatial factorized blendshape representation.

**Related in brain:** 
* None are truly related, as no relevant pages were found in the brain.

**Knowledge gaps:** This paper assumes a pre-trained ultra-high-quality teacher avatar model, which may require significant computational resources to train, and this assumption is not covered in the brain. To fully evaluate this work, one would need to learn about the requirements and limitations of training such models.

**Explore next:** 
* The application of MUA in virtual and mixed reality environments
* The potential of wavelet-guided multi-level spatial factorized blendshape representation in other computer vision tasks
* The trade-offs between model size, computational cost, and fidelity in digital human modeling

*Generated 2026-05-22 by research-notes.py*

<!-- timeline -->

## Timeline

- **2026-05-21** ? Imported to GBrain and summarized