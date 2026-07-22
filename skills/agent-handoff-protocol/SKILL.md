---
name: agent-handoff-protocol
description: This skill should be used whenever an agent dispatches work to another agent or reports work back, including completion, blocking, clarification, and rejection. It defines a structured handoff packet, narrow delegation boundaries, artifact reuse, and escalation rules.
---

# Agent handoff protocol

Every dispatch and report uses the same packet. A packet is a compact, checkable interface between
agents, not a transcript of the preceding conversation.

## The packet

~~~yaml
handoff:
  objective: <one narrow sentence describing the requested outcome>
  from: <agent-name | "user">
  to: <agent-name>
  status: dispatched | complete | blocked | needs_clarification | rejected
  risk: LOW | MEDIUM | HIGH
  inputs:
    - <file path or inline reference to an existing artifact>
  constraints:
    - <explicit boundary, including what NOT to change>
  output_format: <exact report/artifact shape expected>
  produced_artifacts:
    - path: <file path>
      description: <what it contains>
  definition_of_done: <concrete, checkable completion criterion>
  stop_condition: <when investigation or implementation must end>
  notes: <deviations, open questions, or escalation target>
~~~

objective must be narrow enough to complete without discovering a second project. inputs names
the minimum files or prior artifacts needed; do not make the receiver rescan the repository for
context already established. constraints states the scope boundary, especially files or actions
that must not be touched. output_format makes the response machine- and human-checkable (for
example, "findings ordered by severity with path, evidence, and fix"). definition_of_done and
stop_condition are different: the former says what success contains, while the latter prevents
unbounded investigation.

Every handoff must carry an explicit risk tier. MEDIUM and HIGH packets include all fields. For
LOW work, constraints and notes may be omitted only when there is genuinely no meaningful
boundary or deviation; output_format and stop_condition remain mandatory.

## Reuse artifacts; do not re-derive them

Read and cite prior findings, threat models, designs, specs, and test reports from inputs. Do not
rescan files or restate a prior artifact in packet prose unless checking a changed section. If a
needed artifact is missing, report that gap instead of silently recreating it.

## Gaps, retries, and escalation

When a required input is missing, contradictory, or materially ambiguous, set
status: needs_clarification, name the exact gap in notes, and return the packet to the sender
(usually project-manager). Never invent a fact or silently choose between materially different
interpretations.

An agent may make one focused retry after a failed attempt. After two failed attempts, it must
escalate to project-manager, who raises the model tier, narrows/splits the task, or asks the user.
There is no third silent retry. Use status: blocked for an operational blocker and
status: rejected when the deliverable violates a stated boundary.

On completion, replace dispatched with complete, list every produced or modified artifact, and
include the verification command/result. A packet is forwardable: the next agent reads the named
artifacts and does not require the original conversation.

## Role-specific routing

This skill defines the shared packet shape. Each agent's own Handoff section defines role-specific
recipients and completion criteria; it should reference this skill rather than duplicate the schema.
