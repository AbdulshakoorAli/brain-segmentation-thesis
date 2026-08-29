# MMRR-21 Phase 1A Metadata, Lineage, and Label-Issue Review

## Scope and decision

MMRR-21 has sufficient evidence for participant-grouped splitting **within this cohort**, but no split was created. The 21 included scans represent 21 distinct participants. Each included acquisition has a confirmed second acquisition in the original 42-session dataset; native/MNI152 rows are two coordinate-space products of the same included acquisition, not repeat scans.

Temporal `scan` versus `rescan` role remains unresolved because the original study randomized session identifiers. The five-subject March 2019 label notice is provenance annotation only: all six mentioned subject/ID entries concern IDs absent from the accepted native and MNI152 canonical manual-DKT31 volumes. No exclusion is supported.

No MRI was processed, no raw data or passed QC measurement was changed, and no split or other cohort work was performed. Licensing reconciliation and Harvard Dataverse v2 versus OSF/project v3 equivalence remain unresolved.

## Evidence used

- `subject_list_Mindboggle101.txt`: 21 included MMRR subject names.
- `subject_sources_Mindboggle101.txt`: `KKI2009-<Visit ID>` sources; its repeat section covers subjects 1-10 only.
- Scan-information `README_MMRR-21.txt`: every included subject's Visit ID and three-digit SubjectID.
- Scan-information `MMRR_demographics.pdf`: all 42 visits; each SubjectID occurs exactly twice, resolving the second acquisition for all 21 participants, including subjects 11-21.
- The supplied subject table: cohort context. Its embedded font prevented reliable row-text extraction, so it was not sole row-level evidence.
- `label-issues_201903.txt`, `label_definitions.txt`, and downloaded processing scripts: historical entries, hemisphere/name mapping, and DKT31 selection/regeneration logic.
- Existing MMRR inventory and QC: both canonical spaces have no unknown observed IDs and all 42 pairs remain verified.
- Original MMRR paper: 21 volunteers, two fully repositioned sessions, randomized session identifiers.
- Primary Mindboggle-101 paper: MMRR-21 comprises 21 test-retest subjects.

The Harvard Dataverse DOI record and Mindboggle documentation were consulted for package context but supplied no additional row-level lineage evidence.

## Lineage result

- Scan records: 42 (21 native, 21 MNI152).
- Included acquisitions and distinct participant groups: 21.
- Confirmed repeat-acquisition groups: 21, each containing the included `KKI2009` Visit ID and its other session from the 42-row table.
- Additional canonical repeat acquisitions in this archive: 0.
- Temporal roles resolved: 0; unresolved: 21 acquisitions (42 coordinate-space records).

Subjects 1, 9, and 11-21 were checked explicitly. Their included Visit IDs, SubjectIDs, and counterpart Visit IDs come from the README and full demographics table, not subject numbering.

## Label-issue reconciliation

The notice says the errors were corrected in March 2019 but does not specify which distributed product its subject-level `.nii.gz` name denotes. Product scope remains unresolved.

| Subject | ID | Documented anatomy | Current canonical effect | Action |
|---|---:|---|---|---|
| MMRR-21-1 | 1032 | left frontal pole | not observed | annotation only |
| MMRR-21-1 | 1033 | left temporal pole | not observed | annotation only |
| MMRR-21-17 | 2032 | right frontal pole | not observed | annotation only |
| MMRR-21-19 | 1033 | left temporal pole | not observed | annotation only |
| MMRR-21-20 | 2033 | right temporal pole | not observed | annotation only |
| MMRR-21-9 | 2032 | right frontal pole | not observed | annotation only |

These are metadata-mentioned IDs, not observed voxel IDs. They were not added to the DKT dictionary. Exclusions: 0; annotation-only entries: 6 across 5 subjects.

## Reproducibility and preservation

`scripts/review_mmrr21_metadata.py` reconstructs the review tables and appends only evidence-supported manifest fields. Two runs were byte-identical:

- lineage CSV: `e4064703f820f9da86ed05879e27886daa12c9cc3ea5920e6bc6d3014eda2cb3`
- label-issue CSV: `558f97d4a80924cb766ecdc7144c0673bc1c78e9520f5f5666345c474a404289`
- augmented manifest: `23fa2d169043d08d07a645c05f3e901493fc05867b8a03c2762127ba91e4cd3f`

Accepted pair QC (`ee828bcc...e8568`), failures (`12b81b05...e753`), QC code (`763f6e90...7b4c`), DKT dictionary (`76a113ac...1306`), and raw archive (`73b27f5c...eeb1`) retained their established hashes.

## Final accounting

### Resolved

- 42 records assigned to 21 participant and repeat-acquisition groups.
- Native/MNI152 products identified as representations of the same included acquisition.
- Six historical label entries reconciled as metadata-mentioned, not observed, and annotation-only.

### Unresolved

- Temporal scan/rescan role for all 21 acquisitions.
- Exact product intended by the March 2019 notice.
- Licensing reconciliation and Dataverse v2 versus OSF/project v3 equivalence.

### Subjects requiring human clarification

- `MMRR-21-1`, `MMRR-21-9`, `MMRR-21-17`, `MMRR-21-19`, and `MMRR-21-20` if exact label-product scope is required.
- All 21 only if temporal first/second role is required; that role is unnecessary for participant grouping.

### Splitting readiness and next task

MMRR-21 is safe for participant-grouped splitting at the cohort level if `participant_group_id` is used, native/MNI152 products stay together, and future counterpart-session derivatives inherit the same group. Phase-wide splitting remains premature.

Exact next recommended task: obtain human sign-off on the five-subject annotation and MMRR participant map, then explicitly scope the next single Phase 1A cohort for archive/inventory/QC and lineage review; do not create splits until every intended cohort has grouping evidence.
