param(
    [string]$Scenario = '',
    [string]$Exe = '',
    [switch]$Check
)
# Generic bisection for any bug in the decomp build.
#
# The protocol and the files are the ones of the v50 animation search, but nothing is animation-specific any
# more: the test is described by bisect_scenario.txt and every run is judged by one answer - "is the bug there?".
#
#   Control A: every generated replacement on   -> the bug must be there  (answer y)
#   Control B: every generated replacement off  -> the bug must be gone   (answer n)
#              (only hand-written code stays on: the engine, src/fixed, the harness)
#   Search:    binary search over toggle_list.txt for the first function that, switched on, brings the bug back
#   Confirm:   everything on except the found function -> the bug must be gone
#
# After every run the script prints how many replacements were really switched on (decomp_toggle.log) and the
# tail of decomp_debug.log, and copies the log tail, decomp_toggle.txt, testinput.txt and every BMP the run wrote
# into bisect_shots\<step>\.
#
# The state files (bisect_*.txt) belong to one scenario + toggle_list.txt + exe: when any of them changes, the old
# files are moved to bisect_old_<date>\ instead of being read as this search's results.
#
# The scenario file (default bisect_scenario.txt next to this script, or -Scenario FILE):
#   [note]    what to do / watch during the run (printed before the game starts)
#   [input]   lines for testinput.txt, exactly as the exe reads them:
#                 MS loadsave NAME      load a saved game (from Saves\NAME.sav)
#                 L MS lua CODE         run CODE L MS after the save has loaded
#                 MS lua CODE           run CODE MS after the first frame
#                 MS click X Y          click at X,Y     MS key VK / MS dik N / MS hold N MS   keyboard
#             "0 skipintro" and "0 fastcam" (the intro skip and the battle camera flyby skip) are always added.
#   [force]   generated addresses that must stay on in every step (usually empty: hand-written code is always on)
#
# -Check prints the parsed scenario and exits without starting the game.
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $Scenario) { $Scenario = Join-Path $dir 'bisect_scenario.txt' }
if (-not (Test-Path -LiteralPath $Scenario)) {
    Write-Host "Scenario not found: $Scenario"
    Write-Host "The scenario file describes the test (note, testinput lines, forced functions); see"
    Write-Host "bisect_scenario.txt next to this script.  Another save game: put a line '0 loadsave NAME'"
    Write-Host "into its [input] section (there is no -Save argument any more)."
    exit 1
}

# the debug exe: a --toggle build is required (the plain ATThrone.exe ignores decomp_toggle.txt)
$exe = ''
if ($Exe) {
    $exe = if ([System.IO.Path]::IsPathRooted($Exe)) { $Exe } else { Join-Path $dir $Exe }
} else {
    foreach ($n in @('ATThrone_auto_debug.exe', 'ATThrone_debug.exe')) {
        $p = Join-Path $dir $n
        if (Test-Path -LiteralPath $p) { $exe = $p; break }
    }
}
if (-not $exe -or -not (Test-Path -LiteralPath $exe)) {
    Write-Host "No --toggle debug exe next to this script (ATThrone_debug.exe or ATThrone_auto_debug.exe)."
    Write-Host "Pass the right one with -Exe NAME; a plain build ignores decomp_toggle.txt."
    exit 1
}
$listFile = Join-Path $dir 'toggle_list.txt'
if (-not (Test-Path -LiteralPath $listFile)) { Write-Host "toggle_list.txt is not next to this script."; exit 1 }

