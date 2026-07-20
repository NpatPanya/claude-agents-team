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
devops (mitigate) || root-cause-analyst (diagnose, dispatched with model: opus override)
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

## Model and effort selection

Every agent carries a fixed `effort:` value in its own frontmatter (its default reasoning depth)
alongside its default `model:` tier. `effort` cannot be changed per dispatch — only `model` can,
via a per-call override on the Task tool that takes precedence over the agent's frontmatter
default. That makes `model` the only lever available at dispatch time, and it does **not** raise
the agent's effort — an upgraded model still runs at that role's frozen frontmatter effort.

Apply this table when dispatching, keyed by the role's own default tier and the task's risk
classification (above):

| Role's default tier | LOW risk | MEDIUM risk | HIGH risk |
|---|---|---|---|
| haiku (backend/frontend/devops/safe-refactor/tester/document-researcher) | haiku | haiku (→ sonnet if unusually logic-dense or ambiguous) | **sonnet — mandatory** |
| sonnet (qa/codebase-researcher/api-design/task-planner/root-cause-analyst) | haiku OK for a narrow/mechanical instance | sonnet | **opus** |
| opus (project-manager/system-design/architecture-engineer/security-analyst) | opus — never downgrade | opus | opus |

- **HIGH-risk implementation is never left on a haiku-tier agent** — dispatch with the override
  (e.g. `root-cause-analyst` investigating a production incident or data-integrity issue goes out
  with `model: opus`, per the sonnet→HIGH cell above).
- If a model-upgraded role still underperforms on HIGH-risk work, the fix is raising that role's
  frontmatter `effort` permanently and flagging it to the user — there is no per-dispatch effort
  escape hatch.
- opus-tier roles don't get cost relief by downgrading — their value is judgment on high-stakes
  decisions, not throughput. The lever there is whether to invoke the heavy role at all (see
  "right-size the team" in `project-manager`), not which tier to run it at.
- This table is the proactive front half of the escalation rule below — it front-loads the tier
  decision instead of waiting for two failed attempts. A bug that turns out to be
  vulnerability-shaped still goes to `security-analyst` outright, not a model-upgraded pass by the
  same agent.

## Escalation rules

- QA can't explain a failure → `root-cause-analyst`.
- Anything vulnerability-shaped → `security-analyst`.
- Spec gap found mid-implementation → back to `architecture-engineer`/`api-design` via
  `project-manager`, never invented unilaterally (see `agent-handoff-protocol` for how to flag this
  in a handoff packet).
- An agent fails a task twice → `project-manager` escalates model tier, splits the task via
  `task-planner`, or surfaces the blocker to the user — never a third silent retry.
