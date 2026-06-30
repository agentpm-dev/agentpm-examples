---
name: incident-handoff-checklist
description: Operational handoff checklist for incident updates, shift changes, and follow-through tracking.
---

# Incident Handoff Checklist

Use this Skill when an agent needs to leave behind a clear operational state for another person or another agent.

## When to use this Skill

Reach for this checklist when:
- an incident is still active and ownership may change
- the current investigation window is ending
- a status update needs to summarize what is known, what is blocked, and what should happen next
- the agent has partial findings but should not keep exploring without human review

Do not use this Skill for a polished incident retrospective. It is for live operational continuity.

## Required output

Every handoff should make these seven points explicit:

1. Current severity and customer impact.
2. Current owner.
3. What has already been checked.
4. What evidence matters most right now.
5. What is still unknown.
6. The single highest-priority next step.
7. Whether escalation, rollback, or stakeholder communication is pending.

## Writing rules

- Prefer short bullets over long paragraphs.
- Do not bury the current risk.
- If a decision is blocked by missing evidence, say exactly what evidence is missing.
- If the agent changed its confidence level during the investigation, say why.
- If there is no clear owner, say that explicitly instead of implying one.

## Suggested structure

Use the outline in [references/handoff-template.md](references/handoff-template.md) as the default shape.

## Failure cases to avoid

- Do not end with "monitoring" unless monitoring has a concrete owner and trigger.
- Do not say "everything looks fine" if any customer impact is still unknown.
- Do not mark an item as complete if it was only proposed.
- Do not hide unresolved questions inside a generic notes section.
