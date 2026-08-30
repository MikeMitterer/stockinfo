# Agent Scope Guard Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stop unplanned ticket growth before a large diff forms and let Codex decide mechanical scope extensions without involving Mike.

**Architecture:** Extend the existing file-based Claude↔Codex state machine with one short `scope_checkpoint` path. Keep the durable rule in the existing automation contract, teach the scheduler to wake for that phase, and add the required scope block to the board instructions; no executable subsystem or new service is introduced.

**Tech Stack:** Markdown workflow contracts, Git, existing in-context scheduler

**Spec:** `docs/superpowers/specs/2026-08-30-agent-scope-guard-design.md`

## Global Constraints

- Claude remains implementer; Codex decides mechanical scope extensions.
- Mike is involved only for a new product decision.
- One budget extension per ticket; a second breach defaults to reduce or split.
- No new test infrastructure, CLI, service, dependency, or product code.
- T-38 is not interrupted retroactively; the guard applies from T-37 onward.

---

### Task 1: Encode the checkpoint state and decision contract

**Files:**
- Modify: `_tickets/CODEX-REVIEW-AUTOMATION.md`
- Modify: `_tickets/CODEX-IN-CONTEXT-SCHEDULER.md`
- Modify: `_tickets/STATUS.md`

**Interfaces:**
- Consumes: the existing `phase`, `owner`, `handoff_commit`, `ticket`, and `priority_ticket` fields
- Produces: `phase: scope_checkpoint` with a frozen commit and exactly one Codex decision (`continue`, `reduce`, `split`, `mike`)

- [ ] **Step 1: Add the phase and invariant to the automation contract**

Document that `scope_checkpoint` is valid only with `owner: codex`, a frozen
`handoff_commit`, and an OUTBOX containing planned versus actual scope. State
that this is a breadth decision, not a code review, and that Codex must not add
quality requirements.

- [ ] **Step 2: Add the five triggers and one-extension rule**

Copy the exact triggers from the approved spec: unplanned layer, unplanned
public contract/schema/dependency/abstraction, more than 25 percent file
variance, more than 800 diff lines, or process history in code comments.
Product comments and test docstrings may explain only the current invariant
and its technical reason; review rounds, commit IDs, conversation quotes,
dates, and implementation chronicles stay in ticket, spec, and Git.

- [ ] **Step 3: Extend the Claude loop prompt**

Require a `Scope-Vertrag` before the first product edit and make Claude enter
`scope_checkpoint` before further work when a trigger fires. After a Codex
decision, only `continue`, `reduce`, or `split` returns to `claude_working`;
`mike` becomes `blocked`.

- [ ] **Step 4: Extend the scheduler without adding a second review path**

Wake the existing chat for valid `scope_checkpoint` states and deduplicate on
`(phase, ticket, handoff_commit, review_round)`. Keep `ready_for_codex` as the
only trigger for a full review.

- [ ] **Step 5: Update the STATUS phase legend**

Add `scope_checkpoint` to the allowed phases only; do not switch the active
T-38 review state.

- [ ] **Step 6: Verify the state contract**

Run:

```bash
rg -n "scope_checkpoint|continue|reduce|split|800|25 Prozent" \
  _tickets/CODEX-REVIEW-AUTOMATION.md \
  _tickets/CODEX-IN-CONTEXT-SCHEDULER.md \
  _tickets/STATUS.md
git diff --check
```

Expected: every state consumer mentions `scope_checkpoint`; no whitespace
errors.

- [ ] **Step 7: Commit**

```bash
git add _tickets/CODEX-REVIEW-AUTOMATION.md \
  _tickets/CODEX-IN-CONTEXT-SCHEDULER.md _tickets/STATUS.md
git commit -m "docs(process): Scope-Checkpoint verbindlich machen"
```

---

### Task 2: Make every implementation ticket declare its budget

**Files:**
- Modify: `_tickets/README.md`

**Interfaces:**
- Consumes: the ticket header and Verify-Matrix convention
- Produces: a required `Scope-Vertrag` block that Claude fills before product work

- [ ] **Step 1: Add the canonical ticket block**

Add this exact shape to the board rules:

```markdown
## Scope-Vertrag

- **Ergebnis:** Ein Satz mit dem beobachtbaren Ergebnis.
- **Fachliche Änderungen:** Höchstens drei einzeln benannte Regeln.
- **Produktflächen/-dateien:** Erwartetes Inventar vor dem ersten Edit.
- **Tests/Dokumentation:** Erwartete mechanische Anpassungen.
- **Nicht-Ziele:** Ausdrücklich ausgeschlossene Arbeiten.
- **Budget:** Geschätzte Produktdateien, Test-/Dokudateien und Diff-Zeilen.
```

State that existing tickets receive the block immediately before their next
product edit; historical solved tickets are not rewritten.

- [ ] **Step 2: Add the final planned/actual handoff table**

Require the four rows from the spec: semantic changes, product files,
test/documentation files, and diff lines. Each deviation gets one sentence.

- [ ] **Step 3: Verify the board contract**

Run:

```bash
rg -n "Scope-Vertrag|Fachliche Änderungen|Produktflächen|Nicht-Ziele|tatsächlich" _tickets/README.md
git diff --check
```

Expected: one canonical block and one handoff comparison, no duplicate format.

- [ ] **Step 4: Commit**

```bash
git add _tickets/README.md
git commit -m "docs(board): Scope-Budget je Ticket verlangen"
```

---

### Task 3: Close the design artifact and verify the complete rule

**Files:**
- Modify: `docs/superpowers/specs/2026-08-30-agent-scope-guard-design.md`

**Interfaces:**
- Consumes: implemented workflow from Tasks 1 and 2
- Produces: a design status that no longer says written review is pending

- [ ] **Step 1: Mark the spec approved and implemented**

Replace the provisional status with `von Mike bestätigt; im StockInfo-Workflow umgesetzt`.

- [ ] **Step 2: Run the complete static verification**

```bash
rg -n "scope_checkpoint" _tickets/CODEX-REVIEW-AUTOMATION.md \
  _tickets/CODEX-IN-CONTEXT-SCHEDULER.md _tickets/STATUS.md
rg -n "Scope-Vertrag" _tickets/README.md
git diff --check
```

Expected: the checkpoint is represented in all state documents and the ticket
contract exists exactly once.

- [ ] **Step 3: Commit**

```bash
git add docs/superpowers/specs/2026-08-30-agent-scope-guard-design.md
git commit -m "docs(process): Scope-Guard als umgesetzt markieren"
```
