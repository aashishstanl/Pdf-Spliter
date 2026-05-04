#!/bin/bash

# Linux/macOS Shell Script for PDF Processing
# Usage: ./run_pdf_processor.sh "path/to/file.pdf"
# chmod +x run_pdf_processor.sh

set -e

echo ""
echo "============================================================"
echo "   PDF SPLIT FRAMEWORK - Unix/Linux Launcher"
echo "============================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org"
    exit 1
fi

# Check Python version
python_version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "✓ Python $python_version found"

# Check if dependencies are installed
echo "Checking dependencies..."
if ! python3 -c "import PyPDF2" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -r requirements.txt
fi

# Check for Tesseract
if ! command -v tesseract &> /dev/null; then
    echo "WARNING: Tesseract OCR not found"
    echo "Install with:"
    echo "  Ubuntu/Debian: sudo apt-get install tesseract-ocr"
    echo "  macOS: brew install tesseract"
    echo ""
fi

# Handle arguments
if [ $# -eq 0 ]; then
    echo "USAGE EXAMPLES:"
    echo "  ./run_pdf_processor.sh /path/to/document.pdf"
    echo "  ./run_pdf_processor.sh /path/to/pdf_folder/"
    echo ""
    echo "OPTIONS:"
    echo "  --verify      Verify installation"
    echo "  --help        Show this help"
    echo ""
    exit 0
fi

# Handle options
if [ "$1" = "--verify" ]; then
    echo "Running setup verification..."
    python3 verify_setup.py
    exit 0
fi

if [ "$1" = "--help" ]; then
    echo "PDF SPLIT FRAMEWORK - Help"
    echo ""
    echo "Process single file:"
    echo "  python3 batch_process.py --input file.pdf"
    echo ""
    echo "Process folder:"
    echo "  python3 batch_process.py --input folder/ --output report.json"
    echo ""
    echo "View examples:"
    echo "  python3 QUICKSTART.py"
    echo ""
    exit 0
fi

# Process PDF or directory
echo "Processing: $1"
echo ""
python3 batch_process.py --input "$1"

echo ""
echo "============================================================"
echo "   PROCESSING COMPLETE - Check pdf_splits folder"
echo "============================================================"
echo ""
