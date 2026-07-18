---
name: engineering-flows-and-gates
description: This skill should be used when sequencing multi-agent work (deciding which agent runs next and in what order), classifying a task's risk tier, deciding which quality gate applies before work can be considered done, or deciding where to escalate when something goes wrong. Primarily used by project-manager and task-planner when planning/dispatching, and by qa, security-analyst, and root-cause-analyst when deciding whether a gate is satisfied or where to route a finding.
version: 1.0.0
---

# Engineering flows and gates

The canonical reference for how work moves through this team: risk classification, the execution
flow for each kind of task, the quality gates that must pass before something is "done," and where
to escalate when it isn't going well. `project-manager` and `task-planner` should treat this as the
default sequencing unless the specific task clearly warrants a different order — deviate when it
makes sense, but know what you're deviating from.

## Risk classification (tag every task before delegating)

- **LOW** — docs, internal tooling, refactors with existing test coverage.
- **MEDIUM** — feature code, schema changes.
- **HIGH** — auth, payments, data migration, production infra, external API surface.

HIGH always gets `security-analyst` review and never skips `qa`. MEDIUM skips security review only
if it demonstrably touches none of the sensitive surfaces above. LOW may go straight from
implementer to `tester`.

## Execution flows

**New feature (standard):**
```
codebase-researcher || document-researcher → system-design
  → architecture-engineer || api-design → task-planner
  → [backend-developer | frontend-developer | devops] (parallel per plan)
  → tester → qa → security-analyst (HIGH always, MEDIUM if sensitive)
  → project-manager (final report)
```

**Bug fix:**
```
root-cause-analyst → developer agent → tester (regression guard) → qa
```

**Production incident (urgent):**
```
devops (mitigate) || root-cause-analyst (diagnose, max rigor)
  → developer agent → tester → qa → security-analyst if vuln-shaped
```

**Refactor/cleanup (LOW risk only):**
```
codebase-researcher (blast radius, if uncertain) → safe-refactor
  → tester (if weak coverage) → qa (light pass)
```

**API change (existing surface):**
```
codebase-researcher → api-design (breaking-change classification)
  → backend-developer || frontend-developer → tester → qa → security-analyst if access model changes
```

**Security audit:**
```
codebase-researcher (map attack surface) → security-analyst (findings)
  → fix per finding via bug-fix flow → security-analyst re-verifies
```

When `task-planner` marks a batch of tasks within one of these flows as independent (e.g. the
parallel `backend-developer | frontend-developer | devops` step above), `project-manager` should
issue all of that batch's `Task` calls in the same turn rather than round-tripping each one
serially — Claude Code supports multiple `Task` invocations per assistant turn, and there is no
dependency forcing them apart.

## Quality gates

- **GATE-0** (HIGH risk only): design-time security threat model, before any spec work.
- **GATE-1**: tests executed and green, full suite, no weakened assertions.
- **GATE-2**: QA pass against original requirements.
- **GATE-3**: security sign-off, scoped, no unresolved critical/high findings.

## Model-tier escalation

Routine investigation runs at the agent's default model tier (e.g. `root-cause-analyst` on
sonnet). Escalate to a higher tier — reasoning at max rigor, or handing to an opus-tier agent —
for production incidents, data-loss scenarios, or anything security-adjacent. A bug that turns out
to be vulnerability-shaped goes to `security-analyst`, not a higher-effort pass by the same agent.

## Escalation rules

- QA can't explain a failure → `root-cause-analyst`.
- Anything vulnerability-shaped → `security-analyst`.
- Spec gap found mid-implementation → back to `architecture-engineer`/`api-design` via
  `project-manager`, never invented unilaterally (see `agent-handoff-protocol` for how to flag this
  in a handoff packet).
- An agent fails a task twice → `project-manager` escalates model tier, splits the task via
  `task-planner`, or surfaces the blocker to the user — never a third silent retry.
