---
type: paper
title: Atoms Of Thought Universal Eeg Representation Learning With Microstates
---

## Overview
This paper proposes a novel approach to learning universal representations from electroencephalogram (EEG) signals using microstates, which are quasi-stable discrete patterns of scalp electrical potential that last for brief periods. This approach aims to address the challenges of traditional time-domain and frequency-domain features, which are susceptible to artifacts and lack interpretability. By leveraging microstates, the authors aim to improve the accuracy and efficiency of EEG-based classification tasks, such as sleep staging, emotion recognition, and motor imagery classification.

## Method
The authors propose a microstate tokenizer that clusters continuous EEG signals into sequences of discrete microstates using a k-means clustering method. This tokenizer is then adopted universally across a series of downstream tasks, including sleep staging, emotion recognition, and motor imagery classification. The microstate representation is compared to traditional time-domain and frequency-domain features, and its effectiveness is validated across different models and tasks.

## Key Results
* The microstate representation outperforms traditional time-domain and frequency-domain features in sleep staging, emotion recognition, and motor imagery classification tasks.
* The microstate tokenizer initialized in one task can be generalized to a series of downstream tasks, showcasing its universal applicability and alleviating the impact of data scarcity.
* EEG microstates show greater performance gain than conventional features with increasing data size, demonstrating their scalability.
* The microstate representation provides greater interpretability and can serve as an explainable feature linking to various cognitive functions.

## Why It Matters
The proposed microstate representation has significant practical and scientific implications, as it can improve the accuracy and efficiency of EEG-based classification tasks and provide a more interpretable and scalable representation of brain activity. This can lead to breakthroughs in cognitive neuroscience, clinical research, and brain-computer interfaces.

## Limitations
The authors acknowledge that the current study is limited to a specific set of tasks and models, and further research is needed to fully explore the potential of microstate representation in EEG analysis. Additionally, the authors note that the interpretability of microstates and their connection to fundamental cognitive states require further investigation.

## Keywords
EEG analysis, microstates, sleep staging, emotion recognition, motor imagery classification, deep learning, representation learning, brain-computer interfaces, cognitive neuroscience, neuroinformatics.

## Authors

- [[people/xinyang-tian|Xinyang Tian]] — [[companies/tsinghua-university|Tsinghua University]]
- [[people/ruitao-liu|Ruitao Liu]] — [[companies/tsinghua-university|Tsinghua University]]
- [[people/ziyi-ye|Ziyi Ye]] — [[companies/fudan-university|Fudan University]]
- [[people/siyang-xue|Siyang Xue]] — [[companies/tsinghua-university|Tsinghua University]]
- [[people/xin-wang|Xin Wang]] — [[companies/beijing-five-seasons-medical-technology-co-ltd|Beijing Five Seasons Medical Technology Co., Ltd.]]
- [[people/xuesong-chen|Xuesong Chen]] — [[companies/beijing-five-seasons-medical-technology-co-ltd|Beijing Five Seasons Medical Technology Co., Ltd.]]

**Year:** 2025 · **Domain:** computer science


## Research Context

**What's new:** This paper contributes a novel approach to learning universal representations from electroencephalogram (EEG) signals using microstates, which is not currently covered in the brain. The key novel element is the proposal of a microstate tokenizer that can be applied universally across various downstream tasks.

**Related in brain:** 
* No related pages are found in the brain that directly overlap with this paper.

**Knowledge gaps:** This paper assumes a certain level of understanding of EEG signals and microstates, which may not be fully covered in the brain. To fully evaluate this work, one would need to learn about the current state of EEG analysis and the limitations of traditional time-domain and frequency-domain features.

**Explore next:** 
* The application of microstate representation in other areas of cognitive neuroscience and clinical research
* The potential of microstate tokenizers in brain-computer interfaces
* The interpretability of microstates and their connection to fundamental cognitive states

*Generated 2026-05-22 by research-notes.py*

<!-- timeline -->

## Timeline

- **2026-05-21** — Reprocessed by fix-raw-dumps.py