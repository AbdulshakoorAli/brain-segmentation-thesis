# Project-state protocol

Maintain `PROJECT_STATE.md` at the thesis project root. Keep it concise and evidence-based.

Use this structure:

```markdown
# Brain Segmentation Research State

## Project
- Objective:
- Dataset and version:
- Current phase:
- Current milestone:
- Last updated:

## Completed
- Milestone — evidence or artifact path

## In progress
- Task — current status

## Blocked
- Blocker — required decision or input

## Decisions
- Date — decision — rationale

## Validation
- Check — passed/failed/skipped/unverified — evidence

## Next milestone
- One bounded next action and its acceptance criteria
```

Update the state only after inspecting actual artifacts or validation output. Do not mark an item complete because code was generated. Distinguish `blocked`, `failed`, `skipped`, and `unverified`.

Keep detailed prompts, outputs, timing, failures, and manual corrections in a separate project research log. The state file should link to those records rather than duplicating them.
