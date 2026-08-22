[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$repoRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
$archivePath = Join-Path $repoRoot 'data\raw\mindboggle101\archives\volumes\Extra-18_volumes.tar.gz'
$extractTarget = Join-Path $repoRoot 'data\raw\mindboggle101\extracted\Extra-18'
$volumeRoot = Join-Path $extractTarget 'Extra-18_volumes'
$subjectListPath = Join-Path $repoRoot 'data\raw\mindboggle101\metadata\subject_list_Mindboggle101.txt'
$subjectSourcesPath = Join-Path $repoRoot 'data\raw\mindboggle101\metadata\subject_sources_Mindboggle101.txt'
$outputDir = Join-Path $repoRoot 'data\derived\manifests'
$manifestPath = Join-Path $outputDir 'extra18_scan_inventory.csv'
$structurePath = Join-Path $outputDir 'extra18_extracted_structure.txt'

foreach ($requiredPath in @($archivePath, $volumeRoot, $subjectListPath, $subjectSourcesPath)) {
    if (-not (Test-Path -LiteralPath $requiredPath)) {
        throw "Required path is missing: $requiredPath"
    }
}

function ConvertTo-RepoRelativePath {
    param([Parameter(Mandatory)][string]$Path)
    $fullPath = [System.IO.Path]::GetFullPath($Path)
    if (-not $fullPath.StartsWith($repoRoot + [System.IO.Path]::DirectorySeparatorChar, [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Path is outside the repository: $fullPath"
    }
    return $fullPath.Substring($repoRoot.Length + 1).Replace('\', '/')
}

$subjectList = @(
    Get-Content -LiteralPath $subjectListPath |
        ForEach-Object { $_.Trim() } |
        Where-Object { $_ }
)
$subjectListSet = [System.Collections.Generic.HashSet[string]]::new([System.StringComparer]::Ordinal)
foreach ($subject in $subjectList) {
    if (-not $subjectListSet.Add($subject)) {
        throw "Duplicate subject in subject list: $subject"
    }
}

$sourceBySubject = @{}
$inSourceTable = $false
foreach ($line in Get-Content -LiteralPath $subjectSourcesPath) {
    if ($line -match '^---+$') {
        $inSourceTable = $true
        continue
    }
    if (-not $inSourceTable) { continue }
    if ($line -match '^Repeat scans:') { break }
    if ([string]::IsNullOrWhiteSpace($line)) { continue }
    if ($line -notmatch '^([^,]+),\s*([^,]*),\s*([^,]*),\s*([^,]*),\s*(.+)$') {
        throw "Could not parse subject-source row: $line"
    }
    $subject = $Matches[1].Trim()
    if ($sourceBySubject.ContainsKey($subject)) {
        throw "Duplicate subject in subject-source metadata: $subject"
    }
    $sourceBySubject[$subject] = $Matches[5].Trim()
}

$subjectDirectories = @(
    Get-ChildItem -LiteralPath $volumeRoot -Directory -Force |
        Sort-Object Name
)
$subjectIds = @($subjectDirectories | ForEach-Object { $_.Name })
$subjectListMissing = @($subjectIds | Where-Object { -not $subjectListSet.Contains($_) })
$subjectSourceMissing = @($subjectIds | Where-Object { -not $sourceBySubject.ContainsKey($_) })

$rows = [System.Collections.Generic.List[object]]::new()
$missingPairs = [System.Collections.Generic.List[string]]::new()
$spaces = @(
    [pscustomobject]@{
        Name = 'native'
        MriName = 't1weighted_brain.nii.gz'
        LabelName = 'labels.DKT31.manual.nii.gz'
        AlternativeMriName = 't1weighted.nii.gz'
        AlternativeLabelName = 'labels.DKT31.manual+aseg.nii.gz'
        AffineName = $null
    },
    [pscustomobject]@{
        Name = 'MNI152'
        MriName = 't1weighted_brain.MNI152.nii.gz'
        LabelName = 'labels.DKT31.manual.MNI152.nii.gz'
        AlternativeMriName = 't1weighted.MNI152.nii.gz'
        AlternativeLabelName = 'labels.DKT31.manual+aseg.MNI152.nii.gz'
        AffineName = 't1weighted_brain.MNI152.affine.txt'
    }
)

foreach ($subjectDirectory in $subjectDirectories) {
    $subject = $subjectDirectory.Name
    foreach ($space in $spaces) {
        $mriPath = Join-Path $subjectDirectory.FullName $space.MriName
        $labelPath = Join-Path $subjectDirectory.FullName $space.LabelName
        $missing = @()
        if (-not (Test-Path -LiteralPath $mriPath -PathType Leaf)) { $missing += $space.MriName }
        if (-not (Test-Path -LiteralPath $labelPath -PathType Leaf)) { $missing += $space.LabelName }
        if ($missing.Count -gt 0) {
            $status = 'missing'
            $exclusionReason = 'Missing required file(s): ' + ($missing -join '; ')
            $missingPairs.Add("$subject/$($space.Name): $exclusionReason")
        }
        else {
            $status = 'matched_pending_nifti_qc'
            $exclusionReason = $null
        }

        $alternatives = "Additional same-space NIfTI files: $($space.AlternativeMriName); $($space.AlternativeLabelName)."
        if ($space.AffineName) {
            $alternatives += " Ancillary transform: $($space.AffineName)."
        }
        $notes = "Preferred skull-stripped T1 and manual DKT31 cortical label; matched by supplied subject ID, directory, filename, and $($space.Name) space. $alternatives Header and voxel-level QC not performed."
        $sourceSubjectId = if ($sourceBySubject.ContainsKey($subject)) { $sourceBySubject[$subject] } else { $null }

        $rows.Add([pscustomobject][ordered]@{
            scan_id = "Extra-18:${subject}:$($space.Name)"
            participant_id = $subject
            source_subject_id = $sourceSubjectId
            cohort = 'Extra-18'
            mri_path = if (Test-Path -LiteralPath $mriPath -PathType Leaf) { ConvertTo-RepoRelativePath $mriPath } else { $null }
            label_path = if (Test-Path -LiteralPath $labelPath -PathType Leaf) { ConvertTo-RepoRelativePath $labelPath } else { $null }
            space = $space.Name
            pairing_status = $status
            exclusion_reason = $exclusionReason
            notes = $notes
        })
    }
}

New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
$rows | Export-Csv -LiteralPath $manifestPath -NoTypeInformation -Encoding UTF8

$treeItems = @(Get-ChildItem -LiteralPath $extractTarget -Recurse -Force | Sort-Object FullName)
$structureLines = [System.Collections.Generic.List[string]]::new()
$structureLines.Add('# Exact extracted directory structure for Extra-18_volumes.tar.gz')
$structureLines.Add('# Paths are repository-relative; directory paths end with /.')
$structureLines.Add("# Recorded: 2026-08-23")
$structureLines.Add("type`tpath`tsize_bytes")
foreach ($item in $treeItems) {
    $relativePath = ConvertTo-RepoRelativePath $item.FullName
    if ($item.PSIsContainer) {
        $structureLines.Add("directory`t$relativePath/`t")
    }
    else {
        $structureLines.Add("file`t$relativePath`t$($item.Length)")
    }
}
[System.IO.File]::WriteAllLines($structurePath, $structureLines, [System.Text.UTF8Encoding]::new($false))

$tarMembers = @(tar -tzf $archivePath)
if ($LASTEXITCODE -ne 0) { throw "Could not re-list archive: exit $LASTEXITCODE" }
$archiveRelativeItems = @($tarMembers | ForEach-Object { $_.TrimEnd('/').Replace('\', '/') } | Sort-Object -Unique)
$diskRelativeItems = @(
    $treeItems |
        ForEach-Object { (ConvertTo-RepoRelativePath $_.FullName).Substring((ConvertTo-RepoRelativePath $extractTarget).Length + 1) } |
        Sort-Object -Unique
)
$missingFromDisk = @($archiveRelativeItems | Where-Object { $_ -notin $diskRelativeItems })
$unexpectedOnDisk = @($diskRelativeItems | Where-Object { $_ -notin $archiveRelativeItems })

$allFiles = @(Get-ChildItem -LiteralPath $volumeRoot -Recurse -File -Force)
$niftiFiles = @($allFiles | Where-Object { $_.Name -match '\.nii(\.gz)?$' })
$nativeNifti = @($niftiFiles | Where-Object { $_.Name -notmatch '\.MNI152\.nii(\.gz)?$' })
$mniNifti = @($niftiFiles | Where-Object { $_.Name -match '\.MNI152\.nii(\.gz)?$' })
$nonStrippedT1 = @($niftiFiles | Where-Object { $_.Name -in @('t1weighted.nii.gz', 't1weighted.MNI152.nii.gz') })
$skullStrippedT1 = @($niftiFiles | Where-Object { $_.Name -in @('t1weighted_brain.nii.gz', 't1weighted_brain.MNI152.nii.gz') })
$manualDkt = @($niftiFiles | Where-Object { $_.Name -in @('labels.DKT31.manual.nii.gz', 'labels.DKT31.manual.MNI152.nii.gz') })
$manualDktAseg = @($niftiFiles | Where-Object { $_.Name -in @('labels.DKT31.manual+aseg.nii.gz', 'labels.DKT31.manual+aseg.MNI152.nii.gz') })
$classifiedNifti = @($nonStrippedT1 + $skullStrippedT1 + $manualDkt + $manualDktAseg)
$otherNifti = @($niftiFiles | Where-Object { $_.FullName -notin $classifiedNifti.FullName })
$rootFiles = @(Get-ChildItem -LiteralPath $volumeRoot -File -Force | Sort-Object Name)

Write-Output "manifest=$((ConvertTo-RepoRelativePath $manifestPath))"
Write-Output "structure_record=$((ConvertTo-RepoRelativePath $structurePath))"
Write-Output "extracted_file_count=$($allFiles.Count)"
Write-Output "nifti_file_count=$($niftiFiles.Count)"
Write-Output "subject_count=$($subjectIds.Count)"
Write-Output "native_nifti_count=$($nativeNifti.Count)"
Write-Output "mni152_nifti_count=$($mniNifti.Count)"
Write-Output "non_stripped_t1_count=$($nonStrippedT1.Count)"
Write-Output "skull_stripped_t1_count=$($skullStrippedT1.Count)"
Write-Output "manual_dkt_count=$($manualDkt.Count)"
Write-Output "manual_dkt_plus_aseg_count=$($manualDktAseg.Count)"
Write-Output "other_nifti_count=$($otherNifti.Count)"
Write-Output "native_pair_count=$(@($rows | Where-Object { $_.space -eq 'native' -and $_.pairing_status -eq 'matched_pending_nifti_qc' }).Count)"
Write-Output "mni152_pair_count=$(@($rows | Where-Object { $_.space -eq 'MNI152' -and $_.pairing_status -eq 'matched_pending_nifti_qc' }).Count)"
Write-Output "missing_or_ambiguous_pair_count=$($missingPairs.Count)"
Write-Output "subject_list_missing_count=$($subjectListMissing.Count)"
Write-Output "subject_source_missing_count=$($subjectSourceMissing.Count)"
Write-Output "archive_members_missing_from_disk=$($missingFromDisk.Count)"
Write-Output "unexpected_disk_paths=$($unexpectedOnDisk.Count)"
Write-Output "unexpected_root_files=$($rootFiles.Name -join ';')"
Write-Output "subjects=$($subjectIds -join ';')"
