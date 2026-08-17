---
name: grill-me
description: Stress-test a plan, design, implementation approach, or project decision through relentless but useful questioning. Use when the user says "grill me", asks to be challenged, wants a plan pressure-tested, or needs every branch of a decision tree resolved before implementation.
---

# Grill Me

Interview the user until the plan is decision-complete.

## Workflow

1. **Explore first**: If a question can be answered from repo files, configs, schemas, docs, tests, or memory, inspect those instead of asking.
2. **State understanding**: State the current understanding in one tight paragraph.
3. **Ask one question**: Ask one high-impact question at a time.
4. **Recommend answer**: For each question, include the recommended answer and why it is the default.
5. **Order decisions**: Resolve dependent decisions in order. Do not jump to downstream choices before upstream choices are locked.
6. **Log decisions**: Keep a running decision log in the conversation.
7. **Complete scope**: Stop when goal, success criteria, scope, constraints, approach, interfaces, edge cases, tests, and rollout are all clear.

## Constraints

- Do not edit files by default. This skill is for interrogation and alignment.
- Do not ask discoverable questions. Search first.
- Do not ask low-value preference questions.
- Do not accept fuzzy words when a precise term would change implementation.
- Use full prose when clarity matters; brevity rule still removes filler.

## Output Expectations

- Ask one question per turn unless the user explicitly wants a batch.
- Include `Recommended answer:` after each question.
- When done, provide a concise decision summary ready for implementation.
