# Engineering Agent Team

A 12-role software engineering subagent team, installable as a plugin, organized into six
departments like an engineering org. `project-manager` sits at the top and is the single entry
point — talk to it (or just describe a task) and it decides which specialist handles each piece,
dispatching them via the Task tool **strictly one at a time** (never in parallel or in the
background). It also acts as the team's secretary: tracking status, drafting communications, and
surfacing what's pending or blocked.

## Roster

### Orchestration
| Role | Agent name | Model | Effort | Responsibility |
|---|---|---|---|---|
| Project Manager | `project-manager` | opus | high | Top-level orchestrator & secretary: sole entry point; scopes, classifies risk, breaks work into ordered dependency-aware tasks, dispatches specialists one at a time, reconciles conflicts, tracks status, drafts communications |

### Architecture & Design
| Role | Agent name | Model | Effort | Responsibility |
|---|---|---|---|---|
| Architecture Engineer | `architecture-engineer` | opus | high | Technical design across the full arc: high-level architecture and tradeoffs, API contracts (endpoints, schemas, versioning, breaking-change classification), data models, module boundaries, migration paths, and implementable specs |

### Research & Intelligence
| Role | Agent name | Model | Effort | Responsibility |
|---|---|---|---|---|
| Codebase Researcher | `codebase-researcher` | sonnet | medium | Traces how existing code works, assesses change blast radius |
| Document Researcher | `document-researcher` | haiku | low | Gathers external docs, library references, prior art |

### Delivery Engineering
| Role | Agent name | Model | Effort | Responsibility |
|---|---|---|---|---|
| Backend Developer | `backend-developer` | sonnet | medium | Server/API/data-layer implementation |
| Frontend Developer | `frontend-developer` | sonnet | medium | UI/client implementation |
| DevOps | `devops` | sonnet | medium | CI/CD, infra, deployment, rollback plans |
| Safe Refactor | `safe-refactor` | haiku | low | Behavior-preserving mechanical refactors only |

### Quality & Reliability
| Role | Agent name | Model | Effort | Responsibility |
|---|---|---|---|---|
| QA | `qa` | sonnet | high | Reviews deliverables against original requirements, pass/fail gate |
| Tester | `tester` | sonnet | medium | Writes and runs tests, owns the regression suite |
| Root Cause Analyst | `root-cause-analyst` | sonnet (dispatched with `model: opus` override for incidents) | high | Bug/incident investigation with regression-guard recommendations |

### Security
| Role | Agent name | Model | Effort | Responsibility |
|---|---|---|---|---|
| Security Analyst | `security-analyst` | opus | high | Threat modeling, vulnerability review, blocking sign-off |

**Model note:** the original request specified "fable-5" for Project Manager and "opus 4.8" for several roles. Neither is a recognized Claude Code/Cowork model alias, so both were mapped to `opus`, the highest-capability tier available. If your environment has a custom alias configured for those exact names, edit the `model:` field in the relevant agent file.

## Install

This plugin is distributed as a `.plugin` file. Install it through Cowork's plugin installer, or manually unzip into a project's `.claude/` directory structure if using Claude Code directly. Once installed, agents and skills are auto-discovered — no configuration needed. Agents live under `agents/<department>/`; discovery is recursive, so the department subdirectories are purely organizational and don't need declaring anywhere.

## Skills

Two plugin skills hold the knowledge that used to be duplicated across agent files or scattered in this README:

