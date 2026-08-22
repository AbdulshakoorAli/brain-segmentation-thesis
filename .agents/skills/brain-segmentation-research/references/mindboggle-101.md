# Mindboggle-101 working reference

## Authoritative starting points

- Collection: `https://dataverse.harvard.edu/dataverse/mindboggle101`
- Individual brains DOI: `https://doi.org/10.7910/DVN/HMQKCK`
- Project data page: `https://mindboggle.info/data`
- Primary paper DOI: `https://doi.org/10.3389/fnins.2012.00171`

Verify current availability, version metadata, file inventory, and licenses against the downloaded package and authoritative repository before processing.

## Confirmed scope

Mindboggle-101 provides 101 anatomically labelled brain datasets drawn from multiple source cohorts. The collection separates:

- individually labelled surfaces and volumes;
- registration templates;
- population atlases.

Phase 1A targets the individual-brains package. The expected useful components include T1-weighted MRI volumes, manually corrected DKT cortical label volumes, label definitions, subject/source mapping, and possibly surface or FreeSurfer products depending on the package.

## Pairing rules

- Prefer skull-stripped T1 MRI with the matching manual DKT label volume for the initial pipeline.
- Pair files only after inspecting the actual downloaded directory and NIfTI headers.
- Keep coordinate spaces consistent. Never mix a native-space image with an MNI-space label.
- Preserve distributed file names in raw storage. Represent normalized names through the manifest rather than renaming original data.

## Label rules

- The DKT cortical protocol represents regions in both hemispheres.
- Treat stored label values as categorical IDs.
- Do not assume sequential IDs or use numeric magnitude as anatomical meaning.
- Preserve background separately.
- Build the authoritative mapping from the package's label-definition material.
- If a later model needs contiguous class indices, store a reversible `original_label_id` to `class_index` mapping instead of overwriting source labels.

## Cohort and leakage cautions

The scans originate from multiple datasets, including OASIS, NKI, and MMRR-related cohorts. Some components involve repeat acquisitions. Use the distributed subject/source mapping to identify participant or source lineage. Keep repeats together in splits and de-duplicate lineage when combining Mindboggle with external datasets.

## Licensing caution

License descriptions can differ between repository-level metadata and notices bundled with particular components. Record both, preserve attribution requirements, and use the most conservative unresolved interpretation until a qualified reviewer confirms permitted use. Do not redistribute raw scans through the skill.
