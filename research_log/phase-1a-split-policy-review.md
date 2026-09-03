# Research log: Mindboggle-101 split-policy review

- Date: 2026-08-31
- Skill: repository-local `brain-segmentation-research`.
- Initiating prompt: “Use brain-segmentation-research. Continue from PROJECT_STATE.md.”
- State-derived milestone: prepare the human scientific-design review for a conservative participant-grouped split policy.
- Scope boundary: evidence inspection and proposal only; no split assignments, preprocessing, training, inference, evaluation, or raw-data changes.

## Evidence inspected

- The accepted global scan, subject, and participant-group tables parse successfully and contain 202, 101, and 99 rows respectively.
- Participant-group weighting is 97 groups with one included subject record and two groups with two records.
- The two size-two groups are the confirmed NKI-RS/NKI-TRT participant overlaps for source participants 1427581 and 3808535.
- Cohort subject counts are 18 Extra-18, 21 MMRR-21, 22 NKI-RS-22, 20 NKI-TRT-20, and 20 OASIS-TRT-20.
- Sixty-one participant groups record repeat/counterpart constraints.
- The `splits/` directory contained no assignment file before or after this review.

## Proposal result

The review recommends an indivisible `participant_group_id` assignment unit, 70/15/16 subject-record targets, cohort balancing subordinate to group integrity, seed `20260831`, stable SHA-256 tie-breaking, and a frozen test set. Native and MNI152 representations must inherit the same split and must not be counted as independent participants.

No policy was treated as approved. No assignment was generated. The proposal requests explicit human approval of the grouping unit, target matrix, deterministic seed/algorithm, and test/coordinate-space policy before a later implementation milestone.

## Validation accounting

- Passed: input parsing, expected 101/202/99 counts, group-size audit, two shared NKI groups, cohort counts, and repeat/counterpart constraint count.
- Failed: none.
- Skipped: split allocation, split audit, loader/model work, and all image processing.
- Unverified: whether the proposed ratio, cohort objective, seed, and MNI152-first recommendation match the final thesis design.
- Blocked: split generation awaits human scientific approval; licensing and provenance uncertainties remain unresolved.

## Continuation check — 2026-08-31

- Initiating prompt: “Use brain-segmentation-research. Continue from PROJECT_STATE.md.”
- Observed state: the proposal still awaits explicit approval and the `splits/` directory contains zero files.
- Outcome: no split was generated because the continuation request did not approve or revise the four pending scientific-design choices.
