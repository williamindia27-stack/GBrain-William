---
type: paper
title: Kronos
---

## Overview
Kronos is a foundation model designed for financial K-line data, addressing the limitations of existing Time Series Foundation Models (TSFMs) in handling financial data. It aims to provide a unified, scalable pre-training framework for various financial tasks, including price forecasting, volatility prediction, and synthetic data generation. Kronos is crucial as it enables the development of robust and generalizable models for financial time series analysis.

## Method
Kronos employs a specialized tokenizer to discretize continuous, multivariate K-line inputs into a sequence of compact tokens, preserving critical price-volume interactions. It then undergoes autoregressive pre-training on a massive, heterogeneous corpus of over 12 billion K-line records drawn from over 45 global markets and 7 temporal granularities. The model uses a two-phase framework: K-line tokenization and autoregressive pre-training.

## Key Results
* Kronos boosts price series forecasting RankIC by 93% over the leading TSFM and 87% over the best non-pre-trained baseline.
* It achieves a 9% lower MAE in volatility forecasting.
* Kronos demonstrates a 22% improvement in generative fidelity for synthetic K-line generation.
* The model outperforms specialized baselines in various quantitative finance tasks, including price forecasting, return forecasting, and investment simulation.

## Why It Matters
Kronos has significant practical implications as it provides a robust and versatile foundation model for end-to-end financial time series analysis, enabling the development of more accurate and reliable models for various financial tasks. Its ability to generalize across different markets and tasks makes it a valuable tool for financial institutions and researchers.

## Limitations
The authors acknowledge that Kronos may still have limitations in handling certain types of financial data or tasks, and that further research is needed to fully explore its potential and address any remaining challenges. Additionally, the model's performance may be sensitive to the quality and diversity of the pre-training data.

## Keywords
Time Series Foundation Models, financial K-line data, autoregressive pre-training, tokenization, price forecasting, volatility prediction, synthetic data generation, quantitative finance, machine learning, deep learning.

## Authors

- [[people/yu-shi|Yu Shi]] — [[companies/tsinghua-university|Tsinghua University]]
- [[people/zongliang-fu|Zongliang Fu]] — [[companies/tsinghua-university|Tsinghua University]]
- [[people/shuo-chen|Shuo Chen]] — [[companies/tsinghua-university|Tsinghua University]]
- [[people/bohan-zhao|Bohan Zhao]] — [[companies/tsinghua-university|Tsinghua University]]
- [[people/wei-xu|Wei Xu]] — [[companies/tsinghua-university|Tsinghua University]]
- [[people/changshui-zhang|Changshui Zhang]] — [[companies/tsinghua-university|Tsinghua University]]
- [[people/jian-li|Jian Li]] — [[companies/tsinghua-university|Tsinghua University]]

**Domain:** finance


## Research Context

**What's new:** This paper introduces Kronos, a foundation model designed specifically for financial K-line data, addressing limitations of existing Time Series Foundation Models. The key novel element is its unified, scalable pre-training framework for various financial tasks.

**Related in brain:** 
* None are truly related, as no relevant pages were found in the brain.

**Knowledge gaps:** This paper assumes a certain level of understanding of Time Series Foundation Models and financial K-line data, which may not be covered in the brain. To fully evaluate this work, one would need to learn about the current state of TSFMs and their applications in finance.

**Explore next:** 
* Time Series Foundation Models and their limitations in handling financial data
* Applications of Kronos in real-world financial tasks and markets
* Comparison of Kronos with other foundation models in non-financial domains

*Generated 2026-05-22 by research-notes.py*

<!-- timeline -->

## Timeline

- **2026-05-21** ? Imported to GBrain and summarized