# Phase 1B Deterministic Splits Log

Date: 2026-09-20

Initiating prompt: Phase 1B modeling-design proposal approved; generate deterministic train/validation/test assignments only.

Skill: brain-segmentation-research.

Actions:

- Validated accepted split input schemas.
- Assigned 99 participant groups using seed `20260831` and SHA-256 deterministic tie-breaking.
- Propagated assignments to 101 subject records and 202 canonical scan-space rows.
- Marked only MNI152 rows as eligible for this first training baseline.
- Wrote frozen split configuration and audit artifacts.
- Ran generation twice and verified deterministic byte-identical outputs outside volatile timestamp fields.

Validation result: passed.
