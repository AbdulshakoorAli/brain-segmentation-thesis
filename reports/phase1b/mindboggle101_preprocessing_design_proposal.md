# Mindboggle-101 MNI152 Preprocessing Design Proposal

Date: 2026-09-20

## Scope

This is a read-only Phase 1B preprocessing design and feasibility milestone. It analyzes the frozen MNI152 training-space split and source NIfTI files without creating normalized volumes, crops, patches, tensors, caches, model code, training outputs, or evaluation results.

## Verification

- Accepted MNI152 records by split: {"test": 16, "train": 70, "validation": 15}
- Geometry target: shape 182x218x182, spacing 1x1x1 mm, LAS orientation.
- Check failures: 0
- Frozen split and class mapping hashes are recorded in the config proposal and were not modified.

## Recommended Normalization

Recommend per-volume nonzero percentile clipping at 0.5 and 99.5 followed by per-volume nonzero z-score normalization. This uses MRI intensities only, fits parameters independently per image, works for unseen images, avoids validation/test-derived global parameters, and preserves spatial alignment. Training-set-only evidence for the clipping range:

```json
{
  "train_nonzero_mean_median": 1011.2500683334035,
  "train_nonzero_p0_5_max": 2763.8243310546873,
  "train_nonzero_p0_5_median": 6.0,
  "train_nonzero_p0_5_min": 1.0,
  "train_nonzero_p99_5_max": 1146211.0375,
  "train_nonzero_p99_5_median": 1740.5,
  "train_nonzero_p99_5_min": 111.0,
  "train_nonzero_std_median": 452.16317215301996
}
```

Compared options:

- Per-volume nonzero z-score: leakage-safe and simple, but leaves extreme tails untouched.
- Percentile clipping plus per-volume z-score: recommended conservative baseline.
- Training-set global normalization: possible later, but requires persisted train-only fitted parameters and is less robust to scan intensity-scale differences.

## Spatial Strategy

Retain the full MNI152 182x218x182 geometry in deterministic preprocessing. Do not resample or reorient. Use patch-based sampling during training, with 96x96x96 as the initial practical patch size. A 64x64x64 patch is lighter but may lose context; 128x128x128 gives more context but has a much larger 63-class logits footprint. Label-derived cropping is rejected for deterministic baseline preprocessing because it would not be reproducible at inference unless the crop can be generated from MRI alone.

## Class Imbalance

Training-only class-frequency rows were generated for background plus all 62 DKT foreground classes. The rarest foreground training labels are:

|class|original_id|region|hemisphere|train_voxels|train_volumes|
|---|---|---|---|---|---|
|61|2034|transverse temporal|right|99654|70|
|30|1034|transverse temporal|left|123724|70|
|4|1006|entorhinal|left|160882|70|
|35|2006|entorhinal|right|161400|70|
|45|2016|parahippocampal|right|196550|70|
|19|1021|pericalcarine|left|197655|70|
|14|1016|parahippocampal|left|202051|70|
|48|2019|pars orbitalis|right|210475|70|

Recommend initial foreground-biased patch sampling using training labels only, plus a uniform/background fraction for context. Validation/test preprocessing and inference must not require labels. Recommend Dice plus unweighted cross-entropy initially; class-weighted cross-entropy can be revisited after a baseline.

## Label Mapping

Use the approved reversible mapping only inside tensor creation: original DKT IDs to contiguous 0-62, and contiguous predictions back to original DKT IDs for evaluation and visualization. Unknown IDs must fail immediately.

## Storage and Compute

```json
{
  "all_101_float32_mri_gib": 2.7169444859027863,
  "all_101_int16_label_gib": 1.3584722429513931,
  "all_101_uint8_label_gib": 0.6792361214756966,
  "compressed_storage_note": "NIfTI gzip/NPZ/Zarr compression depends on values and chunking; source .nii.gz files are already compressed.",
  "single_float32_mri_bytes": 28884128,
  "single_int16_label_bytes": 14442064,
  "single_uint8_label_bytes": 7221032
}
```

Patch memory estimates:

```json
[
  {
    "coverage_fraction_of_full_volume": 0.036302844247193475,
    "label_uint8_mib": 0.25,
    "logits_63class_float32_mib": 63.0,
    "mri_float32_mib": 1.0,
    "patch_size": "64x64x64",
    "voxels": 262144
  },
  {
    "coverage_fraction_of_full_volume": 0.12252209933427798,
    "label_uint8_mib": 0.84375,
    "logits_63class_float32_mib": 212.625,
    "mri_float32_mib": 3.375,
    "patch_size": "96x96x96",
    "voxels": 884736
  },
  {
    "coverage_fraction_of_full_volume": 0.2904227539775478,
    "label_uint8_mib": 2.0,
    "logits_63class_float32_mib": 504.0,
    "mri_float32_mib": 8.0,
    "patch_size": "128x128x128",
    "voxels": 2097152
  }
]
```

Local CPU validation of preprocessing logic is feasible. Practical 3D training likely requires GPU access; local CPU is suitable only for reduced-model or smoke experiments.

## Acceptance Test Matrix For Future Implementation

- valid preprocessing
- determinism
- source immutability
- normalization correctness
- label remapping round trip
- unknown label rejection
- shape/affine mismatch rejection
- split enforcement
- training-only fitted-statistic enforcement
- crop/pad reversal
- absence of leakage

## Unresolved Cautions

- licensing reconciliation
- Dataverse v2 versus OSF v3 equivalence
- NKI session and acquisition uncertainties
- exact acquisition relationship for the shared NKI participants
- OASIS-2/OASIS-3 row-level overlap
- historical label-notice product scope

## Status

The read-only preprocessing design passes this scoped milestone if human review accepts the proposed normalization, spatial strategy, patch size, sampling policy and loss design.