- **`agent-handoff-protocol`** — the structured handoff-packet format every agent uses to dispatch or report back work (replaces free-form delegation prose), plus the canonical "flag a gap, don't invent" rule. Preloaded into all 12 agents.
- **`engineering-flows-and-gates`** — the execution flow for each kind of task (with risk-tiered variants — e.g. new-feature work gets a lighter `architecture-engineer` spec unless it's HIGH risk or a genuine architecture decision warranting a full design brief), the risk-classification rubric, the delegation and model-tier policy, the quality gates, and the escalation rules. Preloaded into `project-manager` (sequencing) and `qa`/`security-analyst`/`root-cause-analyst` (gates and escalation).

### Per-agent skill assignments

Skills are **preloaded** via each agent's `skills:` frontmatter — the full skill text is injected at
startup, so an agent applies its methodology without having to discover or invoke anything. No agent
lists `Skill` in `tools:`, which means each one is scoped to exactly the skills below and cannot
reach anything else.

| Agent | Preloaded skills (beyond `agent-handoff-protocol`, which all 12 get) |
|---|---|
| `project-manager` | `engineering-flows-and-gates` |
| `qa` | `engineering-flows-and-gates` |
| `root-cause-analyst` | `engineering-flows-and-gates` |
| `security-analyst` | `engineering-flows-and-gates` |
| `frontend-developer` | `frontend-design:frontend-design` |
| `architecture-engineer`, `backend-developer`, `devops`, `safe-refactor`, `tester`, `codebase-researcher`, `document-researcher` | *(none — self-contained on the shared `agt:` skills)* |

`tester` is deliberately test-*after* — it writes and runs tests against already-implemented code, not
test-first — a workflow choice, not an oversight.

> **Dependency:** the only external skill assignment is `frontend-design:frontend-design` (on
> `frontend-developer`), which requires the `frontend-design` plugin. It's declared in
> `.claude-plugin/plugin.json` (`dependencies`), so Claude Code installs it alongside `agt`. If it's
> missing at runtime, Claude Code skips that entry and logs a warning to the debug log — the agent still
> runs, just without the preloaded design methodology. `scripts/validate_repo.py` rejects any external
> skill reference whose plugin isn't declared there, so a new external dependency can't be added to a
> `skills:` block without also declaring it. Every other role is fully self-contained on the two shared
> `agt:` skills, with its verification, debugging, and planning discipline written directly into the role
> definition.

`codebase-researcher`, `document-researcher`, and `architecture-engineer` can write their findings/design brief to a durable file instead of only returning it as packet prose — downstream agents Read it once instead of a paraphrase degrading through relays. See "Durable artifacts over re-derivation" in `engineering-flows-and-gates`.

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
`engineering-flows-and-gates`, which determines which quality gates are mandatory. Hand-offs are
**strictly sequential**: `project-manager` dispatches one agent, waits for its packet, then decides
the next — no agent runs in parallel with another or as a background task.

### Execution flows, quality gates, and escalation

The 6 execution flows (feature / bugfix / incident / refactor / API-change / security-audit), the
4 quality gates (GATE-0 through GATE-3), and the escalation rules live in
`skills/engineering-flows-and-gates/SKILL.md` — that's the canonical reference; this README doesn't
restate it. In short: `project-manager` sequences work against those flows by
default, `qa`/`security-analyst` gate work against those checkpoints, and any agent that hits an
unresolvable gap flags it back rather than guessing (per `agent-handoff-protocol`), routing through
whichever specialist the situation calls for.

## Customizing

- Each agent's `tools:` line restricts what it can touch. Adjust per your workflow.
- Each agent's `skills:` line controls which skill content is preloaded into its context at startup. Adding a skill costs tokens on *every* dispatch of that agent (roughly `bytes ÷ 4`), so keep the leaner mechanical roles (`safe-refactor`, `document-researcher`) lean — there the binding constraint is instruction dilution, not cost. Adding `Skill` to `tools:` would let an agent discover and invoke *any* installed skill at runtime; it's deliberately omitted everywhere so each agent stays scoped to its assigned set.
- Descriptions double as routing triggers for auto-suggestion — keep them specific if edited.
- `codebase-researcher` vs. `document-researcher`: former traces your own codebase, latter pulls external docs.
- `architecture-engineer` owns the full design arc: high-level architecture and tradeoffs, the request/response contract at the API boundary, and internal module structure and data storage. (It replaces the former separate `system-design` and `api-design` roles.)
- Department subdirectories under `agents/` are organizational only — moving a file between departments never changes its `name:` frontmatter, so it never breaks how the agent is invoked or `@`-mentioned.
- `model:` can be overridden per dispatch (the Task tool's per-call `model` param takes precedence over the frontmatter default) — `project-manager` uses this per the model-tier guidance in `engineering-flows-and-gates` to upgrade a task's model tier for higher risk. `effort:` cannot be overridden per dispatch; it's a fixed default you tune once in the agent's own file.

## Workflow reliability policy

Before delegation, classify each task deterministically as LOW, MEDIUM, or HIGH from its impact
signals, and record reasoning effort separately. LOW work stays with the main agent; MEDIUM work
may use one focused specialist; HIGH work requires the full threat-model, design, implementation,
QA, security, and human-review gates. The complete policy and HIGH gate order live in
skills/engineering-flows-and-gates/SKILL.md.

skills/<role>/SKILL.md is the canonical source for every role definition. Agent frontmatter stays
agent-specific, while agent bodies are generated from the matching canonical skill. Check or
regenerate synchronization with:

    python scripts/sync_role_agents.py --check
    python scripts/sync_role_agents.py

Validate the repository and run the tests with:

    python -m pip install -r requirements-dev.txt
    python -m unittest discover -s tests -v
    python scripts/validate_repo.py

Release versions are sourced from .claude-plugin/plugin.json; marketplace metadata must match that
version. Skill frontmatter does not carry a version.
