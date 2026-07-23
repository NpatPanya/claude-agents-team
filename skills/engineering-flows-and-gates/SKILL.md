---
name: engineering-flows-and-gates
description: This skill should be used when sequencing multi-agent work, classifying a task's risk tier and reasoning effort, selecting quality gates, or deciding where to escalate when work goes wrong. Primarily used by project-manager, and by qa, security-analyst, and root-cause-analyst when deciding whether a gate is satisfied.
---

# Engineering flows and gates

This is the canonical workflow policy. project-manager classifies every task before
delegating it, then chooses the smallest team that can satisfy the required gates.

## Deterministic task classification

Classify impact risk and reasoning effort separately; a low-impact task can still require
deep reasoning, and a high-impact task can be mechanically simple.

Risk is determined by the highest matching explicit signal:

- HIGH: authentication or authorization, payments, PII or personal data, secrets or
  credentials, production infrastructure, data/database migration, public or external API,
  breaking API, security work, destructive data changes, or an incident.
- MEDIUM: feature code, schema/database changes that are not migrations, APIs that are
  neither public nor breaking, integrations, background jobs, business logic, bugs, dependency
  changes, or configuration changes.
- LOW: documentation, internal tooling, formatting, and explicitly behavior-preserving
  refactors with existing coverage.

Evaluate HIGH before MEDIUM. If no signal matches, classify as LOW only when the scope is
explicitly narrow and reversible; otherwise classify as MEDIUM and ask project-manager to
bound the work. Record the matching signal in the handoff packet.

Reasoning effort is a separate LOW/MEDIUM/HIGH label. Raise it for ambiguity, cross-cutting
changes, distributed/concurrent behavior, migrations, architecture tradeoffs, multiple services,
or unknown behavior. Do not use effort to waive a risk gate, and do not use risk as a proxy for
how difficult the reasoning is.

## Delegation policy

LOW means the main agent works alone: perform minimal focused inspection, make the smallest
safe change, and run one relevant verification. Do not dispatch a sub-agent.

MEDIUM permits one focused sub-agent only when its checkable output reduces total effort. The
main agent remains accountable. Dispatch that sub-agent on its own and wait for its result — never
run agents in parallel or in the background, even for independent read-only checks. Stop once the
focused output is consumed and the verification is green.

HIGH requires the complete gated flow, targeted specialists, final QA/security review, and a
recorded human review. The number of specialists is driven by the attack surface and dependencies,
not by a default team size. Every hand-off is still strictly sequential — one agent at a time, its
result in hand before the next is dispatched.

## Execution flows

HIGH-risk work (required order):

~~~text
research -> security-analyst (GATE-0 threat model) -> architecture-engineer
  -> implementation -> tester -> QA -> security-analyst (GATE-3)
~~~

GATE-0 must pass before specification or design begins. The implementation stage may use targeted
backend, frontend, devops, or other specialists, but only after the plan is approved. GATE-3 is a
scoped security sign-off after QA and cannot be replaced by a generic test result.

LOW/MEDIUM new feature:

~~~text
focused research (only if needed) -> architecture-engineer
  -> implementation -> tester -> QA -> project-manager
~~~

Add security review for MEDIUM work if it touches a sensitive surface. A genuine architecture
decision upgrades the task to HIGH.

Bug fix: root-cause-analyst -> developer -> tester -> QA.

Production incident: devops (mitigate) -> root-cause-analyst (diagnose) -> developer -> tester -> QA,
then security review if vulnerability-shaped. Mitigate first to stop the bleeding, then diagnose —
sequentially, not concurrently. Use the HIGH model tier for unclear or data-integrity incidents.

LOW refactor: codebase-researcher (only if uncertain) -> safe-refactor -> tester (if coverage
is weak) -> light QA.

Existing API change: codebase-researcher -> architecture-engineer -> implementation -> tester -> QA,
then security review if the access model changes. A breaking or public API change is HIGH.

Security audit: codebase-researcher -> security-analyst (findings) -> fix per bug-fix flow
-> security-analyst re-verifies.

## Quality gates

- GATE-0 (HIGH only): design-time threat model, before specification/design.
- GATE-1: the full relevant test suite is executed and green; assertions are not weakened.
- GATE-2: QA checks the implementation against the original requirements.
- GATE-3 (HIGH only): security sign-off with no unresolved critical/high findings.

## Stop, retry, and escalation rules

- Stop investigating when the requested question is answered with verified evidence, the bounded
  inspection found no more relevant signal, or the next action would repeat an existing check.
- Retry a failed task at most twice. After two failed attempts, escalate to project-manager, who
  must raise the model tier, split the task, or surface the blocker to the user. Never perform a
  third silent retry.
- A missing input, contradiction, or material ambiguity is a needs_clarification handoff; do not
  invent a fact to continue.
- Any destructive action requires explicit scope confirmation, a recoverable approach where
  practical, and escalation/approval before execution. Resolve exact targets before acting.
- Prefer the smallest safe fix that satisfies the acceptance criteria. Do not broaden a fix to
  clean up adjacent code; record follow-up work separately.

## Durable artifacts

Read existing findings, threat models, designs, specs, and test reports from their recorded paths before
investigating again. codebase-researcher, document-researcher, and architecture-engineer should
write multi-file findings/design briefs to docs/ (or an agreed location). Handoffs reference
those artifacts instead of rescanning or restating them.
