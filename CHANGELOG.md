# Changelog

## 2.0.0 — Team restructure (breaking)

Roster shrinks from 15 roles to 12 and the team becomes self-contained and strictly sequential.

### Removed / merged
- **`task-planner` removed** — its task-breakdown and sequencing discipline is now part of
  `project-manager`, which does its own ordered, dependency-aware planning before dispatching.
- **`api-design` and `system-design` removed** — both are merged into a broadened
  **`architecture-engineer`**, which now spans the full design arc: high-level architecture and
  tradeoffs, API contracts, and implementable specs. Its tool access is the union of the three
  former roles (adds `WebSearch`/`WebFetch`).

### Dependencies
- **`superpowers` plugin dependency removed.** The team no longer depends on `superpowers`. The
  behaviors it provided are inlined directly into the affected role definitions: an
  "evidence before assertions" verification clause (the former `verification-before-completion`),
  a confirm-root-cause-before-fixing clause in `root-cause-analyst` (the former
  `systematic-debugging`), and structured-spec discipline in `architecture-engineer` (the former
  `writing-plans`). The former `dispatching-parallel-agents` skill was dropped outright, not
  inlined, because the team is now strictly sequential (below). `frontend-design` remains the only
  external plugin dependency.

### Orchestration
- **`project-manager` elevated** to the single top-level entry point with explicit directive
  authority — it decides and directs which specialist handles each task, in what order, and whether
  to split it. It also takes on secretary duties: tracking team-wide status, drafting communications
  on the user's behalf, and surfacing what's pending or blocked.
- **Strictly sequential dispatch.** All hand-offs are one agent at a time — `project-manager`
  dispatches a task, waits for its result, then decides the next. No parallel or background agent
  execution anywhere in the agents, skills, or workflow policy.
