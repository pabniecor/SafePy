@echo off
REM Build SafePy as standalone executable with PyInstaller

setlocal enabledelayedexpansion

echo Building SafePy executable...

REM Check if PyInstaller is installed
python -c "import PyInstaller" >nul 2>&1
if errorlevel 1 (
    echo Error: PyInstaller not installed. Run: pip install PyInstaller
    exit /b 1
)

REM Build
pyinstaller ^
    --onefile ^
    --windowed ^
    --name SafePy ^
    --icon app\ui\assets\icon.ico ^
    main.py

if errorlevel 1 (
    echo Build failed!
    exit /b 1
)

echo Build completed successfully!
echo Executable is located in: dist\SafePy.exe
