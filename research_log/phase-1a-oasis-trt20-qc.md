# Research log: Phase 1A OASIS-TRT-20 QC, lineage, and overlap

- Date: 2026-08-27
- Skill: repository-local `brain-segmentation-research`.
- Scope: only OASIS-TRT-20 archive validation/extraction, inventory, unchanged NIfTI QC, label issues, participant/acquisition lineage, and OASIS overlap.

## Evidence

Local evidence included the package inventory, subject list/source/table, OASIS reliability README and fact sheet, label notice/definitions, processing scripts, accepted manifests/QC hashes, and archive members. Authoritative corroboration used the official OASIS-1 page (`https://sites.wustl.edu/oasisbrains/home/oasis-1/`) and primary OASIS-1 paper (`https://pubmed.ncbi.nlm.nih.gov/17714011/`).

## Results

- Archive hash matched inventory: `9c26c7846293a74c94270d9b1c977bd180e084690a82538f4848d960be41137b`.
- 201 safe members exactly match disk; 180 files, 160 NIfTIs, 20 subjects.
- Candidates/QC: 20 native and 20 MNI152; 40 verified, 0 failed, 0 blocked, 0 unknown IDs.
- Lineage: 20 distinct participants and repeat groups, 18 included tests, two included retests, and all 20 external counterparts resolved.
- Overlap: all 20 confirmed in the wider OASIS-1 reliability set; no participant or exact file/voxel overlap with another accepted Mindboggle cohort.
- Label notice: nine pole-ID records across eight subjects; all annotation-only, no exclusions.

## Validation

- Automated tests passed 8/8 twice.
- QC and metadata generation ran twice with byte-identical six-artifact hashes.
- Existing QC implementation/tolerances and dictionary remained unchanged.
- Accepted Extra-18, MMRR-21, NKI-RS-22, and NKI-TRT-20 artifacts and archive hashes remained unchanged.
- Shared NKI groups 1427581 and 3808535 remained identical across NKI cohorts.
- OASIS raw archive hash remained equal to inventory; no raw file was renamed or modified.

## Outcome

OASIS-TRT-20 passes this scoped checkpoint and is safe for participant-grouped splitting, but no combined manifest or split was created. OASIS-2/OASIS-3 derivative overlap, NKI acquisition uncertainties, label-product scope, licensing, and Dataverse v2/OSF v3 equivalence remain unresolved.
