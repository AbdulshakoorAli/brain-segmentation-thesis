# Mindboggle-101 Preprocessing Implementation Report

Date: 2026-09-20

Implemented deterministic in-memory MNI152 preprocessing only. No preprocessed volumes, patches, tensors, caches, model code, training outputs, or evaluation results were created.

## API

- `normalize_mri_per_volume`
- `map_labels_to_training_classes`
- `inverse_map_training_classes`
- `preprocess_verified_mni152_pair`

## Approved behavior

- Per-volume nonzero 0.5/99.5 percentile clipping.
- Per-volume nonzero z-score after clipping.
- Background remains exactly zero.
- MRI output dtype is `float32`.
- Label output dtype is `uint8`.
- Native records are rejected for training preprocessing.
- Unknown original DKT IDs and unknown contiguous classes fail.

## Smoke validation

Records: 5

Splits represented: {'validation': 1, 'test': 2, 'train': 2}

Cohorts represented: ['Extra-18', 'MMRR-21', 'NKI-RS-22', 'NKI-TRT-20', 'OASIS-TRT-20']

Failed smoke rows: 0

Source hashes preserved: True

Test-set use: frozen test records were used only to prove the approved per-volume transform executes deterministically; no parameter was tuned from test results.
