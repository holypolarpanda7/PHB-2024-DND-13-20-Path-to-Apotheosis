# ConvertPassiveToStats.ps1
# Converts Passive.txt to Passive.stats format for BG3 Toolkit

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

$PassiveTxtPath = Join-Path $projectRoot 'Public\PHB2024_DND_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa\Stats\Generated\Data\Passive.txt'
$OutputDir = Join-Path $projectRoot 'Editor\Mods\PHB2024_DND_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa\Stats\Stats'
$OutputFile = Join-Path $OutputDir 'Passive.stats'

# Create directory if not exists
New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null

# Read the Passive.txt file
$content = Get-Content $PassiveTxtPath -Raw

# Parse entries
$entries = @()
$currentEntry = @{}
$lines = $content -split '[\r\n]+'

foreach ($line in $lines) {
    if ($line -match '^new entry "(.+)"') {
        if ($currentEntry.Count -gt 0 -and $currentEntry.ContainsKey('Name')) {
            $entries += $currentEntry
        }
        $currentEntry = @{ Name = $matches[1]; Data = @{} }
    }
    elseif ($line -match '^type "(.+)"') {
        $currentEntry['Type'] = $matches[1]
    }
    elseif ($line -match '^using "(.+)"') {
        $currentEntry['Using'] = $matches[1]
    }
    elseif ($line -match '^data "(.+?)" "(.*)\"') {
        $currentEntry.Data[$matches[1]] = $matches[2]
    }
}
# Add last entry
if ($currentEntry.Count -gt 0 -and $currentEntry.ContainsKey('Name')) {
    $entries += $currentEntry
}

Write-Host "Found $($entries.Count) passive entries to convert"

# Generate UUIDs deterministically based on name
function Get-DeterministicUuid {
    param([string]$name)
    $md5 = [System.Security.Cryptography.MD5]::Create()
    $bytes = [System.Text.Encoding]::UTF8.GetBytes('PHB2024_Apotheosis_Passive_' + $name)
    $hash = $md5.ComputeHash($bytes)
    # Format as GUID manually: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
    $guidStr = "{0:x2}{1:x2}{2:x2}{3:x2}-{4:x2}{5:x2}-{6:x2}{7:x2}-{8:x2}{9:x2}-{10:x2}{11:x2}{12:x2}{13:x2}{14:x2}{15:x2}" -f `
        $hash[0], $hash[1], $hash[2], $hash[3], $hash[4], $hash[5], $hash[6], $hash[7], `
        $hash[8], $hash[9], $hash[10], $hash[11], $hash[12], $hash[13], $hash[14], $hash[15]
    return $guidStr
}

# Build XML
$xml = @'
<?xml version="1.0" encoding="utf-8"?>
<stats stat_object_definition_id="3e76b74c-a5ae-4268-944a-aa9c31e2185e">
  <stat_objects>
'@

$handleCounter = 0
foreach ($entry in $entries) {
    $uuid = Get-DeterministicUuid -name $entry.Name
    $displayHandle = 'h' + $handleCounter.ToString('x8') + 'g' + ($handleCounter + 1).ToString('x4')
    $descHandle = 'h' + $handleCounter.ToString('x8') + 'g' + ($handleCounter + 2).ToString('x4')
    $handleCounter += 3
    
    $xml += "`n    <stat_object is_substat=`"false`">`n"
    $xml += "      <fields>`n"
    $xml += "        <field name=`"UUID`" type=`"IdTableFieldDefinition`" value=`"$uuid`"></field>`n"
    $xml += "        <field name=`"Name`" type=`"NameTableFieldDefinition`" value=`"$($entry.Name)`"></field>`n"
    
    # Add DisplayName
    if ($entry.Data.ContainsKey('DisplayName')) {
        $handle = $entry.Data['DisplayName']
        $version = '1'
        $xml += "        <field name=`"DisplayName`" type=`"TranslatedStringTableFieldDefinition`" value=`"`" handle=`"$handle`" version=`"$version`"></field>`n"
    } else {
        $xml += "        <field name=`"DisplayName`" type=`"TranslatedStringTableFieldDefinition`" value=`"`" handle=`"$displayHandle`" version=`"1`"></field>`n"
    }
    
    # Add Description
    if ($entry.Data.ContainsKey('Description')) {
        $handle = $entry.Data['Description']
        $version = '1'
        $xml += "        <field name=`"Description`" type=`"TranslatedStringTableFieldDefinition`" value=`"`" handle=`"$handle`" version=`"$version`"></field>`n"
    } else {
        $xml += "        <field name=`"Description`" type=`"TranslatedStringTableFieldDefinition`" value=`"`" handle=`"$descHandle`" version=`"1`"></field>`n"
    }
    
    # Add Icon
    if ($entry.Data.ContainsKey('Icon')) {
        $xml += "        <field name=`"Icon`" type=`"StringTableFieldDefinition`" value=`"$($entry.Data['Icon'])`"></field>`n"
    }
    
    # Add Properties
    if ($entry.Data.ContainsKey('Properties')) {
        $xml += "        <field name=`"Properties`" type=`"EnumerationListTableFieldDefinition`" value=`"$($entry.Data['Properties'])`" enumeration_type_name=`"PassiveFlags`" version=`"1`"></field>`n"
    }
    
    # Add Boosts if present
    if ($entry.Data.ContainsKey('Boosts')) {
        $boosts = $entry.Data['Boosts'] -replace '&', '&amp;' -replace '<', '&lt;' -replace '>', '&gt;'
        $xml += "        <field name=`"Boosts`" type=`"StringTableFieldDefinition`" value=`"$boosts`"></field>`n"
    }
    
    # Add BoostContext if present
    if ($entry.Data.ContainsKey('BoostContext')) {
        $xml += "        <field name=`"BoostContext`" type=`"EnumerationListTableFieldDefinition`" value=`"$($entry.Data['BoostContext'])`" enumeration_type_name=`"StatsFunctorContext`" version=`"1`"></field>`n"
    }
    
    # Add StatsFunctorContext if present
    if ($entry.Data.ContainsKey('StatsFunctorContext')) {
        $xml += "        <field name=`"StatsFunctorContext`" type=`"EnumerationListTableFieldDefinition`" value=`"$($entry.Data['StatsFunctorContext'])`" enumeration_type_name=`"StatsFunctorContext`" version=`"1`"></field>`n"
    }
    
    # Add StatsFunctors if present
    if ($entry.Data.ContainsKey('StatsFunctors')) {
        $functors = $entry.Data['StatsFunctors'] -replace '&', '&amp;' -replace '<', '&lt;' -replace '>', '&gt;'
        $xml += "        <field name=`"StatsFunctors`" type=`"StringTableFieldDefinition`" value=`"$functors`"></field>`n"
    }
    
    # Add Conditions if present
    if ($entry.Data.ContainsKey('Conditions')) {
        $conditions = $entry.Data['Conditions'] -replace '&', '&amp;' -replace '<', '&lt;' -replace '>', '&gt;'
        $xml += "        <field name=`"Conditions`" type=`"StringTableFieldDefinition`" value=`"$conditions`"></field>`n"
    }
    
    $xml += "      </fields>`n"
    $xml += "    </stat_object>`n"
}

$xml += @'

  </stat_objects>
</stats>
'@

# Write output
Set-Content -Path $OutputFile -Value $xml -Encoding UTF8
Write-Host "Created Passive.stats at: $OutputFile"
Write-Host "Total entries: $($entries.Count)"
