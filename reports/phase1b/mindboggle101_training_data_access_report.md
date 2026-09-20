# Mindboggle-101 Training-Data Access Report

Date: 2026-09-21

Implemented framework-independent lazy access to the frozen MNI152 split records. No patch sampling, augmentation, tensors, DataLoaders, models, training, evaluation, or materialized preprocessing outputs were created.

Training-data access version: `phase1b-mni152-lazy-training-data-access-v1`

Record counts: {"test": 16, "train": 70, "validation": 15}

Participant-group counts: {"test": 16, "train": 69, "validation": 14}

Cohort counts: {"Extra-18": 18, "MMRR-21": 21, "NKI-RS-22": 22, "NKI-TRT-20": 20, "OASIS-TRT-20": 20}

Smoke records: 7

Failures: 0

Frozen test access requires explicit `allow_frozen_test=True`; test data remains unavailable by default and must not be used for tuning or development decisions.

Upstream raw and accepted artifacts were hash-checked before and after validation and remained unchanged.
