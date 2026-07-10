param(
    [Parameter(Mandatory = $true, Position = 0, ValueFromRemainingArguments = $true)]
    [string[]]$Commands,

    [string]$WindowTitle = 'BG3 Script Extender Debug Console',

    [string]$WindowTitlePattern = 'BG3.*Script Extender.*Console',

    [int]$InitialDelayMs = 150,

    [int]$BetweenCommandsDelayMs = 120,

    [switch]$KeepClipboard
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
using System.Text;

namespace Win32 {
    public static class NativeMethods {
        public delegate bool EnumWindowsProc(IntPtr hWnd, IntPtr lParam);

        [DllImport("user32.dll")]
        public static extern bool EnumWindows(EnumWindowsProc lpEnumFunc, IntPtr lParam);

        [DllImport("user32.dll", CharSet = CharSet.Unicode)]
        public static extern int GetWindowText(IntPtr hWnd, StringBuilder lpString, int nMaxCount);

        [DllImport("user32.dll")]
        public static extern int GetWindowTextLength(IntPtr hWnd);

        [DllImport("user32.dll")]
        public static extern bool IsWindowVisible(IntPtr hWnd);

        [DllImport("user32.dll")]
        public static extern bool SetForegroundWindow(IntPtr hWnd);
    }
}
'@

function Get-MatchingWindowTitles {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Pattern
    )

    $windowMatches = New-Object System.Collections.ArrayList
    $callback = [Win32.NativeMethods+EnumWindowsProc]{
        param($hWnd, $lParam)

        if (-not [Win32.NativeMethods]::IsWindowVisible($hWnd)) {
            return $true
        }

        $length = [Win32.NativeMethods]::GetWindowTextLength($hWnd)
        if ($length -le 0) {
            return $true
        }

        $buffer = New-Object System.Text.StringBuilder ($length + 1)
        [void][Win32.NativeMethods]::GetWindowText($hWnd, $buffer, $buffer.Capacity)
        $title = $buffer.ToString()
        if ($title -match $Pattern) {
            [void]$windowMatches.Add([pscustomobject]@{ Handle = $hWnd; Title = $title })
        }

        return $true
    }

    [void][Win32.NativeMethods]::EnumWindows($callback, [IntPtr]::Zero)
    return $windowMatches
}

function Focus-TargetWindow {
    param(
        [Parameter(Mandatory = $true)]
        [System.__ComObject]$Shell,

        [Parameter(Mandatory = $true)]
        [string]$ExactTitle,

        [Parameter(Mandatory = $true)]
        [string]$TitlePattern
    )

    if ($Shell.AppActivate($ExactTitle)) {
        return [pscustomobject]@{ Title = $ExactTitle; Handle = [IntPtr]::Zero }
    }

    $windowMatches = @(Get-MatchingWindowTitles -Pattern $TitlePattern)
    if ($windowMatches.Count -eq 0) {
        throw "Could not find an active window titled '$ExactTitle' or matching /$TitlePattern/. Open the SE console first."
    }

    $target = $windowMatches[0]
    [void][Win32.NativeMethods]::SetForegroundWindow($target.Handle)
    [void]$Shell.AppActivate($target.Title)

    return $target
}

function Send-ConsoleKeys {
    param(
        [Parameter(Mandatory = $true)]
        [System.__ComObject]$Shell,

        [Parameter(Mandatory = $true)]
        [string]$Text
    )

    Set-Clipboard -Value $Text
    # SE console often accepts Shift+Insert more reliably than Ctrl+V.
    $Shell.SendKeys('+{INSERT}')
    [System.Threading.Thread]::Sleep(40)
    $Shell.SendKeys('~')
}

$originalClipboard = $null
if (-not $KeepClipboard) {
    try {
        $originalClipboard = Get-Clipboard -Raw
    } catch {
        $originalClipboard = $null
    }
}

$shell = New-Object -ComObject WScript.Shell
$resolvedWindow = Focus-TargetWindow -Shell $shell -ExactTitle $WindowTitle -TitlePattern $WindowTitlePattern

[System.Threading.Thread]::Sleep($InitialDelayMs)

# Prime the SE console into input mode (equivalent to pressing Enter once).
$shell.SendKeys('~')
[System.Threading.Thread]::Sleep(80)

try {
    foreach ($command in $Commands) {
        if ([string]::IsNullOrWhiteSpace($command)) {
            continue
        }

        if ($resolvedWindow.Handle -ne [IntPtr]::Zero) {
            [void][Win32.NativeMethods]::SetForegroundWindow($resolvedWindow.Handle)
        } else {
            [void]$shell.AppActivate($resolvedWindow.Title)
        }

        [System.Threading.Thread]::Sleep(40)
        Send-ConsoleKeys -Shell $shell -Text $command
        [System.Threading.Thread]::Sleep($BetweenCommandsDelayMs)
    }
} finally {
    if (-not $KeepClipboard) {
        try {
            if ($null -ne $originalClipboard) {
                Set-Clipboard -Value $originalClipboard
            }
        } catch {
        }
    }
}