# ---- the scenario ------------------------------------------------------------------------------------------
$noteLines = @()
$inputLines = @()
$force = @()
$section = ''
$lineNo = 0
foreach ($raw in (Get-Content -LiteralPath $Scenario)) {
    $lineNo++
    $line = $raw.Trim()
    if (-not $line -or $line.StartsWith('#')) { continue }
    if ($line -match '^\[(.+)\]$') { $section = $matches[1].Trim().ToLower(); continue }
    switch ($section) {
        'note'  { $noteLines += $line }
        'input' { $inputLines += $line }
        'force' {
            $a = $line.ToUpper()
            if ($a -notmatch '^[0-9A-F]{8}$') { Write-Host "$Scenario line ${lineNo}: '$line' is not an 8-digit hex address."; exit 1 }
            $force += $a
        }
        default { Write-Host "$Scenario line ${lineNo}: '$line' is outside a section ([note], [input], [force])."; exit 1 }
    }
}
if ($inputLines.Count -eq 0) {
    Write-Host "Warning: the scenario has no [input] lines - the game will just sit in the main menu."
}
$testLines = @('0 skipintro', '0 fastcam') + $inputLines
$forceText = if ($force.Count) { $force -join ' ' } else { '(none)' }

if ($Check) {
    Write-Host "exe:      $exe"
    Write-Host "scenario: $Scenario"
    Write-Host "note:"
    foreach ($n in $noteLines) { Write-Host "  $n" }
    Write-Host "testinput.txt:"
    foreach ($n in $testLines) { Write-Host "  $n" }
    Write-Host "force:    $forceText"
    Write-Host ("toggle_list.txt: {0} functions" -f @(Get-Content -LiteralPath $listFile | Where-Object { $_.Trim() -match '^[0-9A-Fa-f]{8}$' }).Count)
    exit 0
}

# ---- files next to the exe ---------------------------------------------------------------------------------
$toggle = Join-Path $dir 'decomp_toggle.txt'
$toggleLog = Join-Path $dir 'decomp_toggle.log'
$testinput = Join-Path $dir 'testinput.txt'
$log = Join-Path $dir 'decomp_debug.log'
$state = Join-Path $dir 'bisect_state.txt'
$exclude = Join-Path $dir 'bisect_exclude.txt'
$versionFile = Join-Path $dir 'bisect_version.txt'
$ctrlAll = Join-Path $dir 'bisect_ctrl_all.txt'
$ctrlOff = Join-Path $dir 'bisect_ctrl_off.txt'
$toggleBase = Join-Path $dir 'bisect_toggle_base.txt'

# results of an older search (another scenario, another list, another exe) would be read as this search's
# results: set them aside
$sig = ((Get-FileHash -LiteralPath $Scenario -Algorithm SHA256).Hash + '|' +
        (Get-FileHash -LiteralPath $listFile -Algorithm SHA256).Hash + '|' +
        (Get-FileHash -LiteralPath $exe -Algorithm SHA256).Hash)
$stateFiles = @('bisect_state.txt', 'bisect_exclude.txt', 'bisect_ctrl_all.txt', 'bisect_ctrl_off.txt',
                'bisect_toggle_base.txt')
$old = @()
if (Test-Path -LiteralPath $versionFile) {
    if (([string](Get-Content -LiteralPath $versionFile -Raw)).Trim() -ne $sig) { $old = $stateFiles }
} elseif ((Test-Path -LiteralPath $state) -or (Test-Path -LiteralPath $exclude)) {
    $old = $stateFiles
}
if ($old.Count -gt 0) {
    $bak = Join-Path $dir ('bisect_old_' + (Get-Date -Format 'yyyyMMdd_HHmmss'))
    New-Item -ItemType Directory -Path $bak | Out-Null
    foreach ($n in $old) {
        $p = Join-Path $dir $n
        if (Test-Path -LiteralPath $p) { Move-Item -LiteralPath $p -Destination $bak }
    }
    Write-Host "The scenario, the function list or the exe changed: the state of the earlier search was moved to"
    Write-Host "$bak (nothing is read from it).  Copy bisect_exclude.txt back from there to keep its exclusions."
}
Set-Content -Path $versionFile -Value $sig -Encoding ASCII

