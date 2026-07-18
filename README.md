# Engineering Agent Team

A 15-role software engineering subagent team, installable as a plugin. `project-manager` is the orchestrator — talk to it (or just describe a task) and it delegates to the right specialist via the Task tool.

## Roster

| Role | Agent name | Model | Responsibility |
|---|---|---|---|
| Project Manager | `project-manager` | opus | Orchestrator: scopes, classifies risk, delegates, reconciles conflicts, reports status |
| System Design | `system-design` | opus | High-level architecture, component boundaries, tradeoffs |
| Architecture Engineer | `architecture-engineer` | opus | Detailed specs: schemas, interfaces, module boundaries, migration paths |
| API Design | `api-design` | sonnet | API contracts: endpoints, schemas, versioning, breaking-change classification |
| Codebase Researcher | `codebase-researcher` | sonnet | Traces how existing code works, assesses change blast radius |
| QA | `qa` | sonnet | Reviews deliverables against original requirements, pass/fail gate |
| Document Researcher | `document-researcher` | haiku | Gathers external docs, library references, prior art |
| Task Planner | `task-planner` | sonnet | Breaks specs into ordered, risk-tagged, dependency-aware tasks |
| Safe Refactor | `safe-refactor` | haiku | Behavior-preserving mechanical refactors only |
| Backend Developer | `backend-developer` | haiku | Server/API/data-layer implementation |
| Frontend Developer | `frontend-developer` | haiku | UI/client implementation |
| DevOps | `devops` | haiku | CI/CD, infra, deployment, rollback plans |
| Root Cause Analyst | `root-cause-analyst` | sonnet (escalates to opus) | Bug/incident investigation with regression-guard recommendations |
| Tester | `tester` | haiku | Writes and runs tests, owns the regression suite |
| Security Analyst | `security-analyst` | opus | Threat modeling, vulnerability review, blocking sign-off |

**Model note:** the original request specified "fable-5" for Project Manager and "opus 4.8" for several roles. Neither is a recognized Claude Code/Cowork model alias, so both were mapped to `opus`, the highest-capability tier available. If your environment has a custom alias configured for those exact names, edit the `model:` field in the relevant agent file.

## Install

This plugin is distributed as a `.plugin` file. Install it through Cowork's plugin installer, or manually unzip into a project's `.claude/` directory structure if using Claude Code directly. Once installed, agents are auto-discovered — no configuration needed.

## How it works

Every agent file carries a standardized **Handoff contract** (Requires / Produces / Hands off to / Done when) so work passes cleanly between roles instead of leaking context or silently dropping requirements. `project-manager` classifies each task's risk (LOW/MEDIUM/HIGH) up front — this determines which quality gates are mandatory.

### Execution flows

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

### Quality gates

- **GATE-0** (HIGH risk only): design-time security threat model, before any spec work
- **GATE-1**: tests executed and green, full suite, no weakened assertions
- **GATE-2**: QA pass against original requirements
- **GATE-3**: security sign-off, scoped, no unresolved critical/high findings

### Escalation rules

- QA can't explain a failure → `root-cause-analyst`
- Anything vulnerability-shaped → `security-analyst`
- Spec gap found mid-implementation → back to `architecture-engineer`/`api-design` via PM, never invented unilaterally
- An agent fails a task twice → PM escalates model tier, splits the task, or surfaces the blocker to the user — never a third silent retry

## Customizing

- Each agent's `tools:` line restricts what it can touch. Adjust per your workflow.
- Descriptions double as routing triggers for auto-suggestion — keep them specific if edited.
- `codebase-researcher` vs. `document-researcher`: former traces your own codebase, latter pulls external docs.
- `api-design` vs. `architecture-engineer`: former owns the request/response contract at the API boundary; latter owns internal module structure and data storage.
