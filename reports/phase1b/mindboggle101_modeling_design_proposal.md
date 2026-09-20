# Mindboggle-101 Modeling Design Proposal

Date: 2026-09-15

## Human phase-transition decision

The professor reviewed the manifest-driven 2D/3D Mindboggle-101 viewer, found the project direction very good, and approved continuing toward segmentation-model development. This document is a read-only training-readiness audit and scientific-design proposal; it does not generate splits, preprocessing outputs, or training code.

## Modeling objective

Proposed task: voxel-wise multiclass segmentation from a T1-weighted skull-stripped brain MRI to the matching manual DKT31 cortical label volume. The target is a manual reference segmentation, not a prediction. The foreground contains the 62 original DKT anatomical regions and background is a separate class. Manual+aseg files remain auxiliary and are not canonical targets.

## Native versus MNI152 evidence

- Native rows: 101; shapes 7, spacings 8, orientations 6, rounded affines 48.
- MNI152 rows: 101; shapes 1, spacings 1, orientations 1, rounded affines 1.
- MNI152 foreground proportion median: 0.089035; native foreground proportion median: 0.039017.
- MNI152 MRI nonzero voxels median: 1795821.0; native MRI nonzero voxels median: 1141317.0.

Recommendation: use MNI152 as the primary first-baseline coordinate space. The actual manifest evidence supports the provisional preference because all 101 MNI152 records share one 182x218x182 shape, 1 mm spacing, LAS orientation, and one rounded affine. Native space should be preserved for a later comparison because it keeps the distributed native geometry but has varied shapes/orientations and higher batching burden.

Do not use native and MNI152 versions of the same acquisition as independent samples. Split the 101 subject/acquisition records, then attach exactly one chosen coordinate-space row for training.

## Compute environment

|item|value|
|---|---|
|operating_system|Windows 11 (10.0.26200)|
|python_version|3.12.10|
|cpu|11th Gen Intel(R) Core(TM) i7-1165G7 @ 2.80GHz|
|installed_ram|31.7 GiB installed|
|project_drive_disk|221.4 GiB free of 244.1 GiB on D:\|
|gpu_model|not_detected_by_nvidia_smi|
|gpu_vram|not_detected_by_nvidia_smi|
|nvidia_driver|unavailable (FileNotFoundError: [WinError 2] The system cannot find the file specified)|
|cuda_available|unavailable_without_torch (ModuleNotFoundError: No module named 'torch')|
|pytorch_version|not_installed (ModuleNotFoundError)|
|monai_version|not_installed (ModuleNotFoundError)|
|nnunet_version|not_installed (ModuleNotFoundError)|
|nibabel_version|5.4.2|
|numpy_version|2.5.2|

Implication: if `cuda_available` is false or no compatible NVIDIA GPU is detected, the primary 3D baseline remains a design target but local training will likely require smaller patches, CPU-only smoke runs, or access to GPU hardware.

## Class distribution in recommended MNI152 space

All 62 foreground DKT labels are observed and documented. All 62 occur in every one of the 101 MNI152 records. The class distribution is highly imbalanced; a foreground-aware loss and sampling strategy is required.

Smallest total MNI152 regions:

|label_id|name|hemisphere|voxels|presence|
|---|---|---|---|---|
|2034|transverse temporal|right|144702|101|
|1034|transverse temporal|left|170163|101|
|2006|entorhinal|right|231487|101|
|1006|entorhinal|left|233441|101|
|2016|parahippocampal|right|280583|101|
|1021|pericalcarine|left|283476|101|
|1016|parahippocampal|left|292522|101|
|1019|pars orbitalis|left|310012|101|

## Reversible class mapping proposal

Background maps to training class 0. The 62 noncontiguous original DKT IDs map deterministically to contiguous classes 1-62 in ascending original-label order, and each row maps back to its original DKT ID, region name, and hemisphere. This is a proposal only; no NIfTI label volume has been rewritten.

## Split feasibility proposal

