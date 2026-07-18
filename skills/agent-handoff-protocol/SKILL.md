---
name: agent-handoff-protocol
description: This skill should be used whenever an agent in this team dispatches work to another agent or reports work back (starting a task, completing one, blocking on something, or rejecting a deliverable). It defines the structured handoff-packet format that replaces free-form delegation prose, and the canonical rule for handling gaps found mid-task. Use when composing a Task-tool brief, when finishing a piece of delegated work, or when deciding how to react to an ambiguous/missing requirement.
version: 1.0.0
---

# Agent handoff protocol

Every handoff between agents on this team — a dispatch, a completion report, a block, a
rejection — uses the same packet shape. One vocabulary, both directions: `project-manager` fills
this in to delegate, and the receiving agent fills in the same shape to report back. This is what
lets a handoff be *forwarded* rather than *re-composed* at every relay.

## The packet

```yaml
handoff:
  objective: <one sentence — what this piece of work is for>
  from: <agent-name | "user">
  to: <agent-name>                 # who acts on this next
  status: dispatched | complete | blocked | needs_clarification | rejected
  risk: LOW | MEDIUM | HIGH
  inputs:
    - <file path or inline reference to prior artifacts>
  constraints:
    - <explicit "do NOT" scope boundary>
  produced_artifacts:
    - path: <file path>
      description: <what it is>
  definition_of_done: <concrete, checkable completion criterion>
  notes: <deviations, open questions, escalation target if blocked>
```

Field notes:
- **`objective`** — one sentence. If you need a paragraph to say what the work is for, the task is
  under-scoped; split it instead.
- **`inputs`** — file paths or inline references only. The receiving agent cannot see the
  dispatching agent's conversation, so anything it needs must be named here, not assumed.
- **`constraints`** — the scope boundary, stated as what NOT to do. This is what prevents an
  implementer from quietly expanding scope or "helpfully" touching adjacent code.
- **`produced_artifacts`** — every file the agent created or modified, with a one-line description
  of each. This is how the next agent in the chain knows what to `Read` without re-deriving it.
  Leave empty on a `dispatched` packet (nothing produced yet); required on `complete`.
  Every path here is state you're handing off — see `engineering-flows-and-gates` for which risk
  tier requires which downstream gate before this artifact counts as "safe to build on."
- **`definition_of_done`** — must be checkable by someone who wasn't in the room. "Looks good" is
  not a definition of done; "all five acceptance criteria in the spec are met and `npm test`
  passes" is.
- **`status`** — `dispatched` is set by the delegator; the receiving agent replaces it with
  `complete`, `blocked`, `needs_clarification`, or `rejected` before handing back. Never leave a
  packet in `dispatched` state when reporting — that status means "not yet started," and if you're
  reporting, it has at least started.

## Hit a gap? Flag it — never invent unilaterally

If you discover the spec is ambiguous, a dependency is missing, a required input never arrived, or
what you were asked to do conflicts with something you can observe in the code: **do not guess and
proceed.** Set `status: needs_clarification`, name the specific gap in `notes`, and hand the packet
back to whoever gave you the task (usually `project-manager`, unless your own role's handoff
routing says otherwise). Inventing a resolution and continuing is how a small ambiguity becomes a
large rework — the packet format makes naming the gap cheap, so there's no excuse to skip it.

## What stays in each agent's own file

This skill defines the *shape*. Each agent's own "Handoff" section still owns the parts that are
genuinely role-specific: which concrete agent(s) it routes `to` under which conditions (e.g. a
security-relevant finding vs. an unexplained failure vs. an ambiguous requirement each go
somewhere different), and any role-specific nuance to `definition_of_done` (e.g. what "done" means
for a security review is different from what it means for a refactor). Don't restate the packet
schema itself in an agent file — point here instead.
