@echo off
REM Windows Batch Script for PDF Processing
REM Usage: run_pdf_processor.bat "C:\path\to\file.pdf"

setlocal enabledelayedexpansion

echo.
echo ============================================================
echo   PDF SPLIT FRAMEWORK - Windows Launcher
echo ============================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import PyPDF2" >nul 2>&1
if errorlevel 1 (
    echo.
    echo Installing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

REM Check arguments
if "%1"=="" (
    echo.
    echo USAGE EXAMPLES:
    echo   run_pdf_processor "C:\Downloads\document.pdf"
    echo   run_pdf_processor "C:\pdf_folder\"
    echo.
    echo OPTIONS:
    echo   --verify      Verify installation
    echo   --help        Show this help
    echo.
    pause
    exit /b 0
)

REM Handle options
if "%1"=="--verify" (
    echo Running setup verification...
    python verify_setup.py
    pause
    exit /b 0
)

if "%1"=="--help" (
    echo PDF SPLIT FRAMEWORK - Help
    echo.
    echo Process single file:
    echo   python batch_process.py --input "file.pdf"
    echo.
    echo Process folder:
    echo   python batch_process.py --input "folder" --output "report.json"
    echo.
    echo View examples:
    echo   python QUICKSTART.py
    echo.
    pause
    exit /b 0
)

REM Process PDF or directory
echo.
echo Processing: %1
echo.
python batch_process.py --input "%1"

echo.
echo ============================================================
if errorlevel 0 (
    echo   PROCESSING COMPLETE - Check pdf_splits folder
) else (
    echo   ERROR: Processing failed
)
echo ============================================================
echo.
pause
