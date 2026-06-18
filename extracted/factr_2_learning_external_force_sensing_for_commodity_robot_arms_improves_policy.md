---
title: "Factr 2 Learning External Force Sensing For Commodity Robot Arms Improves Policy"
type: paper
---

## Overview
The paper addresses the problem of force sensing in commodity robot arms, which is essential for precise force-aware control in tasks such as insertion, fastening, and deformable-object handling. Many low-cost robot arms lack built-in force sensing, limiting their ability to provide force feedback during data collection and preventing policies from leveraging force information. The proposed system, FACTR 2, enables force-aware teleoperation and policy learning on off-the-shelf robots without additional sensing hardware.

## Method
The core approach proposed is Neural External Torque Estimation (NEXT), a data-driven method that estimates external joint torques without needing dedicated force sensors. NEXT trains a recurrent model on 10 minutes of free-motion data and produces high-quality estimates comparable to dedicated joint-torque sensors. The learned external force signal enables force-feedback teleoperation and Force-Informed Re-Sampling Training (FIRST), a behavior cloning method that up-samples pre-contact and contact segments during training.

## Key Results
* NEXT estimates external joint torques with high accuracy, comparable to dedicated joint-torque sensors, using only 10 minutes of free-motion data and 1 minute of training.
* FIRST improves policy learning by up-sampling pre-contact and contact segments during training, resulting in gains of over 17% in task progress across five long-horizon tasks.
* FACTR 2 enables force-feedback teleoperation on low-cost arms, such as the Piper and Y AM, achieving performance comparable to sensorized systems.
* NEXT outperforms prior estimation methods, including traditional analytical modeling and system identification approaches.
* FIRST consistently improves success rates over prior baselines, with gains in alignment, recovery, and contact-phase performance.

## Why It Matters
The proposed system, FACTR 2, democratizes force sensing for any robot arm, enabling both force-feedback teleoperation and force-aware policy learning on commodity robot arms. This has significant practical implications for robotics, as it allows for more precise and robust manipulation in a wide range of tasks.

## Limitations
The authors acknowledge that the proposed system may have limitations in terms of its ability to handle complex and dynamic environments, and that further research is needed to fully explore its potential and limitations.

## Keywords
robotics, force sensing, torque estimation, neural networks, teleoperation, policy learning, imitation learning, reinforcement learning, robot arms, manipulation, control systems.

## Authors
Steven Oh, Jason Jingzhou Liu, Tony Tao, Philip Han, Kenneth Shaw, Satoshi Funabashi, Ruslan Salakhutdinov, Deepak Pathak

## Research Context

**What's new:** This paper contributes a novel approach to force sensing in commodity robot arms, specifically the Neural External Torque Estimation (NEXT) method, which enables high-quality estimates of external joint torques without dedicated force sensors. The key novel element is the ability to achieve this using only 10 minutes of free-motion data and 1 minute of training.

**Related in brain:** 
* wiki/synthesis/2026-06-16
* an_agency_transferring_model_free_policy_enhancement_technique
* the_matching_principle_a_geometric_theory_of_loss_functions_for_nuisance_robust

**Knowledge gaps:** This paper assumes a certain level of familiarity with robotics and force sensing, which may not be fully covered in the brain. To fully evaluate this work, one would need to learn more about the current state of force sensing in robotics and the limitations of existing methods.

**Explore next:** 
* Investigating the applications of Neural External Torque Estimation (NEXT) in various robotics tasks
* Comparing the performance of NEXT with other force sensing methods
* Examining the potential of FACTR 2 for use in complex and dynamic environments

*Generated 2026-06-17 by research-notes.py*

<!-- timeline -->

## Timeline

- **2026-06-11** — Imported to GBrain and summarized
