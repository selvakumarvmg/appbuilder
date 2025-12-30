@echo off
setlocal EnableExtensions EnableDelayedExpansion

:: Args:
::   updater.bat "C:\Program Files\PremediaApp\PremediaApp.exe" "C:\Users\vmg\AppData\Local\Temp\PremediaApp_v1.1.43.exe"

set "OLD_EXE=%~1"
set "NEW_FILE=%~2"

if "%OLD_EXE%"=="" (echo [ERR] Missing OLD_EXE & exit /b 1)
if "%NEW_FILE%"=="" (echo [ERR] Missing NEW_FILE & exit /b 1)

for %%I in ("%OLD_EXE%") do set "EXE_NAME=%%~nxI"

:: Create a log folder
set "LOG_DIR=C:\ProgramData\PremediaApp\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%" >NUL 2>&1
set "LOG_FILE=%LOG_DIR%\update_%date:~10,4%%date:~4,2%%date:~7,2%_%time:~0,2%%time:~3,2%%time:~6,2%.log"
set "LOG_FILE=%LOG_FILE:\=_%"

echo ===== Updater started: %date% %time% ===== > "%LOG_FILE%"
echo OLD_EXE=%OLD_EXE% >> "%LOG_FILE%"
echo NEW_FILE=%NEW_FILE% >> "%LOG_FILE%"

:: --- 1. Elevate to admin if needed ---
whoami /groups | find "S-1-5-32-544" >NUL
if errorlevel 1 (
  echo [INFO] Elevating to Admin... >> "%LOG_FILE%"
  powershell -NoProfile -Command "Start-Process -FilePath '%~f0' -ArgumentList @('%OLD_EXE','%NEW_FILE%') -Verb RunAs"
  exit /b 0
)

:: --- 2. Stop the running app ---
echo [INFO] Killing %EXE_NAME% >> "%LOG_FILE%"
taskkill /IM "%EXE_NAME%" /F >NUL 2>&1

:: --- 3. Wait until unlocked (max 15 s) ---
set /a t=0
:wait_unlock
set /a t+=1
powershell -NoProfile -Command "try{$s=[IO.File]::Open('%OLD_EXE%','Open','ReadWrite','None');$s.Close();exit 0}catch{exit 1}"
if errorlevel 1 (
  if %t% GEQ 15 (
    echo [ERR] File locked after 15 s >> "%LOG_FILE%"
    echo [ERR] Update failed – EXE locked.
    exit /b 2
  )
  timeout /t 1 >NUL
  goto :wait_unlock
)

:: --- 4. Backup & replace ---
echo [INFO] Backing up old exe... >> "%LOG_FILE%"
copy /Y "%OLD_EXE%" "%OLD_EXE%.bak" >NUL 2>&1

echo [INFO] Replacing with new file... >> "%LOG_FILE%"
powershell -NoProfile -Command "Copy-Item -LiteralPath '%NEW_FILE%' -Destination '%OLD_EXE%' -Force"

if errorlevel 1 (
  echo [ERR] Replace failed >> "%LOG_FILE%"
  echo [ERR] Update failed – could not copy new exe.
  exit /b 3
)

:: --- 5. Restart the app ---
echo [INFO] Restarting %EXE_NAME% >> "%LOG_FILE%"
start "" "%OLD_EXE%"

echo [OK] ✅ Update complete >> "%LOG_FILE%"
exit /b 0
