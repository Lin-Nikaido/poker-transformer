---
name: designing-feature
description: Generates 2-3 implementation options for a new feature with structured pros/cons covering complexity, extensibility, testability, and alignment with existing patterns. Use after exploring the codebase and clarifying requirements.
---

# Designing Feature

Produces structured implementation options for a new feature.

**Input**: Issue summary (from `fetching-github-issue`) + context report (from `exploring-codebase`) + any user clarifications.

## Instructions

### Step 1: Identify Key Design Decisions

List decisions the implementation must resolve:

- Which layer owns the new logic? (apis / application / core / infrastructure)
- New registry entry, or extend an existing component?
- New ADK `Agent`, or a new tool on an existing agent?
- Async or sync? (always async for I/O)
- Does this require a database migration?

### Step 2: Generate Options

For each option:

```
### Option <N>: <Short Name>

**Approach**: <1-2 sentences>

**Files to create / modify**:
- `src/trust/<layer>/<file>.py` -- <change description>

**Pros**:
- <pro>

**Cons**:
- <con>

**Test strategy**:
- Unit: <what to mock, what to assert>
- Integration: <if needed>
```

### Step 3: Recommend

State which option you recommend and why. Do not leave the choice open-ended.

Present options and wait for user selection before proceeding to implementation planning.
