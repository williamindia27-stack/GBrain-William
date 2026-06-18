# New Paper Imported — Variance Reduction For Expectations With Diffusion Teachers

*Imported: 2026-05-21 11:05*

## Summary

**What it is:** The paper "Variance Reduction for Expectations with Diffusion Teachers" introduces a framework called CARV to reduce the variance of Monte Carlo expectations in diffusion models used as teachers in downstream pipelines.
**Key contribution:** The authors propose a hierarchical Monte Carlo estimator that amortizes expensive upstream computations over cheap diffusion-noise resamples, combined with timestep importance sampling and stratified-inverse-CDF construction.
**Main finding:** The CARV framework delivers 2-3× effective compute multipliers in text-to-3D distillation and attribution experiments, and cuts gradient variance by an order of magnitude in single-step distillation, without changing the objective.

---
*gbrain slug: `variance_reduction_for_expectations_with_diffusion_teachers`*
