---
type: paper
title: AgentScope
---

## Overview
AgentScope is a developer-centric framework for building agentic applications, empowering agents to combine intrinsic knowledge with dynamic tool use, and enhancing their capacity to address real-world tasks. This framework solves the problem of building flexible and efficient agent-environment interactions, which is crucial for developing powerful LLM-based agent applications. AgentScope provides a practical foundation for building scalable, adaptive, and effective agentic applications.

## Method
The core approach of AgentScope is to abstract foundational components essential for agentic applications, including message, model, memory, and tool modules, and provide unified interfaces and extensible modules. AgentScope also adopts the ReAct paradigm, which combines explicit reasoning with actions, enabling agents to analyze tasks, call tools, observe execution results, and iteratively refine their steps in a closed loop.

## Key Results
* AgentScope provides a set of foundational components, including message, model, memory, and tool modules, which can be composed flexibly to serve a broad set of practical applications.
* The framework supports parallel tool calls, asynchronous executions, and real-time steering, delivering industrial-grade performance and efficiency for running agentic applications.
* AgentScope integrates several built-in agents, including a browser-use agent, a deep research agent, and a meta-planner agent, which can be used out of the box or customized further.
* The framework includes a comprehensive suite of toolkits, such as the evaluation module and Studio, to streamline the entire workflow and provide developer-friendly experiences.
* AgentScope provides a runtime sandbox to ensure safe agent execution and facilitate rapid deployment in production environments.

## Why It Matters
AgentScope provides a practical foundation for building scalable, adaptive, and effective agentic applications, which can solve complex real-world problems and support flexible interactions with both users and environments. The framework's ability to integrate diverse LLM APIs and support tool-based perception and interaction makes it a promising direction in both academic research and industrial practice.

## Limitations
The authors acknowledge that AgentScope is still a developing framework, and its limitations include the need for further customization and extension of its foundational components to support a wider range of practical applications. Additionally, the framework's performance and efficiency may vary depending on the specific use case and deployment environment.

## Keywords
Large Language Models, Agentic Applications, ReAct Paradigm, Tool-Based Interaction, Agent-Environment Interaction, Developer-Centric Framework, Modular Design, Extensibility, Scalability, Adaptability, Efficiency.

## Authors

- [[people/dawei-gao|Dawei Gao]] — [[companies/alibaba-group|Alibaba Group]]
- [[people/zitao-li|Zitao Li]] — [[companies/alibaba-group|Alibaba Group]]
- [[people/yuexiang-xie|Yuexiang Xie]] — [[companies/alibaba-group|Alibaba Group]]
- [[people/weirui-kuang|Weirui Kuang]] — [[companies/alibaba-group|Alibaba Group]]
- [[people/liuyi-yao|Liuyi Yao]] — [[companies/alibaba-group|Alibaba Group]]
- [[people/bingchen-qian|Bingchen Qian]] — [[companies/alibaba-group|Alibaba Group]]
- [[people/zhijian-ma|Zhijian Ma]] — [[companies/alibaba-group|Alibaba Group]]
- [[people/yue-cui|Yue Cui]] — [[companies/alibaba-group|Alibaba Group]]
- [[people/haohao-luo|Haohao Luo]] — [[companies/alibaba-group|Alibaba Group]]
- [[people/shen-li|Shen Li]] — [[companies/alibaba-group|Alibaba Group]]
- [[people/lu-yi|Lu Yi]] — [[companies/alibaba-group|Alibaba Group]]
- [[people/yi-yu|Yi Yu]] — [[companies/alibaba-group|Alibaba Group]]

**Year:** 2025 · **Domain:** computer science


## Research Context

**What's new:** This paper introduces AgentScope, a novel framework for building agentic applications that combines intrinsic knowledge with dynamic tool use, enhancing the capacity to address real-world tasks. The key novel element is the provision of unified interfaces and extensible modules for message, model, memory, and tool modules.

**Related in brain:** None, as no related pages were found in the brain.

**Knowledge gaps:** This paper assumes a certain level of understanding of agentic applications and LLM-based agent applications, which may not be covered in the brain. To fully evaluate this work, one would need to learn about the current state of agentic applications and their limitations.

**Explore next:** 
* The ReAct paradigm and its applications in agentic systems
* The integration of diverse LLM APIs in AgentScope
* The potential applications of AgentScope in real-world tasks and industries

*Generated 2026-05-22 by research-notes.py*

<!-- timeline -->

## Timeline

- **2026-05-21** ? Imported to GBrain and summarized