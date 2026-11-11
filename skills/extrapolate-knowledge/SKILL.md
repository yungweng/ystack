---
name: extrapolate-knowledge
description: Extrapolate from what the user already knows in their current endeavor to principles, transferable patterns, predictions, and next moves. Use when the user says "extrapolate", "what follows from this", "what does this imply", "where does this lead", "connect the dots", or wants to turn scattered findings, lessons, or results into deeper insight.
---

# Extrapolate Knowledge

Goal: take the **known** (facts, results, lessons, decisions in the current endeavor) and push it one or two steps further than the user has: into principles, analogies, predictions, and moves. Every extrapolation is anchored to a named piece of evidence from the endeavor.

## 1. Inventory the known

Gather from the conversation, named files or links, and, in a repo, README, AGENTS.md/CLAUDE.md, recent git log, notes, and TODOs.

List 5 to 15 **knowns** as short, numbered statements, each tagged `observed` (seen in data, code, or results) or `believed` (assumption, opinion, secondhand). Add one line stating the goal and current stage. If the goal is unclear, ask one question and stop.

Done when every claim you will build on appears in this list.

## 2. Extrapolate along each axis

For each axis, derive what follows from the knowns. Skip an axis that yields nothing real.

- **Principle**: what general rule explains several knowns at once? Name the rule and the knowns it covers.
- **Transfer**: which other field solved a structurally identical problem, and what did it learn that applies here? Name the field and the mapping.
- **Trajectory**: if the current trend continues (growth, cost, usage, complexity, team size), what happens in 3, 6, 12 months? Where does it bend or break?
- **Second order**: what does a known enable or cause downstream that nobody has planned for?
- **Inversion**: what would have to be true for the opposite conclusion to hold? Does any known already point there?
- **Edge of validity**: where does each principle stop holding (scale, context, users, time)?
- **Leverage**: which single known, if exploited further, pays off most?

When an extrapolation depends on current external facts (prices, laws, APIs, versions), verify with available tools or mark it `unverified`.

## 3. Grade and filter

Give each extrapolation a confidence: `high` (follows directly from observed knowns), `medium` (needs one reasonable assumption), `speculative` (a leap worth testing). Keep an extrapolation only if it is new to the user, changes a decision or expectation, and has a cheap test. Keep 5 to 10.

## 4. Report

```
## Extrapolation: <endeavor in a few words>

**Knowns used:** <numbered list from step 1, with observed/believed tags>

1. **<Extrapolated claim>** (axis: <axis>, confidence: high|medium|speculative)
   From: <known numbers it rests on>
   Implies: <consequence for this endeavor>
   Test: <cheapest way to confirm or kill it>

...

### Emerging model
<3-5 sentences: the compact mental model of the endeavor these extrapolations add up to>

### Predictions to track
- <falsifiable prediction, with the signal and date to check it>
```

Close with the one extrapolation to act on first and why.

## Rules

- Anchor every claim to knowns by number; a claim without an anchor goes in "speculative" or out.
- Keep `observed` and `believed` knowns distinct when grading confidence.
- Stay with this endeavor's specifics; each item names a concrete thing in it.
- Report insight; implement only when asked.
