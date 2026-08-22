---
name: brain-segmentation-research
description: Develop and continue a reproducible, prompt-driven brain MRI segmentation research project. Use for Mindboggle-101 dataset preparation, data dictionaries, subject-safe train/validation/test splits, NIfTI data loading and validation, project-state management, and later visualization or segmentation milestones. Trigger when a user asks to start, resume, inspect, implement, or validate a phase of the brain segmentation thesis project.
---

# Brain Segmentation Research

Advance the thesis one validated milestone at a time. Treat generated code as an implementation candidate that must pass technical and scientific checks.

## Start every task

1. Read repository instructions and `PROJECT_STATE.md` when present.
2. Inspect existing files and preserve working user changes.
3. Identify the current phase, requested milestone, available inputs, and acceptance criteria.
4. If the project has no state file, create `PROJECT_STATE.md` using `references/project-state.md`.
5. Record the initiating prompt, date, skill version, intended deliverable, and final validation result in the project's research log.
6. Work only on the requested milestone. Do not silently advance to another phase.

## Route the work

- For Phase 1A dataset foundation work, read `references/phase-1a.md` and `references/mindboggle-101.md` completely.
- For a later phase without a corresponding reference, prepare a scoped proposal and acceptance criteria; do not invent a finalized workflow.
- Add proven instructions, scripts, or templates to this skill only after they succeed on real project data and are reusable across students.

## Apply scientific guardrails

- Keep original data immutable. Write manifests, derived data, splits, caches, and reports outside the raw-data directory.
- Derive metadata from source files or authoritative documentation. Mark unavailable values as missing; never infer participant attributes.
- Verify image/label shape, affine, orientation, voxel spacing, finite values, and label vocabulary before treating a pair as usable.
- Keep native-space images with native-space labels and MNI-space images with matching MNI-space labels.
- Split by participant or acquisition lineage, not blindly by scan. Keep repeat scans from one participant in one split.
- Record split seed, algorithm, grouping key, counts, exclusions, and dataset version.
- Detect overlap with external OASIS, NKI, MMRR, or derivative datasets before combining benchmarks.
- Treat the manual DKT label volume as reference segmentation, not as a model prediction.
- Report license and provenance conflicts rather than choosing the most permissive interpretation.
- Do not claim medical or clinical validity from visualization or software tests.

## Validate before completion

1. Run the smallest relevant automated tests and dataset checks.
2. Report passed, failed, skipped, and unverified checks separately.
3. Stop when required data is missing, MRI/label alignment fails, leakage cannot be ruled out, or an acceptance criterion fails.
4. Update `PROJECT_STATE.md` with completed work, evidence, blockers, decisions, and the next milestone.
5. Summarize created artifacts and remaining risks without claiming the next phase is complete.

## Keep the skill reusable

- Keep project-specific paths, secrets, downloaded medical data, participant records, and experiment logs out of the skill.
- Store detailed domain knowledge in `references/`, deterministic repeated operations in `scripts/`, and proven starter templates in `assets/`.
- Prefer concise instructions and load only the reference relevant to the active phase.
- Require human review for dataset licensing, scientific design, phase transitions, and thesis claims.
