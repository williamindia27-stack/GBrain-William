---
type: paper
title: BLF (Forecasting)
---

## Overview
The paper presents BLF (Bayesian Linguistic Forecaster), a system for binary forecasting that achieves state-of-the-art performance on the ForecastBench benchmark, outperforming top methods such as Cassi, GPT-5, and Foresight-32B. This matters because accurate forecasting is crucial in various domains, including geopolitics, finance, and public health. The system's performance is comparable to human superforecasters, with a difficulty-adjusted Brier Index (ABI) of 71.0.

## Method
The BLF system is built on three key ideas: (1) maintaining a semi-structured Bayesian linguistic belief state, which combines numerical probability estimates with natural-language evidence summaries; (2) hierarchical multi-trial aggregation, which runs multiple independent trials and combines them using logit-space shrinkage; and (3) hierarchical calibration, which uses Platt scaling with a hierarchical prior to avoid over-shrinking extreme predictions. The system uses an iterative tool-use loop, with a base LLM (mostly Gemini-3.1-Pro) and a search engine (Brave).

## Key Results
* BLF outperforms the top 5 methods on the ForecastBench leaderboard, with a p-value < 0.001 for all comparisons.
* The system achieves a difficulty-adjusted Brier Index (ABI) of 71.0, comparable to the human superforecaster median (ABI = 70.9).
* Ablation studies show that removing the structured belief state degrades the Brier Index by 5.1, while removing web search access degrades it by 3.4.
* Hierarchical shrinkage and calibration provide significant additional gains, with the former helping on some datasets but not others.

## Why It Matters
The BLF system's state-of-the-art performance on ForecastBench has practical significance, as it can be used to inform decision-making in various domains. The system's ability to outperform human superforecasters on some questions also highlights its potential for improving forecasting accuracy.

## Limitations
The authors acknowledge that the system's performance may be limited by the quality of the base LLM and the search engine used, as well as the potential for leakage from search and tool use. They implement a four-layer defense to minimize leakage, but acknowledge that some undetected leakage may still occur (1.5% residual leakage rate).

## Keywords
Bayesian forecasting, linguistic belief states, hierarchical aggregation, calibration, Platt scaling, ForecastBench, binary forecasting, agentic systems, large language models, tool-use loop.

## Authors

- [[people/kevin-murphy|Kevin Murphy]] — [[companies/university-of-british-columbia|University of British Columbia]]

**Year:** 2026 · **Domain:** computer science


## Research Context

**What's new:** This paper introduces the Bayesian Linguistic Forecaster (BLF) system, a novel approach to binary forecasting that achieves state-of-the-art performance on the ForecastBench benchmark. The key novel element is the combination of numerical probability estimates with natural-language evidence summaries in a semi-structured Bayesian linguistic belief state.

**Related in brain:** 
* None are truly related, as no relevant pages were found in the brain.

**Knowledge gaps:** This paper assumes a certain level of understanding of forecasting methods and benchmarks, such as the ForecastBench leaderboard, which may not be covered in the brain. To fully evaluate this work, one would need to learn about the current state of forecasting research and the limitations of existing methods.

**Explore next:** 
* The ForecastBench benchmark and its significance in the field of forecasting
* The potential applications of the BLF system in domains such as geopolitics, finance, and public health
* The limitations and potential biases of the BLF system, including the risk of leakage from search and tool use

*Generated 2026-05-22 by research-notes.py*

<!-- timeline -->

## Timeline

- **2026-05-21** ? Imported to GBrain and summarized