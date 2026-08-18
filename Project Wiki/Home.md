---
title: Clinical AI Kit — Wiki Home
type: dashboard
status: active
updated: 2026-07-05
tags:
  - home
  - index
---

# Clinical AI Kit

Clinician-facing AI platform built on Google ADK: specialist agent pipelines for image extraction, patient Q&A, and database intelligence, gated by clinician review and privacy-aware security controls. Capstone project for Kaggle's 5-Day AI Agents Intensive Course.

> [!info] Living wiki
> This vault documents only what is built in the repository. Pages in `_generated/` are machine-owned and rewritten by `scripts/sync_wiki.py` on every work session (Stop hook). Hand-edit everything else.

## Overview

- [[Problem and Solution]] — what Clinical AI Kit does and why
- [[Course Concepts Map]] — Days 1a–5b coverage and rubric alignment

## Architecture & Agent Workflows

- [[System Overview]] — the four-layer stack
- [[Agent Architecture]] — every agent, tier, and tool
- [[Model Registry]] — the 3-tier Gemini registry
- [[Module Reference]] — every Python module and its purpose
- [[Module Dependency Graph]] — auto-regenerated import graph
- [[Architecture Board.canvas|Architecture Board]] — visual system map
- [[End-to-End Request Flow]] — request lifecycle sequence
- [[Image Extraction Pipeline]] — 7-specialist extraction workflow with a nested validation loop
- [[Patient QA Pipeline]] — 8-specialist grounded Q&A workflow
- [[DB Intelligence Pipeline]] — 6-specialist NL-to-SQL workflow
- [[Human-in-the-Loop Approval]] — human verification gates
- [[Development Workflow]] — local build and sync cycles
- [[Deployment Pipeline]] — production topology and engines

## Security & Memory

- [[Security Layers]] — 3-layer callbacks + clinical guards
- [[Memory Layers]] — 4-layer memory with PII/PHI governance

## Operations

- [[Clinical App]] — FastAPI product server + React frontend
- [[REST API and Developer Console]] — versioned REST APIs, styled Swagger, and interactive playground console
- [[MCP and A2A]] — interoperability surfaces
- [[Testing and Eval]] — pytest suite + ADK evaluation
- [[Observability]] — logs, traces, clinical audit
- [[Deployment]] — Cloud Run / Agent Engine / GKE

## Harness

- [[Claude Harness]] — rules, skills, hooks, memory, sync scripts

## Machine-Generated (auto-updated)

- [[Architecture Views.base|Architecture Views Base]] - active architecture, operations, and process notes

- [[Module Inventory]] · [[Test Inventory]] · [[Harness Index]] · [[Changelog]] · [[Drift Report]]
