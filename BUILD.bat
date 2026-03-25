@echo off
echo ============================================
echo   Building HKI standalone exe...
echo ============================================
echo.

where python >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python first.
    pause
    exit /b 1
)

pip install -r requirements.txt >nul 2>&1

python -m PyInstaller ^
    --noconfirm ^
    --clean ^
    --windowed ^
    --onefile ^
    --name HKI ^
    --icon "assets\hki.ico" ^
    --add-data "assets;assets" ^
    hki_app.pyw

echo.
if not exist "dist\HKI.exe" (
    echo BUILD FAILED.
    echo.
    pause
    exit /b 1
)

echo Creating release folder...
if exist release rmdir /s /q release
mkdir release
copy "dist\HKI.exe" "release\HKI.exe" >nul
copy "Install-HKI.cmd" "release\Install-HKI.cmd" >nul
copy "Uninstall-HKI.cmd" "release\Uninstall-HKI.cmd" >nul

echo.
echo ============================================
echo   DONE!  Ship the "release" folder:
echo.
echo     release\HKI.exe
echo     release\Install-HKI.cmd
echo     release\Uninstall-HKI.cmd
echo.
echo   Users just double-click HKI.exe to run,
echo   or run Install-HKI.cmd to add it to
echo   Windows Search.
echo ============================================
echo.
pause