$skip = @()
if (Test-Path -LiteralPath $exclude) {
    $skip = @(Get-Content -LiteralPath $exclude | ForEach-Object { $_.Trim().ToUpper() } | Where-Object { $_ })
}
$list = @(Get-Content -LiteralPath $listFile | ForEach-Object { $_.Trim().ToUpper() } |
          Where-Object { $_ -match '^[0-9A-F]{8}$' -and $skip -notcontains $_ -and $force -notcontains $_ } |
          Sort-Object)
if ($list.Count -eq 0) { Write-Host "toggle_list.txt is empty or everything in it is excluded - nothing to search."; exit 1 }

# the lines decomp_debug.log got during the last run
function Read-NewLog([long]$from, [string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { return @() }
    $t = ''
    $fs = [System.IO.File]::Open($path, 'Open', 'Read', 'ReadWrite')
    try {
        $fs.Position = $from
        $sr = New-Object System.IO.StreamReader($fs, [System.Text.Encoding]::ASCII)
        $t = $sr.ReadToEnd()
    } finally { $fs.Dispose() }
    return @($t -split "`r?`n" | Where-Object { $_.Trim() })
}

# the tester's answer, lower case (an empty or broken read stops the search instead of crashing the script)
function Ask([string]$prompt) {
    $v = Read-Host $prompt
    if ($null -eq $v) { return 'q' }
    return $v.Trim().ToLower()
}

# one step: run the game with these toggle rules, let the tester watch and answer, show what the engine wrote down
# $expectOn: how many replacements decomp_toggle.log should report (-1 = any, -2 = all of them)
function Run-Step([string[]]$rules, [string]$label, [int]$expectOn = -1) {
    while ($true) {
        Set-Content -Path $toggle -Value $rules -Encoding ASCII
        Set-Content -Path $testinput -Value $testLines -Encoding ASCII
        $from = 0
        if (Test-Path -LiteralPath $log) { $from = (Get-Item -LiteralPath $log).Length }
        $t0 = Get-Date
        Write-Host ""
        Write-Host ("=== {0} ===" -f $label)
        foreach ($n in $noteLines) { Write-Host ("  {0}" -f $n) }
        Write-Host "Starting the game (skip intros + camera flyby, then the scenario's input)."
        $game = Start-Process -FilePath $exe -WorkingDirectory $dir -PassThru
        $a = ''
        do {
            $a = Ask "Is the bug present? (y - yes, n - no / gone, r - repeat this step, q - stop)"
        } while ('y', 'n', 'r', 'q' -notcontains $a)
        $exited = $false
        if ($game) {
            $exited = $game.HasExited
            if (-not $exited) {
                Stop-Process -Id $game.Id -Force -ErrorAction SilentlyContinue
                $game.WaitForExit(10000) | Out-Null
            }
        }
        Start-Sleep -Milliseconds 500
        $new = @(Read-NewLog $from $log)
        $bmps = @(Get-ChildItem -Path $dir -Filter '*.bmp' -File -ErrorAction SilentlyContinue |
                  Where-Object { $_.LastWriteTime -ge $t0 })
        $dst = Join-Path $dir ('bisect_shots\' + $label)
        New-Item -ItemType Directory -Force -Path $dst | Out-Null
        if ($bmps.Count -gt 0) { Copy-Item -LiteralPath $bmps.FullName -Destination $dst -Force }
        Copy-Item -LiteralPath $toggle -Destination (Join-Path $dst 'decomp_toggle.txt') -Force
        Copy-Item -LiteralPath $testinput -Destination (Join-Path $dst 'testinput.txt') -Force
        Set-Content -Path (Join-Path $dst 'step.txt') -Encoding ASCII -Value ((@(
            "label: $label", "answer: $a", '', 'decomp_toggle.txt:') + $rules) + @('', 'decomp_debug.log:') + $new)
        $on = -1; $total = -1
        if (Test-Path -LiteralPath $toggleLog) {
            $m = [regex]::Match([string](Get-Content -LiteralPath $toggleLog -Raw), '(\d+) of (\d+) replaced')
            if ($m.Success) { $on = [int]$m.Groups[1].Value; $total = [int]$m.Groups[2].Value }
        }
        $want = if ($expectOn -eq -2) { $total } else { $expectOn }
        if ($on -lt 0) {
            Write-Host "Toggle: decomp_toggle.log was not written - the rules were not applied, this run means nothing."
        } else {
            Write-Host ("Toggle: {0} of {1} replacements on." -f $on, $total)
            if ($expectOn -eq -2 -and $total -gt 0 -and $on -ne $total) {
                Write-Host ("Warning: all {0} replacements were expected on - the rules were not applied as intended." -f $total)
            } elseif ($want -ge 0 -and ($on -gt $want -or $on -lt $want - 3)) {
                Write-Host ("Warning: about {0} replacements were expected - the rules were not applied as intended." -f $want)
            }
        }
        if ($new.Count -eq 0) {
            Write-Host "decomp_debug.log got nothing in this run (is this the debug exe?)."
        } else {
            Write-Host ("decomp_debug.log, last {0} line(s) of this run:" -f [math]::Min(30, $new.Count))
            foreach ($n in @($new | Select-Object -Last 30)) { Write-Host ("  {0}" -f $n) }
        }
        Write-Host ("BMPs this run: {0} -> bisect_shots\{1}\" -f $bmps.Count, $label)
        if ($a -eq 'r') { continue }
        if ($exited) {
            Write-Host "The game closed by itself - that is usually a crash, and then the answer is not usable."
            $b = ''
            do {
                $b = Ask "Repeat this step? (r - repeat, c - keep this answer, q - stop)"
            } while ('r', 'c', 'q' -notcontains $b)
            if ($b -eq 'q') { return 'q' }
            if ($b -eq 'r') { continue }
        }
        return $a
    }
}

$baseOn = -1; $baseTotal = -1
try {
    if (-not (Test-Path -LiteralPath $ctrlAll)) {
        $a = Run-Step @('+ 00000000-FFFFFFFF') 'ctrl_all' -expectOn -2
        if ($a -eq 'q') { Write-Host "Nothing saved."; exit }
        if ($a -ne 'y') {
            Write-Host ""
            Write-Host "Control A failed: with every generated function switched on the bug did not appear."
            Write-Host "Either it is already fixed in this build or the scenario did not reach it.  Edit"
            Write-Host "$Scenario (the note and the input lines) and run again.  Nothing was saved."
            exit
        }
        'ok' | Set-Content -Path $ctrlAll -Encoding ASCII
        Write-Host "Control A passed: everything on - the bug is there."
    }
    if (-not (Test-Path -LiteralPath $ctrlOff)) {
        $a = Run-Step (@('- 00000000-FFFFFFFF') + @($force | ForEach-Object { "+ $_" })) 'ctrl_off'
        if ($a -eq 'q') { Write-Host "Nothing saved."; exit }
        if ($a -eq 'y') {
            Write-Host ""
            Write-Host "Control B failed: with every generated function off (only the hand-written code of the engine,"
            Write-Host "src/fixed and the harness on) the bug is still there.  Its cause is in the hand-written code or"
            Write-Host "in the scenario, not in a replaced function, and a search over toggle_list.txt cannot find it."
            Write-Host "Send me decomp_debug.log and bisect_shots\ctrl_off."
            exit
        }
        'ok' | Set-Content -Path $ctrlOff -Encoding ASCII
        Write-Host "Control B passed: everything off - the bug is gone."
        if (Test-Path -LiteralPath $toggleLog) {
            $m = [regex]::Match([string](Get-Content -LiteralPath $toggleLog -Raw), '(\d+) of (\d+) replaced')
            if ($m.Success) {
                ('{0} {1}' -f $m.Groups[1].Value, $m.Groups[2].Value) | Set-Content -Path $toggleBase -Encoding ASCII
            }
        }
    }

    if (Test-Path -LiteralPath $toggleBase) {
        $t = (Get-Content -LiteralPath $toggleBase -Raw).Trim() -split ' '
        if ($t.Count -ge 2) { $baseOn = [int]$t[0]; $baseTotal = [int]$t[1] }
    }
    if (Test-Path -LiteralPath $state) {
        $lo, $hi = (Get-Content -LiteralPath $state) -split ' ' | ForEach-Object { [int]$_ }
        if ($null -eq $hi -or $hi -gt $list.Count -or $lo -lt 0 -or $hi -le $lo) {
            Move-Item -LiteralPath $state -Destination ($state + '.old_' + (Get-Date -Format 'HHmmss'))
            $lo = 0; $hi = $list.Count
            Write-Host "The saved position does not fit this list, starting from the beginning."
        } else {
            Write-Host "Resuming where the last search stopped."
        }
    } else {
        $lo = 0; $hi = $list.Count
    }
    Write-Host "Functions in the search: $($list.Count).  Switched off for good: $($skip.Count)."
    while ($hi - $lo -gt 1) {
        $mid = [int][math]::Floor(($lo + $hi) / 2)
        $left = [math]::Ceiling([math]::Log($hi - $lo, 2))
        $skipInRange = @($skip | Where-Object { $_ -ge $list[0] -and $_ -le $list[$mid - 1] }).Count
        $a = Run-Step (@('- 00000000-FFFFFFFF') + @('+ {0}-{1}' -f $list[0], $list[$mid - 1]) +
                       @($skip | ForEach-Object { "- $_" }) + @($force | ForEach-Object { "+ $_" })) ('k' + $mid) `
                      -expectOn $(if ($baseOn -ge 0) { $baseOn + $mid - $skipInRange } else { -1 })
        Write-Host ("{0} of {1} generated functions on.  Steps left: about {2}." -f $mid, $list.Count, $left)
        if ($a -eq 'q') {
            "$lo $hi" | Set-Content -Path $state -Encoding ASCII
            Write-Host "Saved, run again later to continue."
            exit
        }
        if ($a -eq 'y') { $hi = $mid } else { $lo = $mid }
        "$lo $hi" | Set-Content -Path $state -Encoding ASCII
    }

    $bad = $list[$hi - 1]
    Add-Content -Path $exclude -Value $bad -Encoding ASCII
    Remove-Item -LiteralPath $state -ErrorAction SilentlyContinue
    Set-Content -Path $toggle -Encoding ASCII -Value ((@($skip + $bad) | ForEach-Object { "- $_" }) +
                                                     @($force | ForEach-Object { "+ $_" }))
    Write-Host ""
    Write-Host "Found: $bad - the last generated function that brings the bug back.  It is in bisect_exclude.txt now."
    $a = Run-Step (@('+ 00000000-FFFFFFFF') + @($skip | ForEach-Object { "- $_" }) + @("- $bad") +
                   @($force | ForEach-Object { "+ $_" })) ('confirm_' + $bad) `
                  -expectOn $(if ($baseTotal -ge 0) { $baseTotal - 1 - $skip.Count } else { -1 })
    if ($a -eq 'n') {
        Write-Host "Confirmed: with $bad off and everything else on the bug is gone.  Send me bisect_exclude.txt,"
        Write-Host "decomp_debug.log and bisect_shots\confirm_$bad; the search can continue from there (run this"
        Write-Host "script again to look for the next function)."
    } else {
        Write-Host "Not confirmed: with $bad off the bug was still there, so this result is not reliable."
        Write-Host "The bug is probably an interaction of several replacements rather than one function."
        Write-Host "Send me decomp_debug.log, bisect_exclude.txt and bisect_shots\confirm_$bad and the step shots."
    }
} finally {
    Remove-Item -LiteralPath $testinput -ErrorAction SilentlyContinue
}
