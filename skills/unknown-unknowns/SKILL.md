---
name: unknown-unknowns
description: Surface the unknown unknowns in the user's current endeavor, meaning risks, constraints, domain knowledge, and questions they have not thought to ask. Use when the user says "unknown unknowns", "what am I missing", "blind spots", "what don't I know", or starts something unfamiliar (new domain, stack, market, legal area, migration, launch).
---

# Unknown Unknowns

Goal: tell the user what they don't know they don't know. Do not restate what they already covered. Every item must be specific to their situation, not generic advice.

## 1. Establish the endeavor

Build a picture from the available context before asking anything:

- The conversation so far.
- If in a repo: README, AGENTS.md/CLAUDE.md, package manifests, config, CI, recent git log, open TODOs.
- Any files or links the user named.

Write down in 2 to 4 lines: the goal, the current stage, the user's apparent expertise, and what they have already considered. If the goal is still unclear, ask **one** question and stop.

## 2. Sweep the lenses

Go through each lens and ask: "What would an experienced practitioner in this exact field know here that a smart newcomer would not?" Skip lenses that yield nothing real.

- **Domain knowledge**: jargon, conventions, established practice, prior art, existing solutions the user may be reinventing.
- **Hidden constraints**: legal, regulatory, licensing, privacy (e.g. GDPR), tax, contracts, platform policies, accessibility.
- **Scale and time**: what breaks at 10x/100x, over months, at the first migration, at the first team handover.
- **Operations**: deployment, monitoring, backups, secrets, cost at scale, on-call, vendor lock-in, support load.
- **Security and abuse**: attackers, misuse, fraud, spam, data leaks.
- **People**: stakeholders not yet consulted, users who behave differently than assumed, dependencies on a single person.
- **Second-order effects**: what success causes, what a failure mode cascades into, irreversible decisions hiding as small ones.
- **Assumptions**: premises the plan silently depends on. Name each one and how to test it cheaply.
- **Tooling and ecosystem**: deprecations, version churn, known gotchas of the chosen tools, better-suited tools.

When a claim depends on current facts (laws, prices, API behavior, versions), verify with available tools or mark it as unverified.

## 3. Filter

Keep an item only if all are true:

- It is plausibly unknown to this user, given what they said and did.
- It would change a decision, cost, timeline, or risk if known.
- It is concrete enough to act on.

Drop filler. 5 to 10 strong items beat 30 weak ones.

## 4. Report

Order by impact (consequence × likelihood), highest first. Format:

```
## Unknown unknowns: <endeavor in a few words>

**Assumed context:** <the 2-4 line picture from step 1>

1. **<Short title>** (impact: high|medium|low)
   Why it matters: <consequence for this specific endeavor>
   How to find out / de-risk: <cheapest concrete next step>

...

### Questions worth asking
- <questions the user should put to an expert, stakeholder, or themselves>

### Where to learn more
- <specific sources: official docs, standards, communities, the search term an expert would use>
```

Close with the single item to address first and why.

## Rules

- Be specific. "Consider security" is useless; "Your webhook endpoint accepts unsigned payloads, so anyone can forge orders" is useful.
- Separate verified facts from inference.
- Don't lecture about things the user clearly already handles.
- Don't start implementing fixes unless asked.
