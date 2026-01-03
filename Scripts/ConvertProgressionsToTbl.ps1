# ConvertProgressionsToTbl.ps1
# Converts Progressions.lsx to Progressions.tbl with proper toolkit format

param(
    [string]$InputPath = "..\Public\PHB2024_DND_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa\Progressions\Progressions.lsx",
    [string]$OutputPath = "..\Editor\Mods\PHB2024_DND_13-20_PathtoApotheosis_1467c26f-e7bb-49d1-d980-6e033aea04fa\Progressions\Progressions.tbl"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$inputFile = Join-Path $scriptDir $InputPath
$outputFile = Join-Path $scriptDir $OutputPath

Write-Host "Reading Progressions.lsx from: $inputFile"

if (-not (Test-Path $inputFile)) {
    Write-Error "Input file not found: $inputFile"
    exit 1
}

[xml]$lsx = Get-Content $inputFile -Encoding UTF8

# stat_object_definition_id for Progressions (NOT ProgressionDescriptions!)
$statObjectDefId = "53912403-fe14-4ce0-89aa-96acb1dee21a"

# Build the output XML
$sb = [System.Text.StringBuilder]::new()
[void]$sb.AppendLine('<?xml version="1.0" encoding="utf-8"?>')
[void]$sb.AppendLine("<stats stat_object_definition_id=`"$statObjectDefId`">")
[void]$sb.AppendLine("  <stat_objects>")

$progressionNodes = $lsx.save.region.node.children.node | Where-Object { $_.id -eq "Progression" }
$count = 0

foreach ($prog in $progressionNodes) {
    $attributes = @{}
    
    # Extract all attributes from the progression node
    foreach ($attr in $prog.attribute) {
        $attributes[$attr.id] = $attr.value
    }
    
    # Get required values
    $uuid = $attributes["UUID"]
    $originalName = $attributes["Name"]
    $tableUUID = $attributes["TableUUID"]
    $level = $attributes["Level"]
    $progressionType = $attributes["ProgressionType"]
    
    # Optional values
    $allowImprovement = if ($attributes["AllowImprovement"]) { $attributes["AllowImprovement"] } else { "false" }
    $boosts = if ($attributes["Boosts"]) { $attributes["Boosts"] } else { "" }
    $passivesAdded = if ($attributes["PassivesAdded"]) { $attributes["PassivesAdded"] } else { "" }
    $passivesRemoved = if ($attributes["PassivesRemoved"]) { $attributes["PassivesRemoved"] } else { "" }
    $selectors = if ($attributes["Selectors"]) { $attributes["Selectors"] } else { "" }
    $isMulticlass = if ($attributes["IsMulticlass"]) { $attributes["IsMulticlass"] } else { "false" }
    $subClasses = if ($attributes["SubClasses"]) { $attributes["SubClasses"] } else { "" }
    
    # Generate unique Name for toolkit (required to be unique) and keep original as FSName
    $name = "PHB2024_Apo_$count"
    $fsName = $originalName
    
    # Capitalize boolean values for toolkit
    $allowImprovementBool = if ($allowImprovement -eq "true") { "True" } else { "False" }
    
    [void]$sb.AppendLine("    <stat_object is_substat=`"false`">")
    [void]$sb.AppendLine("      <fields>")
    [void]$sb.AppendLine("        <field name=`"Name`" type=`"NameTableFieldDefinition`" value=`"$name`" />")
    [void]$sb.AppendLine("        <field name=`"UUID`" type=`"IdTableFieldDefinition`" value=`"$uuid`" />")
    [void]$sb.AppendLine("        <field name=`"TableUUID`" type=`"GuidTableFieldDefinition`" value=`"$tableUUID`" />")
    [void]$sb.AppendLine("        <field name=`"FSName`" type=`"StringTableFieldDefinition`" value=`"$fsName`" />")
    [void]$sb.AppendLine("        <field name=`"Level`" type=`"ByteTableFieldDefinition`" value=`"$level`" />")
    [void]$sb.AppendLine("        <field name=`"ProgressionType`" type=`"ByteTableFieldDefinition`" value=`"$progressionType`" />")
    
    # Only include optional fields if they have values (matching All-in-One format)
    if ($allowImprovement -eq "true") {
        [void]$sb.AppendLine("        <field name=`"AllowImprovement`" type=`"BoolTableFieldDefinition`" value=`"True`" />")
    }
    if ($boosts) {
        [void]$sb.AppendLine("        <field name=`"Boosts`" type=`"StringTableFieldDefinition`" value=`"$boosts`" />")
    }
    if ($passivesAdded) {
        [void]$sb.AppendLine("        <field name=`"PassivesAdded`" type=`"StringTableFieldDefinition`" value=`"$passivesAdded`" />")
    }
    if ($selectors) {
        [void]$sb.AppendLine("        <field name=`"Selectors`" type=`"StringTableFieldDefinition`" value=`"$selectors`" />")
    }
    
    [void]$sb.AppendLine("      </fields>")
    [void]$sb.AppendLine("    </stat_object>")
    
    $count++
}

[void]$sb.AppendLine("  </stat_objects>")
[void]$sb.AppendLine("</stats>")

# Ensure output directory exists
$outputDir = Split-Path -Parent $outputFile
if (-not (Test-Path $outputDir)) {
    New-Item -ItemType Directory -Path $outputDir -Force | Out-Null
}

# Write with UTF-8 encoding (no BOM)
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($outputFile, $sb.ToString(), $utf8NoBom)

Write-Host "Generated Progressions.tbl with $count progressions"
Write-Host "Output: $outputFile"
