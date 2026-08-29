# Manifest-driven Mindboggle-101 viewer report

## Milestone decision

The manifest-driven Mindboggle-101 viewer passes this scoped technical milestone and is ready for local human research use. It exposes all 202 verified canonical MRI/manual-DKT31 pairs from the accepted global manifest and performs the established essential checks before display.

Displayed labels are **manual DKT31 reference segmentations, not model predictions**. This is not a clinical viewer and makes no medical claim.

## Supported catalog

The viewer reads `data/derived/manifests/mindboggle101_scan_manifest.csv` at launch rather than embedding cohort, subject, path, pair, shape, orientation, or slice values.

| Cohort | Native | MNI152 | Total |
|---|---:|---:|---:|
| Extra-18 | 18 | 18 | 36 |
| MMRR-21 | 21 | 21 | 42 |
| NKI-RS-22 | 22 | 22 | 44 |
| NKI-TRT-20 | 20 | 20 | 40 |
| OASIS-TRT-20 | 20 | 20 | 40 |
| **Total** | **101** | **101** | **202** |

All 202 `canonical_pair_id` values resolve uniquely. Cascading selectors are populated from observed manifest values for cohort, participant/scan, coordinate space, and canonical pair. The preview shows scan ID, shape, spacing, orientation, and the manual-reference notice before load.

## Reuse and scoped changes

The accepted implementation was extended rather than replaced:

- `src/brain_segmentation/loading.py`
  - retains the existing `CanonicalPairRecord`, read-only array contract, DKT dictionary loading, path confinement, and essential scientific checks;
  - adds stable loading of all verified manifest records and exact lookup by `canonical_pair_id`;
  - generalizes the native-only guard to verified `native` and `MNI152` products;
  - checks manifest affine status and expected native/MNI filename-space consistency.
- `src/brain_segmentation/visualization.py`
  - retains deterministic DKT colors, transparent background, original-value MRI display, slice/opacity/mode widgets, label lookup, and manual-reference notice;
  - derives anatomical slice, horizontal, and vertical axes from each NIfTI orientation code without reorienting the source array;
  - displays orientation alongside participant, cohort, space, shape, and spacing;
  - uses a display-only lookup table for faster categorical coloring; original DKT values are unchanged.
- `scripts/run_extra18_visualization.py` remains available and compatible; it now iterates the selected viewer's metadata-derived planes.
- `scripts/run_mindboggle101_viewer.py` is the new general selector, direct-pair launcher, and headless smoke validator.

No resampling, normalization, reorientation, cropping, padding, source rewrite, preprocessing, prediction, or DKT-ID remapping was introduced.

## Selector and viewer features

- Manifest-derived cohort selector.
- Manifest-derived participant/scan selector.
- Manifest-derived coordinate-space selector.
- Canonical-pair selector and direct `--canonical-pair-id` lookup.
- Axial, coronal, and sagittal MRI views defined from each record's orientation metadata.
- MRI-only, label-only, and overlay modes.
- Per-plane slice controls and overlay-opacity control.
- Deterministic foreground colors and transparent background.
- Subject, cohort, space, shape, spacing, orientation, slice, label ID, and anatomical region display.
- Clear manual-reference/not-prediction statement.
- Selection errors remain in the selector status area; an invalid direct canonical ID returns a clear message and exit code `2`.
- Each newly selected pair is checked before its viewer window replaces the previous one.

## Ten-record smoke validation

Selection rule: for every observed cohort, select the minimum `(canonical_pair_id, scan_id)` separately for `native` and `MNI152`. Exactly 10 records were loaded; no per-record screenshots were created.

| Cohort | Space | Selected participant | Shape | Orientation | Result |
|---|---|---|---|---|---|
| Extra-18 | native | Afterthought-1 | 176×256×256 | LAS | passed |
| Extra-18 | MNI152 | Afterthought-1 | 182×218×182 | LAS | passed |
| MMRR-21 | native | MMRR-21-10 | 170×256×256 | RPS | passed |
| MMRR-21 | MNI152 | MMRR-21-10 | 182×218×182 | LAS | passed |
| NKI-RS-22 | native | NKI-RS-22-10 | 192×256×256 | LAS | passed |
| NKI-RS-22 | MNI152 | NKI-RS-22-10 | 182×218×182 | LAS | passed |
| NKI-TRT-20 | native | NKI-TRT-20-10 | 192×256×256 | LAS | passed |
| NKI-TRT-20 | MNI152 | NKI-TRT-20-10 | 182×218×182 | LAS | passed |
| OASIS-TRT-20 | native | OASIS-TRT-20-10 | 256×256×160 | ASL | passed |
| OASIS-TRT-20 | MNI152 | OASIS-TRT-20-10 | 182×218×182 | LAS | passed |

For every record:

- selection and canonical lookup passed;
- files parsed and passed shape, affine, orientation, spacing, finite-value, MRI-content, label-integrality/nonempty, vocabulary, manifest, same-subject, and space checks;
- axial, coronal, and sagittal MRI/label artists rendered as 2D planes;
- slice, opacity, mode, transparency, deterministic-color, and label-ID/name controls passed;
- selected MRI and label SHA-256 values were identical before and after display.

Result: **10 passed, 0 failed**. Machine-readable evidence is in `data/derived/qc/mindboggle101_viewer_smoke_validation.json`. All six manifest orientation codes (`ASL`, `LAS`, `LIA`, `PIR`, `RAS`, `RPS`) also passed metadata-driven anatomical-axis construction. Existing QC regression tests passed `8/8` once.

## Dependencies and preservation

Dependency changes: none. The viewer reuses NumPy, NiBabel, Matplotlib `3.10.7`, and standard-library Tk `8.6` already available in the project environment.

Preservation checks passed for 47 accepted inputs: the global and cohort manifests, QC/lineage/overlap artifacts, participant-group metadata, DKT dictionary and source label definitions, shared QC implementation, accepted Extra-18 visualization artifacts, and all five raw archives. The 20 NIfTI files used by smoke validation also retained identical before/after hashes.

## Final accounting

### Passed

- 202/202 verified pairs catalogued and uniquely addressable.
- Five cohort selectors, 101 native records, and 101 MNI152 records supported.
- 10/10 required real-pair smoke records selected, validated, and rendered in all three planes.
- Recoverable invalid-selection behavior, six-orientation mapping, existing tests, and preservation checks passed.

### Failed

- None.

### Skipped

- Loading/rendering all 202 records in this milestone; screenshots for the 10 smoke records; extensive new synthetic tests; splits, preprocessing, training, inference, quantitative evaluation, and 3D surfaces.

### Unverified

- Human usability on different monitor/DPI/backend configurations; scientific or clinical interpretation; all previously unresolved provenance and external-overlap questions.

### Blocked

- Licensing reconciliation and formal phase-transition decisions still require human review. They do not block local technical viewer use.

## Launch command and next task

From the repository root:

```powershell
.\.venv\Scripts\python.exe scripts\run_mindboggle101_viewer.py
```

Exact next recommended task: conduct a short human usability review on a graphical workstation, explicitly checking selector flow, one non-LAS native record, one LAS MNI152 record, label lookup, and error messaging; record acceptance or requested interface changes before authorizing another milestone.
