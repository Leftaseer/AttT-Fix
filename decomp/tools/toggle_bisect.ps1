# Двоичный поиск заменённой функции, из-за которой игра падает в каком-то сценарии.
# Нужна сборка build.py --toggle (ATThrone_auto_debug.exe): она при запуске читает decomp_toggle.txt рядом с собой
# и включает только перечисленные там замены. Скрипт сам пишет этот файл, запускает игру без заставок (-nologo,
# ключ самой игры), ждёт её закрытия и спрашивает, проявилась ли ошибка; после 12-13 шагов называет функцию и
# добавляет её в bisect_exclude.txt (она остаётся выключенной, следующий запуск ищет следующую виноватую).
# Файлы рядом со скриптом: toggle_list.txt (адреса всех замен), bisect_state.txt (где остановились).
$ErrorActionPreference = 'Stop'
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
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
if ($exe) { Write-Host "Игра: $(Split-Path -Leaf $exe) (запускается скриптом, без заставок)." }
else { Write-Host "ATThrone_auto_debug.exe не найден рядом со скриптом: запускайте игру сами." }
while ($hi - $lo -gt 1) {
    $mid = [int][math]::Floor(($lo + $hi) / 2)
    $rules = @('- 00000000-FFFFFFFF', ('+ {0}-{1}' -f $list[0], $list[$mid - 1])) + @($skip | ForEach-Object { "- $_" })
    Set-Content -Path $toggle -Value $rules -Encoding ASCII
    $left = [math]::Ceiling([math]::Log($hi - $lo, 2))
    Write-Host ""
    Write-Host "Включено $mid из $($list.Count) замен. Осталось шагов: около $left."
    if ($exe) {
        Write-Host "Запускаю игру. Повторите сценарий и закройте игру (или дождитесь вылета)."
        Start-Process -FilePath $exe -ArgumentList '-nologo' -WorkingDirectory $dir -Wait
    } else {
        Write-Host "Запустите ATThrone_auto_debug.exe, повторите сценарий, закройте игру (или дождитесь вылета)."
    }
    do { $a = Read-Host "Ошибка проявилась (вылет, проход сквозь стену и т.п.)? (y - да, n - нет, q - прервать)" } until ('y', 'n', 'q' -contains $a)
    if ($a -eq 'q') { "$lo $hi" | Set-Content $state; Write-Host "Сохранено, можно продолжить позже."; exit }
    if ($a -eq 'y') { $hi = $mid } else { $lo = $mid }
    "$lo $hi" | Set-Content $state
}
$bad = $list[$hi - 1]
Add-Content -Path $exclude -Value $bad
Remove-Item $state -ErrorAction SilentlyContinue
Set-Content -Path $toggle -Value (@($skip + $bad) | ForEach-Object { "- $_" }) -Encoding ASCII
Write-Host ""
Write-Host "Найдено: функция $bad. Она добавлена в bisect_exclude.txt и выключена в decomp_toggle.txt."
Write-Host "Если игра всё ещё падает в этом сценарии, запустите поиск ещё раз."
