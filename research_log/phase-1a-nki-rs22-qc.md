# Research log: Phase 1A NKI-RS-22 QC and lineage

- Date: 2026-08-27
- Skill: repository-local `brain-segmentation-research`.
- Scope: only `NKI-RS-22_volumes.tar.gz`; archive inspection/extraction, scan inventory, unchanged NIfTI QC, label-issue review, and participant/acquisition lineage.
- Boundaries: no other cohort, splits, loader, training, visualization, or MRI transformations.

## Evidence reviewed

- `metadata/raw_file_inventory.csv`.
- Mindboggle subject list, subject-source table, subject table, label definitions, and `label-issues_201903.txt`.
- Scan-information archive members `README_NKI-RS-22.txt`, the selected-22 phenotype table, `NKI.1-39.NumbersQC.csv`, and the full phenotype table.
- Downloaded Mindboggle processing scripts, especially the canonical/manual+aseg product names and DKT31 filtering logic.
- Existing Extra-18 and MMRR-21 manifests, QC outputs, metadata review, reports, QC implementation, dictionary, and tests.

Local evidence was sufficient; no external source was required.

## Results

- Archive SHA-256 matched inventory: `450588dcb8528b617c1472cb8119748f60481b6d40d2d10e6aafca21a8e078c4`.
- 221 safe members (198 files, 23 directories), no unsafe paths, links, special entries, duplicates, or overwrite risk.
- Extracted tree exactly matches the archive: 198 files, 176 NIfTIs, 22 subjects.
- Canonical candidates: 22 native and 22 MNI152; missing/ambiguous pairs: 0.
- Existing QC engine used unchanged: 44 verified, 0 failed, 0 blocked, 0 unknown observed IDs.
- Participant groups: 22 confirmed, 0 unresolved. Acquisition sessions: 21 resolved, 1 ambiguous (`NKI-RS-22-16`: `MR_3927656_3303` versus `MR_3927656_3268`).
- Repeat acquisitions: none documented among included NKI rows; absence outside the selection is unverified.
- Label notice: 18 entries across 7 subjects; 7 annotation-only, 11 not applicable to canonical DKT31, 0 exclusions.

## Repeated validation

- Automated tests: 8/8 passed twice.
- QC: 44/44 verified on both runs.
- Metadata generation: identical counts and byte-identical outputs on both runs.
- Stable hashes: manifest `320ce9fa...24d3`, pair QC `b7825600...749f`, failures `12b81b05...e753`, lineage `88f0201d...bdda`, issues `808d770f...ffcb`.
- Accepted QC code/dictionary and Extra-18/MMRR-21 artifact hashes were unchanged.
- Final raw archive checksum remained equal to inventory.

## Outcome

NKI-RS-22 passes this scoped Phase 1A checkpoint. It is safe for within-cohort participant-grouped splitting by the evidence-supported group ID, but no split was created. Human clarification remains recommended for the one session discrepancy and historical label-product scope. Licensing and Dataverse v2/OSF v3 equivalence remain unresolved.
