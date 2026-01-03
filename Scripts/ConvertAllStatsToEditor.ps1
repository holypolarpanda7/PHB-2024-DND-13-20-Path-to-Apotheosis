# ConvertAllStatsToEditor.ps1
# Converts all Stats .txt files to .stats format for BG3 Toolkit

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

$StatsDir = Join-Path $projectRoot 'Public\PHB2024_DND_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa\Stats\Generated\Data'
$OutputDir = Join-Path $projectRoot 'Editor\Mods\PHB2024_DND_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa\Stats\Stats'

# Create directory if not exists
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

# File type to stat_object_definition_id mapping
$statObjectDefIds = @{
    'Passive'      = '3e76b74c-a5ae-4268-944a-aa9c31e2185e'
    'Spell_Shout'  = '133a0da0-5e42-42ee-b5ed-f3839de5bf38'
    'Spell_Target' = '76e3fabd-0294-4e64-a3c7-51230b6e3a97'
    'Spell_Zone'   = '8a77dbfd-8e23-4eda-b579-07faad354d31'
    'Status_BOOST' = 'a9e6a22a-d154-4fb7-8449-e899b9ea0e7a'
}

# Function to generate deterministic UUID based on name
function Get-DeterministicUuid {
    param([string]$prefix, [string]$name)
    $md5 = [System.Security.Cryptography.MD5]::Create()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes("PHB2024_Apo_${prefix}_${name}")
    $hash = $md5.ComputeHash($bytes)
    $guidStr = "{0:x2}{1:x2}{2:x2}{3:x2}-{4:x2}{5:x2}-{6:x2}{7:x2}-{8:x2}{9:x2}-{10:x2}{11:x2}{12:x2}{13:x2}{14:x2}{15:x2}" -f `
        $hash[0], $hash[1], $hash[2], $hash[3], $hash[4], $hash[5], $hash[6], $hash[7], `
        $hash[8], $hash[9], $hash[10], $hash[11], $hash[12], $hash[13], $hash[14], $hash[15]
    return $guidStr
}

# Function to escape XML special characters
function Escape-Xml {
    param([string]$text)
    if ($null -eq $text) { return "" }
    return $text -replace '&', '&amp;' -replace '<', '&lt;' -replace '>', '&gt;' -replace '"', '&quot;'
}

# Function to parse a Stats txt file
function Parse-StatsTxt {
    param([string]$content)
    
    $entries = @()
    $currentEntry = $null
    $lines = $content -split '[\r\n]+'
    
    foreach ($line in $lines) {
        # Skip comments and empty lines
        if ($line -match '^\s*//' -or $line -match '^\s*$') { continue }
        
        if ($line -match '^new entry "(.+)"') {
            if ($null -ne $currentEntry -and $currentEntry.ContainsKey('Name')) {
                $entries += $currentEntry
            }
            $currentEntry = @{ Name = $matches[1]; Data = @{}; Using = $null; Type = $null }
        }
        elseif ($line -match '^type "(.+)"') {
            if ($null -ne $currentEntry) { $currentEntry['Type'] = $matches[1] }
        }
        elseif ($line -match '^using "(.+)"') {
            if ($null -ne $currentEntry) { $currentEntry['Using'] = $matches[1] }
        }
        elseif ($line -match '^data "(.+?)" "(.*)"') {
            if ($null -ne $currentEntry) { $currentEntry.Data[$matches[1]] = $matches[2] }
        }
    }
    # Add last entry
    if ($null -ne $currentEntry -and $currentEntry.ContainsKey('Name')) {
        $entries += $currentEntry
    }
    
    return $entries
}