|proposal_item|recommendation|value|status|
|---|---|---|---|
|grouping_key|accept|participant_group_id|proposal_pending_human_approval|
|coordinate_space_for_splitting|use_subject_record_once_then_link_space_rows|split 101 subject/acquisition records, not 202 scan-space rows|proposal_pending_human_approval|
|target_counts|accept_approximate|70 train / 15 validation / 16 test subject records|proposal_pending_human_approval|
|cohort_balance|stratify_by_cohort_with_group_integrity_first|Extra-18:18; MMRR-21:21; NKI-RS-22:22; NKI-TRT-20:20; OASIS-TRT-20:20|proposal_pending_human_approval|
|shared_cross_cohort_groups|preserve|NKI-Rockland-1427581; NKI-Rockland-3808535|proposal_pending_human_approval|
|repeat_counterpart_constraints|preserve|99|proposal_pending_human_approval|
|seed|accept|20260831|proposal_pending_human_approval|
|tie_breaking|accept|SHA-256 over dataset version, seed, participant_group_id, and allocation context|proposal_pending_human_approval|
|frozen_test_policy|accept_after_human_approval|freeze once, then do not inspect or tune on test labels|proposal_pending_human_approval|

Recommendation: accept `participant_group_id` as the grouping key; accept approximate 70/15/16 subject-record targets; accept seed `20260831`; accept SHA-256 deterministic tie-breaking; stratify by cohort while preserving group integrity first; freeze the test set only after explicit approval. The two confirmed shared NKI participant groups must remain indivisible.

## Baseline model strategy

Primary proposal: patch-based 3D U-Net / nnU-Net-style baseline on MNI152 records. Use a 63-class output head, mixed Dice plus cross-entropy or focal/Tversky-style weighting for imbalance, AdamW or SGD-with-momentum depending on framework defaults, conservative learning-rate scheduling, small patch batches sized to VRAM, validation every epoch or fixed iteration interval, best-validation checkpoint plus latest checkpoint, and patience-based early stopping.

Fallback proposal: 2D U-Net over deterministic anatomical slices, or smaller 3D patches with gradient accumulation if GPU memory is insufficient. The fallback is less anatomically complete but easier to run on limited hardware.

## Preprocessing proposal

- Coordinate space: MNI152 for the first baseline; native space later.
- Orientation handling: preserve source arrays for now because MNI152 rows are consistently LAS; if a framework requires canonical orientation, make it a logged reversible transform applied identically to MRI and labels.
- Resampling: none for MNI152 baseline because shape/spacing are already standardized; if used later, MRI interpolation may be linear or spline, labels must use nearest-neighbor only.
- Intensity clipping/normalization: compute brain-mask nonzero percentiles per training MRI, then z-score or robust normalize MRI only; record parameters and never alter labels.
- Foreground cropping/padding: optional reversible crop around nonzero MRI or label support for training patches; pad to model-compatible patch sizes; evaluation must reconstruct to full MNI152 grid.
- Patch sampling: foreground-biased random patches plus some background/context patches to address class imbalance.
- Label remapping: apply the proposed reversible contiguous mapping only inside training tensors, not source NIfTI files.
- Augmentation: modest intensity perturbation and spatial transforms only after split approval; labels require nearest-neighbor interpolation.

## Evaluation proposal

Report Dice per original DKT region, macro-average foreground Dice, median foreground Dice, cohort-wise Dice, hemisphere-wise Dice, and failure cases. Treat absent classes explicitly; since all 62 regions are present in the proposed MNI152 records, absent-class handling is mainly a guardrail. Background Dice should be reported separately or excluded from foreground macro averages. HD95 or surface distance can be optional if compute and implementation time allow. Validation guides model selection; the frozen test set is used once for final reporting.

## Unresolved constraints

Licensing reconciliation, Dataverse v2 versus OSF v3 equivalence, unresolved external-dataset overlap cautions, NKI session/acquisition uncertainties, OASIS external-overlap uncertainty, historical label-notice scope, and the absence of any clinical-validity claim remain explicit constraints.

## Validation summary

Passed: read-only manifest/header/array audit, MNI152 class-distribution audit, reversible class-mapping proposal, split-feasibility proposal, compute-environment inspection, and scope-control checks.

Skipped: split assignment generation, preprocessing output generation, dependency installation, model implementation, and training.

Unverified: final human approval of coordinate space, class mapping, split policy, baseline framework, dependency set, and hardware execution plan.

Blocked: none for this proposal milestone; subsequent implementation awaits explicit approval.
