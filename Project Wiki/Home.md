---
title: Nexus Clinical AI Command Center — Wiki Home
type: dashboard
status: active
updated: 2026-07-04
tags:
  - home
  - index
---

# Nexus Clinical AI Command Center

Clinician-facing AI platform built on Google ADK: specialist agent pipelines for image extraction, patient Q&A, and database intelligence, gated by clinician review and HIPAA-aligned security. Capstone project for Kaggle's 5-Day AI Agents Intensive Course.

> [!info] Living wiki
> This vault documents only what is built in the repository. Pages in `_generated/` are machine-owned and rewritten by `scripts/sync_wiki.py` on every work session (Stop hook). Hand-edit everything else.

## Overview

- [[Problem & Solution]] — what Nexus does and why
- [[Course Concepts Map]] — Days 1a–5b coverage and rubric alignment

## Architecture

- [[System Overview]] — the four-layer stack
- [[Agent Architecture]] — every agent, tier, and tool
- [[Model Registry]] — the 3-tier Gemini registry
- [[Module Reference]] — every Python module and its purpose
- [[Module Dependency Graph]] — auto-regenerated import graph
- [[Architecture Board.canvas|Architecture Board]] — visual system map

## Processes (BPMN-style)

- [[End-to-End Request Flow]]
- [[Image Extraction Pipeline]]
- [[Patient QA Pipeline]]
- [[DB Intelligence Pipeline]]
- [[Human-in-the-Loop Approval]]
- [[Development Workflow]]
- [[Deployment Pipeline]]

## Security & Memory

- [[Security Layers]] — 3-layer callbacks + clinical guards
- [[Memory Layers]] — 4-layer memory with PII/PHI governance

## Operations

- [[Clinical App]] — FastAPI product server + React frontend
- [[MCP and A2A]] — interoperability surfaces
- [[Testing & Eval]] — pytest suite + ADK evaluation
- [[Observability]] — logs, traces, clinical audit
- [[Deployment]] — Cloud Run / Agent Engine / GKE

## Harness

- [[Claude Harness]] — rules, skills, hooks, memory, sync scripts

## Machine-Generated (auto-updated)

- [[Module Inventory]] · [[Test Inventory]] · [[Harness Index]] · [[Changelog]] · [[Drift Report]]
