# New Paper Imported — Quantifying Hyperparameter Transfer And The Importance Of Embedding Layer Learni

*Imported: 2026-05-21 11:05*

## Summary

**What it is:** This paper investigates hyperparameter transfer, a method for extrapolating optimal optimization hyperparameters from small to large scales, which is crucial for training large language models.
**Key contribution:** The authors develop a framework to quantify hyperparameter transfer through three metrics, including the quality of the scaling law fit, robustness to extrapolation errors, and asymptotic loss penalty due to choice of parameterization.
**Main finding:** The study finds that the Maximal Update Parameterization (µP) offers high-quality learning rate transfer relative to standard parameterization (SP) primarily because it maximizes the learning rate of the embedding layer, which acts as a bottleneck in SP and induces training instabilities.

---
*gbrain slug: `quantifying_hyperparameter_transfer_and_the_importance_of_embedding_layer_learni`*
