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
    --name HKI ^
    --icon "assets\hki.ico" ^
    --add-data "assets;assets" ^
    hki_app.pyw

echo.
if exist "dist\HKI\HKI.exe" (
    echo ============================================
    echo   DONE! Your exe is at:
    echo   dist\HKI\HKI.exe
    echo.
    echo   Zip the dist\HKI folder to share.
    echo ============================================
) else (
    echo BUILD FAILED.
)
echo.
pause