# Function to build XML for a stat type
function Build-StatsXml {
    param(
        [array]$entries,
        [string]$statDefId,
        [string]$fileType
    )
    
    $sb = [System.Text.StringBuilder]::new()
    [void]$sb.AppendLine('<?xml version="1.0" encoding="utf-8"?>')
    [void]$sb.AppendLine("<stats stat_object_definition_id=`"$statDefId`">")
    [void]$sb.AppendLine("  <stat_objects>")
    
    foreach ($entry in $entries) {
        $uuid = Get-DeterministicUuid -prefix $fileType -name $entry.Name
        
        [void]$sb.AppendLine("    <stat_object is_substat=`"false`">")
        [void]$sb.AppendLine("      <fields>")
        [void]$sb.AppendLine("        <field name=`"UUID`" type=`"IdTableFieldDefinition`" value=`"$uuid`" />")
        [void]$sb.AppendLine("        <field name=`"Name`" type=`"NameTableFieldDefinition`" value=`"$($entry.Name)`" />")
        
        # Add Using if present
        if ($entry.Using) {
            [void]$sb.AppendLine("        <field name=`"Using`" type=`"BaseClassTableFieldDefinition`" value=`"$($entry.Using)`" />")
        }
        
        # Add all data fields
        foreach ($key in $entry.Data.Keys) {
            $value = Escape-Xml $entry.Data[$key]
            
            # Handle different field types
            switch ($key) {
                'DisplayName' {
                    # Extract handle and version from format "handle;version"
                    if ($value -match '(.+);(\d+)') {
                        $handle = $matches[1]
                        $version = $matches[2]
                    } else {
                        $handle = $value
                        $version = "1"
                    }
                    [void]$sb.AppendLine("        <field name=`"DisplayName`" type=`"TranslatedStringTableFieldDefinition`" value=`"`" handle=`"$handle`" version=`"$version`" />")
                }
                'Description' {
                    if ($value -match '(.+);(\d+)') {
                        $handle = $matches[1]
                        $version = $matches[2]
                    } else {
                        $handle = $value
                        $version = "1"
                    }
                    [void]$sb.AppendLine("        <field name=`"Description`" type=`"TranslatedStringTableFieldDefinition`" value=`"`" handle=`"$handle`" version=`"$version`" />")
                }
                'ExtraDescription' {
                    if ($value -match '(.+);(\d+)') {
                        $handle = $matches[1]
                        $version = $matches[2]
                    } else {
                        $handle = $value
                        $version = "1"
                    }
                    [void]$sb.AppendLine("        <field name=`"ExtraDescription`" type=`"TranslatedStringTableFieldDefinition`" value=`"`" handle=`"$handle`" version=`"$version`" />")
                }
                'Properties' {
                    # Enumeration list - determine type based on file type
                    $enumType = switch ($fileType) {
                        'Passive' { 'PassiveFlags' }
                        'Status_BOOST' { 'StatusPropertyFlags' }
                        default { 'SpellFlags' }
                    }
                    [void]$sb.AppendLine("        <field name=`"Properties`" type=`"EnumerationListTableFieldDefinition`" value=`"$value`" enumeration_type_name=`"$enumType`" version=`"1`" />")
                }
                'SpellFlags' {
                    [void]$sb.AppendLine("        <field name=`"SpellFlags`" type=`"EnumerationListTableFieldDefinition`" value=`"$value`" enumeration_type_name=`"SpellFlags`" version=`"1`" />")
                }
                'StatusPropertyFlags' {
                    [void]$sb.AppendLine("        <field name=`"StatusPropertyFlags`" type=`"EnumerationListTableFieldDefinition`" value=`"$value`" enumeration_type_name=`"StatusPropertyFlags`" version=`"1`" />")
                }
                'StatsFunctorContext' {
                    [void]$sb.AppendLine("        <field name=`"StatsFunctorContext`" type=`"EnumerationListTableFieldDefinition`" value=`"$value`" enumeration_type_name=`"StatsFunctorContext`" version=`"1`" />")
                }
                'BoostContext' {
                    [void]$sb.AppendLine("        <field name=`"BoostContext`" type=`"EnumerationListTableFieldDefinition`" value=`"$value`" enumeration_type_name=`"StatsFunctorContext`" version=`"1`" />")
                }
                'StatusType' {
                    [void]$sb.AppendLine("        <field name=`"StatusType`" type=`"EnumerationTableFieldDefinition`" value=`"$value`" enumeration_type_name=`"StatusType`" version=`"1`" />")
                }
                'SpellType' {
                    [void]$sb.AppendLine("        <field name=`"SpellType`" type=`"EnumerationTableFieldDefinition`" value=`"$value`" enumeration_type_name=`"SpellType`" version=`"1`" />")
                }
                'SpellSchool' {
                    [void]$sb.AppendLine("        <field name=`"SpellSchool`" type=`"EnumerationTableFieldDefinition`" value=`"$value`" enumeration_type_name=`"SpellSchool`" version=`"1`" />")
                }
                'Level' {
                    [void]$sb.AppendLine("        <field name=`"Level`" type=`"IntTableFieldDefinition`" value=`"$value`" />")
                }
                'AreaRadius' {
                    [void]$sb.AppendLine("        <field name=`"AreaRadius`" type=`"IntTableFieldDefinition`" value=`"$value`" />")
                }
                'TargetRadius' {
                    [void]$sb.AppendLine("        <field name=`"TargetRadius`" type=`"StringTableFieldDefinition`" value=`"$value`" />")
                }
                'MemoryCost' {
                    [void]$sb.AppendLine("        <field name=`"MemoryCost`" type=`"IntTableFieldDefinition`" value=`"$value`" />")
                }
                default {
                    # Default to StringTableFieldDefinition
                    [void]$sb.AppendLine("        <field name=`"$key`" type=`"StringTableFieldDefinition`" value=`"$value`" />")
                }
            }
        }
        
        [void]$sb.AppendLine("      </fields>")
        [void]$sb.AppendLine("    </stat_object>")
    }
    
    [void]$sb.AppendLine("  </stat_objects>")
    [void]$sb.AppendLine("</stats>")
    
    return $sb.ToString()
}

# Process each file type
$filesToProcess = @('Passive', 'Spell_Shout', 'Spell_Target', 'Spell_Zone', 'Status_BOOST')

foreach ($fileType in $filesToProcess) {
    $inputFile = Join-Path $StatsDir "$fileType.txt"
    $outputFile = Join-Path $OutputDir "$fileType.stats"
    
    if (-not (Test-Path $inputFile)) {
        Write-Host "Skipping $fileType - file not found: $inputFile"
        continue
    }
    
    Write-Host "Processing $fileType..."
    
    # Read and parse
    $content = Get-Content $inputFile -Raw
    $entries = Parse-StatsTxt -content $content
    
    if ($entries.Count -eq 0) {
        Write-Host "  No entries found in $fileType.txt"
        continue
    }
    
    # Get stat_object_definition_id
    $statDefId = $statObjectDefIds[$fileType]
    if (-not $statDefId) {
        Write-Host "  Unknown file type: $fileType"
        continue
    }
    
    # Build XML
    $xml = Build-StatsXml -entries $entries -statDefId $statDefId -fileType $fileType
    
    # Write output (UTF-8 no BOM)
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText($outputFile, $xml, $utf8NoBom)
    
    Write-Host "  Created $fileType.stats with $($entries.Count) entries"
}

Write-Host "`nDone! All stats files converted."
