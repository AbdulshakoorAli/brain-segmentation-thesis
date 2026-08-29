# Research log: Phase 1A MMRR-21 lineage review

- Date: 2026-08-27
- Scope: evidence-only MMRR-21 metadata, acquisition lineage, and March 2019 label-issue review.
- Request: create one lineage record per scan, reconcile relevant label issues, annotate the manifest from evidence, preserve technical QC, and do not process MRI data or create splits.

## Evidence and findings

Local sources were reviewed first: the subject list, subject-source table, subject table, scan-information README and demographics PDF, label-issue notice, label definitions, all four downloaded processing scripts, inventory, and accepted QC artifacts.

The README maps 21 included subjects to unique three-digit MMRR SubjectIDs and Visit IDs. The 42-session demographics table contains each SubjectID exactly twice, yielding 21 confirmed participant/repeat-acquisition groups. This resolves subjects 11-21 despite their absence from the abbreviated repeat section of the subject-source file. The original MMRR paper (`https://pmc.ncbi.nlm.nih.gov/articles/PMC3020263/`) and primary Mindboggle paper (`https://www.frontiersin.org/journals/neuroscience/articles/10.3389/fnins.2012.00171/full`) corroborate the two-session/test-retest design. Randomized session IDs leave temporal roles unresolved.

Six issue-ID entries affect five subjects. IDs 1032, 1033, 2032, and 2033 have documented names but are absent from current canonical voxel data. The notice says errors were corrected but leaves product scope unspecified, so all entries are annotations and none supports exclusion.

## Outputs and validation

- `mmrr21_lineage.csv`: 42 rows, 21 participant groups, 21 repeat-acquisition groups.
- `mmrr21_label_issue_review.csv`: 6 rows, 0 exclusions, 6 annotation-only actions.
- The manifest received only evidence-supported lineage/issue fields.
- `scripts/review_mmrr21_metadata.py` generated all three CSVs identically twice. SHA-256: lineage `e4064703...a2cb3`; issues `558f97d4...4289`; manifest `23fa2d16...cd3f`.
- Accepted pair-QC, failures, QC code, and dictionary hashes remained `ee828bcc...e8568`, `12b81b05...e753`, `763f6e90...7b4c`, and `76a113ac...1306`.
- Raw archive SHA-256 remained `73b27f5ccce27a47e6cf03b9a1adc64b191d677009340feb531793e0fa83eeb1`.

No raw/NIfTI data or QC measurement was modified. No MRI processing, split, loader, training, visualization, or other cohort work occurred. Temporal role, exact label-notice product scope, licensing, and Dataverse v2/OSF v3 equivalence remain unresolved.
