---
type: paper
title: Smokescreen
---

## Overview
Smokescreen is a Python package designed to address the problem of experimenter bias in cosmological analyses by providing a data-vector blinding and encryption method. This approach is crucial in preventing analysts from unconsciously tuning their pipelines towards an expected result, thereby compromising the scientific integrity of the measurement. Smokescreen's method is particularly important in cosmological experiments where it is challenging to design analyses in a double-blind or single-blind manner.

## Method
Smokescreen's core approach involves applying cosmology-dependent shifts to the observed data vector, moving it away from the true cosmological signal without affecting its statistical properties. The package uses Firecrown likelihoods and the SACC format to compute these shifts, ensuring that the theoretical model used for blinding is identical to that used for inference. The blinding process involves five steps, including constructing a concealed cosmology, evaluating theory vectors, computing a blinding factor, and applying the factor to the measured data vector.

## Key Results
* Smokescreen achieves 94% code coverage as tracked by Codecov, ensuring the physical correctness of the blinding process.
* The package can perform shifts in any of the base cosmological parameters present in pyCCL.
* Smokescreen's test suite verifies the correctness of the blinding process, including the computation of additive and multiplicative blinding factors.
* The package provides a standardized implementation of the data vector blinding methodology, making it easier to integrate with collaboration-wide analysis pipelines.
* Smokescreen allows for the use of any Firecrown-compatible likelihood, guaranteeing that the theoretical modeling used for concealment is identical to that used for inference.

## Why It Matters
Smokescreen's data-vector blinding and encryption method provides a practical solution to the problem of experimenter bias in cosmological analyses, ensuring the scientific integrity of the measurement. By making the concealment procedure transparent and reproducible, Smokescreen allows the wider community to inspect and verify how blinding shifts are computed prior to and post unblinding.

## Limitations
The authors acknowledge that Smokescreen is designed specifically for experiments using Firecrown likelihoods and the SACC data format, which may limit its applicability to other types of analyses. Additionally, the package's effectiveness relies on the quality of the input data and the accuracy of the theoretical models used for blinding and inference.

## Keywords
cosmological analyses, data-vector blinding, encryption, Firecrown likelihoods, SACC format, pyCCL, experimenter bias, scientific integrity, reproducibility, transparency.

## Authors

- [[people/arthur-loureiro|Arthur Loureiro]] — [[companies/stockholm-university|Stockholm University]]
- [[people/jessica-muir|Jessica Muir]] — [[companies/university-of-cincinnati|University of Cincinnati]]
- [[people/jonathan-blazek|Jonathan Blazek]] — [[companies/northeastern-university|Northeastern University]]
- [[people/nora-elisa-chisari|Nora Elisa Chisari]] — [[companies/utrecht-university|Utrecht University]]
- [[people/pedro-h-costa-ribeiro|Pedro H. Costa Ribeiro]] — [[companies/universidade-federal-do-rio-de-janeiro|Universidade Federal do Rio de Janeiro]]
- [[people/christos-georgiou|Christos Georgiou]] — [[companies/the-barcelona-institute-of-science-and-technology|The Barcelona Institute of Science and Technology]]
- [[people/c-danielle-leonard|C. Danielle Leonard]] — [[companies/newcastle-university|Newcastle University]]
- [[people/bruno-moraes|Bruno Moraes]] — [[companies/cbpf-centro-brasileiro-de-pesquisas-f-sicas|CBPF - Centro Brasileiro de Pesquisas Físicas]]
- [[people/marc-paterno|Marc Paterno]] — [[companies/fermi-national-accelerator-laboratory|Fermi National Accelerator Laboratory]]
- [[people/nikolina-sarcevic|Nikolina Šarčević]] — [[companies/duke-university|Duke University]]
- [[people/tilman-troester|Tilman Tröster]] — [[companies/eth-zurich|ETH Zurich]]
- [[people/sandro-d-p-vitenti|Sandro D. P. Vitenti]] — [[companies/universidade-estadual-de-londrina|Universidade Estadual de Londrina]]

**Year:** 2026 · **Domain:** physics


## Research Context

**What's new:** This paper introduces Smokescreen, a Python package that addresses experimenter bias in cosmological analyses through data-vector blinding and encryption, a novel approach to ensuring scientific integrity in measurements. The key novel element is the application of cosmology-dependent shifts to observed data vectors.

**Related in brain:** 
* None, as no related pages were found in the brain.

**Knowledge gaps:** This paper assumes a certain level of familiarity with cosmological analyses, Firecrown likelihoods, and the SACC data format, which may not be covered in the brain. To fully evaluate this work, one would need to learn about these topics and their relevance to experimenter bias.

**Explore next:** 
* The application of Smokescreen to various cosmological analyses to test its effectiveness
* The development of similar blinding and encryption methods for other types of analyses
* The potential limitations and biases of using Firecrown likelihoods and the SACC data format in Smokescreen

*Generated 2026-05-22 by research-notes.py*

<!-- timeline -->

## Timeline

- **2026-05-21** ? Imported to GBrain and summarized