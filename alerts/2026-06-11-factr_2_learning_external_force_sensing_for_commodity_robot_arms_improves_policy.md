# New Paper Imported — Factr 2 Learning External Force Sensing For Commodity Robot Arms Improves Policy

*Imported: 2026-06-11 11:30*

## Summary

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

---
*gbrain slug: `factr_2_learning_external_force_sensing_for_commodity_robot_arms_improves_policy`*
