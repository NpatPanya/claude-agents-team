# Engineering Agent Team

A 15-role software engineering subagent team, installable as a plugin, organized into six
departments like an engineering org. `project-manager` is the orchestrator — talk to it (or just
describe a task) and it delegates to the right specialist via the Task tool.

## Roster

### Orchestration
| Role | Agent name | Model | Effort | Responsibility |
|---|---|---|---|---|
| Project Manager | `project-manager` | opus | high | Orchestrator: scopes, classifies risk, delegates, reconciles conflicts, reports status |
| Task Planner | `task-planner` | sonnet | medium | Breaks specs into ordered, risk-tagged, dependency-aware tasks |

### Architecture & Design
| Role | Agent name | Model | Effort | Responsibility |
|---|---|---|---|---|
| System Design | `system-design` | opus | high | High-level architecture, component boundaries, tradeoffs |
| Architecture Engineer | `architecture-engineer` | opus | high | Detailed specs: schemas, interfaces, module boundaries, migration paths |
| API Design | `api-design` | sonnet | medium | API contracts: endpoints, schemas, versioning, breaking-change classification |

### Research & Intelligence
| Role | Agent name | Model | Effort | Responsibility |
|---|---|---|---|---|
| Codebase Researcher | `codebase-researcher` | sonnet | medium | Traces how existing code works, assesses change blast radius |
| Document Researcher | `document-researcher` | haiku | low | Gathers external docs, library references, prior art |

### Delivery Engineering
| Role | Agent name | Model | Effort | Responsibility |
|---|---|---|---|---|
| Backend Developer | `backend-developer` | haiku | medium | Server/API/data-layer implementation |
| Frontend Developer | `frontend-developer` | haiku | medium | UI/client implementation |
| DevOps | `devops` | haiku | medium | CI/CD, infra, deployment, rollback plans |
| Safe Refactor | `safe-refactor` | haiku | low | Behavior-preserving mechanical refactors only |

### Quality & Reliability
| Role | Agent name | Model | Effort | Responsibility |
|---|---|---|---|---|
| QA | `qa` | sonnet | high | Reviews deliverables against original requirements, pass/fail gate |
| Tester | `tester` | haiku | medium | Writes and runs tests, owns the regression suite |
| Root Cause Analyst | `root-cause-analyst` | sonnet (dispatched with `model: opus` override for incidents) | high | Bug/incident investigation with regression-guard recommendations |

### Security
| Role | Agent name | Model | Effort | Responsibility |
|---|---|---|---|---|
| Security Analyst | `security-analyst` | opus | high | Threat modeling, vulnerability review, blocking sign-off |

**Model note:** the original request specified "fable-5" for Project Manager and "opus 4.8" for several roles. Neither is a recognized Claude Code/Cowork model alias, so both were mapped to `opus`, the highest-capability tier available. If your environment has a custom alias configured for those exact names, edit the `model:` field in the relevant agent file.

## Install

This plugin is distributed as a `.plugin` file. Install it through Cowork's plugin installer, or manually unzip into a project's `.claude/` directory structure if using Claude Code directly. Once installed, agents and skills are auto-discovered — no configuration needed. Agents live under `agents/<department>/`; discovery is recursive, so the department subdirectories are purely organizational and don't need declaring anywhere.

## Skills

Two plugin skills hold the knowledge that used to be duplicated across agent files or scattered in this README, loaded on demand rather than baked into every agent's context:

- **`agent-handoff-protocol`** — the structured handoff-packet format every agent uses to dispatch or report back work (replaces free-form delegation prose), plus the canonical "flag a gap, don't invent" rule. Loaded on nearly every turn that ends in a handoff.
- **`engineering-flows-and-gates`** — the execution flow for each kind of task (with risk-tiered variants — e.g. new-feature work skips `system-design` unless it's HIGH risk or a genuine architecture decision), the risk-classification rubric, the model-override table, the quality gates, and the escalation rules. Loaded mainly by `project-manager`/`task-planner` when sequencing, and by `qa`/`security-analyst`/`root-cause-analyst` when checking which gate or escalation applies.

`codebase-researcher`, `document-researcher`, and `system-design` can write their findings/design brief to a durable file instead of only returning it as packet prose — downstream agents Read it once instead of a paraphrase degrading through relays. See "Durable artifacts over re-derivation" in `engineering-flows-and-gates`.

## How it works

Every agent's handoff — dispatching work or reporting it back — uses the packet format defined in `agent-handoff-protocol`:

```yaml
handoff:
  objective: <one sentence>
  from: <agent-name | "user">
  to: <agent-name>
  status: dispatched | complete | blocked | needs_clarification | rejected
  risk: LOW | MEDIUM | HIGH
  inputs: [<file path or inline reference>]
  constraints: [<explicit "do NOT" boundary>]
  produced_artifacts: [{path, description}]
  definition_of_done: <concrete, checkable criterion>
  notes: <deviations, open questions, escalation target if blocked>
```

`project-manager` fills this in to delegate; the receiving agent fills in the same shape to report
back — one vocabulary in both directions, so a handoff is *forwarded* rather than re-composed at
every relay. `project-manager` classifies each task's risk (LOW/MEDIUM/HIGH) up front per
`engineering-flows-and-gates`, which determines which quality gates are mandatory.

### Execution flows, quality gates, and escalation

The 6 execution flows (feature / bugfix / incident / refactor / API-change / security-audit), the
4 quality gates (GATE-0 through GATE-3), and the escalation rules live in
`skills/engineering-flows-and-gates/SKILL.md` — that's the canonical reference; this README doesn't
restate it. In short: `project-manager` and `task-planner` sequence work against those flows by
default, `qa`/`security-analyst` gate work against those checkpoints, and any agent that hits an
unresolvable gap flags it back rather than guessing (per `agent-handoff-protocol`), routing through
whichever specialist the situation calls for.

## Customizing

- Each agent's `tools:` line restricts what it can touch. Adjust per your workflow.
- Descriptions double as routing triggers for auto-suggestion — keep them specific if edited.
- `codebase-researcher` vs. `document-researcher`: former traces your own codebase, latter pulls external docs.
- `api-design` vs. `architecture-engineer`: former owns the request/response contract at the API boundary; latter owns internal module structure and data storage.
- Department subdirectories under `agents/` are organizational only — moving a file between departments never changes its `name:` frontmatter, so it never breaks how the agent is invoked or `@`-mentioned.
- `model:` can be overridden per dispatch (the Task tool's per-call `model` param takes precedence over the frontmatter default) — `project-manager`/`task-planner` use this per the model-override table in `engineering-flows-and-gates` to upgrade a task's model tier for higher risk. `effort:` cannot be overridden per dispatch; it's a fixed default you tune once in the agent's own file.
