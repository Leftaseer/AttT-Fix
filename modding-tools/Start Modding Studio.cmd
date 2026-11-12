@echo off
setlocal
pushd "%~dp0"
if exist "%~dp0runtime\python.exe" (
    "%~dp0runtime\python.exe" -B "%~dp0attt.py" serve %*
) else (
    where py >nul 2>nul
    if errorlevel 1 (
        python -B "%~dp0attt.py" serve %*
    ) else (
        py -3 -B "%~dp0attt.py" serve %*
    )
)
if errorlevel 1 pause
popd
