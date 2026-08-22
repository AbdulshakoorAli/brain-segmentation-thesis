# Mindboggle-101 Dataset Source and License Record

## Dataset identity

- Dataset name: Mindboggle-101 manually labeled individual brains
- Individual-brains dataset DOI: [10.7910/DVN/HMQKCK](https://doi.org/10.7910/DVN/HMQKCK)
- Official collection URL: https://dataverse.harvard.edu/dataverse/mindboggle101
- OSF primary-repository URL: https://osf.io/nhtur/
- Project data page: https://mindboggle.info/data
- Observed local raw-data location: `data/raw/mindboggle101/` (24 files; archives remain unextracted)
- Retrieval date: unverified; downloaded files were present when inspected on 2026-08-23

## Version status

The project data page reports Mindboggle-101 data, code, and documents as version 3, updated 2019-04-03. The Harvard Dataverse API for the Individuals DOI reports dataset version 2 with 24 files. The local filenames and byte sizes match that Dataverse v2 listing exactly, but equivalence between Dataverse v2 and the OSF/project-level v3 designation is unverified. Local SHA-256 checksums are recorded in `metadata/raw_file_inventory.csv`.

## Phase 1A scope

This project targets individual T1-weighted MRI volumes and their corresponding manually corrected Desikan-Killiany-Tourville (DKT) cortical label volumes. Templates, population atlases, surfaces, FreeSurfer products, and model-ready remappings are out of scope for this milestone.

The manual DKT volume is reference segmentation, not a model prediction. MRI/label pairs must later be proven to share a compatible coordinate space; native-space and MNI-space artifacts must not be mixed.

## Licensing status and unresolved checks

Licensing is unresolved and requires human review before data use. No standalone license or terms file appears in either the local 24-file set or the Harvard Dataverse v2 file listing. The following checks remain blocked:

- reconcile the repository-level license metadata with the project page's general Creative Commons statement and any component-specific notices;
- confirm the license version and terms for every in-scope T1 MRI and DKT label component;
- identify any cohort/source restrictions, attribution requirements, non-commercial or share-alike terms, and redistribution limits;
- preserve and inventory every license, citation, provenance, and terms-of-use file shipped with the package;
- confirm that intended thesis processing, publication, and artifact sharing comply with all applicable terms.

No permissive interpretation is adopted while these sources remain unreconciled.

## Source verification record

URLs and the project-level upstream version statement were checked on 2026-08-22. On 2026-08-23, the observed local set was compared with the Harvard Dataverse API: all 24 filenames and byte sizes matched its dataset-version-2 listing. Exact OSF v3 equivalence, retrieval date, source hierarchy, and bundled licensing evidence remain unverified. See `docs/raw_dataset_organization_report.md`.
