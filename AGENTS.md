# Repository Instructions

- Work one milestone at a time and follow `PROJECT_STATE.md` plus the repository-local brain-segmentation research skill.
- Preserve source MRI and label data unchanged under `data/raw/`; write manifests, derived outputs, caches, and reports elsewhere.
- Never infer participant attributes, scan lineage, file names, label IDs, or validation outcomes. Use authoritative documentation or inspected source files and mark unavailable facts unverified.
- Keep MRI and labels in matching coordinate spaces. Before accepting a pair, verify parsing, shape, affine, orientation, spacing, finite values, label vocabulary, and spatial overlap.
- Make data splits only after participant/acquisition lineage is known, and keep all related scans in one split.
- Log each initiating prompt and validation outcome in `research_log/`, then update `PROJECT_STATE.md` from observed evidence.
- Report passed, failed, skipped, blocked, and unverified checks separately. Human review is required for licensing, scientific design, phase transitions, and thesis claims.
