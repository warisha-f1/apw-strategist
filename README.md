# APW F1 Strategist
An AI-powered Race Engineering platform that utilizes a Multi-Agent System (MAS) to convert raw telemetry into actionable race strategies.

# Project Overview
The APW F1 Strategist acts as a virtual pit wall. It uses LLM-powered agents to monitor live or historical telemetry, identify performance gaps via Time Delta analysis, and recommend optimal pit-stop windows and tire management.

# Architecture & Capstone Features
Multi-Agent System: Includes a Strategist Agent (LLM Orchestrator) and a Data Agent (Python Tool) communicating via A2A Protocol.

Context Engineering: Implements context compaction to feed high-frequency telemetry data into the LLM without exceeding token limits.

Memory Bank: Utilizes long-term memory to store driver-specific performance history for predictive modeling.

Observability: Integrated Logging and Tracing to provide transparency into the agent's decision-making process.