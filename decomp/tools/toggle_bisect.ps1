# Двоичный поиск заменённой функции, из-за которой игра падает или ведёт себя не так, как оригинал.
# Нужна сборка build.py --toggle -D DECOMP_DEBUG_LOG -D DECOMP_TEST_INPUT (ATThrone_auto_debug.exe): она при запуске
# читает decomp_toggle.txt рядом с собой и включает только перечисленные там замены, а testinput.txt велит ей
# пропустить заставки и сразу загрузить сохранение. Скрипт сам пишет оба файла, запускает игру, игра без заставок
# загружает сохранение $Save (по умолчанию game0 - быстрое сохранение, F5), а скрипт сразу спрашивает, проявилась
# ли ошибка; после ответа сам закрывает игру и запускает следующий шаг. Через 12-13 шагов называет функцию и
# добавляет её в bisect_exclude.txt (она остаётся выключенной, следующий запуск ищет следующую виноватую).
# Другое сохранение: toggle_bisect.bat game3 (имя файла из папки Saves без .sav).
# Файлы рядом со скриптом: toggle_list.txt (адреса всех замен), bisect_state.txt (где остановились).
param([string]$Save = 'game0')
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$testinput = Join-Path $dir 'testinput.txt'
$exclude = Join-Path $dir 'bisect_exclude.txt'
$state = Join-Path $dir 'bisect_state.txt'
$toggle = Join-Path $dir 'decomp_toggle.txt'
$skip = @()
if (Test-Path $exclude) { $skip = @(Get-Content $exclude | ForEach-Object { $_.Trim().ToUpper() } | Where-Object { $_ }) }
$list = @(Get-Content (Join-Path $dir 'toggle_list.txt') | ForEach-Object { $_.Trim().ToUpper() } |
          Where-Object { $_ -match '^[0-9A-F]{8}$' -and $skip -notcontains $_ })

if (Test-Path $state) {
    $lo, $hi = (Get-Content $state) -split ' ' | ForEach-Object { [int]$_ }
    Write-Host "Продолжаю с места остановки."
} else {
    $lo = 0; $hi = $list.Count
}
Write-Host "Замен в поиске: $($list.Count). Выключены навсегда: $($skip.Count)."
# the build to run: the debug one if it is here (it logs crashes)
$exe = @('ATThrone_auto_debug.exe', 'ATThrone_auto.exe') | ForEach-Object { Join-Path $dir $_ } |
       Where-Object { Test-Path $_ } | Select-Object -First 1
if ($exe) { Write-Host "Игра: $(Split-Path -Leaf $exe) (запускается скриптом, без заставок, сразу загружает $Save)." }
else { Write-Host "ATThrone_auto_debug.exe не найден рядом со скриптом: запускайте игру сами." }
if (-not (Test-Path (Join-Path $dir "Saves\$Save.sav"))) {
    Write-Host "Внимание: нет файла Saves\$Save.sav - игра останется в меню загрузки."
}
# для игры: без заставок, затем загрузить сохранение (строки читает ATThrone_auto_debug.exe; по окончании файл удаляется)
Set-Content -Path $testinput -Value @('0 skipintro', "0 loadsave $Save") -Encoding ASCII
try {
while ($hi - $lo -gt 1) {
    $mid = [int][math]::Floor(($lo + $hi) / 2)
    $rules = @('- 00000000-FFFFFFFF', ('+ {0}-{1}' -f $list[0], $list[$mid - 1])) + @($skip | ForEach-Object { "- $_" })
    Set-Content -Path $toggle -Value $rules -Encoding ASCII
    $left = [math]::Ceiling([math]::Log($hi - $lo, 2))
    Write-Host ""
    Write-Host "Включено $mid из $($list.Count) замен. Осталось шагов: около $left."
    $game = $null
    if ($exe) {
        Write-Host "Запускаю игру. Проверьте сценарий и ответьте здесь, игру закрывать не нужно."
        $game = Start-Process -FilePath $exe -WorkingDirectory $dir -PassThru
    } else {
        Write-Host "Запустите ATThrone_auto_debug.exe и проверьте сценарий."
    }
    do { $a = Read-Host "Ошибка проявилась (вылет, проход сквозь стену и т.п.)? (y - да, n - нет, q - прервать)" } until ('y', 'n', 'q' -contains $a)
    if ($game -and -not $game.HasExited) {
        Stop-Process -Id $game.Id -Force -ErrorAction SilentlyContinue
        $game.WaitForExit(10000) | Out-Null
    }
    if ($a -eq 'q') {
        "$lo $hi" | Set-Content $state
        Write-Host "Сохранено, можно продолжить позже."
        exit
    }
    if ($a -eq 'y') { $hi = $mid } else { $lo = $mid }
    "$lo $hi" | Set-Content $state
}
} finally {
    # обычный запуск ATThrone_auto_debug.exe снова с заставками и главным меню
    Remove-Item $testinput -ErrorAction SilentlyContinue
}
$bad = $list[$hi - 1]
Add-Content -Path $exclude -Value $bad
Remove-Item $state -ErrorAction SilentlyContinue
Set-Content -Path $toggle -Value (@($skip + $bad) | ForEach-Object { "- $_" }) -Encoding ASCII
Write-Host ""
Write-Host "Найдено: функция $bad. Она добавлена в bisect_exclude.txt и выключена в decomp_toggle.txt."
Write-Host "Если игра всё ещё падает в этом сценарии, запустите поиск ещё раз."
