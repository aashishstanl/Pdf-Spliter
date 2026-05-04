# PDF Split Framework - Documentation

## Overview

A production-ready Python framework that automatically splits PDF files into individual documents based on specific markers. It follows these rules:

### Splitting Rules

1. **Start of File**: "No. X" marker (handwritten at top/left margin)
2. **End of File**: "Being No. X" blue stamp marker (must match)
3. **End Rule**: The file ends only when the left-side stamp's `Being No.` matches the active first-page `No.`
4. **Fallback Naming**: Disabled by default to avoid unrelated blue-stamp numbers; can be enabled with `USE_FIFTH_LINE_FALLBACK`
5. **Output**: Individual PDFs named `X.pdf` bundled in a ZIP file (max 5MB each)

---

## Installation

### Prerequisites

- Python 3.8+
- Tesseract OCR (for text extraction)
- Poppler (required by `pdf2image` to read PDF pages)

### What Tesseract and Poppler Do

Poppler opens the PDF and converts each page into an image:

```text
PDF page -> image
```

Tesseract reads text from those page images using OCR:

```text
image -> detected text
```

Together, they let the script detect markers like `No. 123` and `Being No. 123`, then split the original PDF into separate files.

### Windows Installation

1. **Install Tesseract OCR**:

   Download the Windows installer from:

   https://github.com/UB-Mannheim/tesseract/wiki

   Install it to the default location:

   ```text
   C:\Program Files\Tesseract-OCR
   ```

   Then set the path in `config.py`:

   ```python
   TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
   ```

2. **Install Poppler**:

   Download Poppler for Windows, extract it, then set the `bin` folder in `config.py`.

   Example:

   ```python
   POPPLER_PATH = r"C:\poppler\Library\bin"
   ```

3. **Install Python Dependencies**:

   If PowerShell blocks venv activation, you can run the venv Python directly:

   ```powershell
   .\venv\Scripts\python.exe -m pip install -r requirements.txt
   ```

   Then process a PDF without activating the venv:

   ```powershell
   .\venv\Scripts\python.exe setup.py "C:\path\to\your.pdf"
   ```

   Optional, only for the current PowerShell window:

   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\venv\Scripts\Activate.ps1
   ```

### Linux/macOS Installation

1. **Install Tesseract and Poppler**:

   ```bash
   # Ubuntu/Debian
   sudo apt update
   sudo apt-get install tesseract-ocr
   sudo apt-get install poppler-utils

   # macOS
   brew install tesseract
   brew install poppler
   ```

2. **Install Python Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

---

## Quick Start

### Basic Usage

```python
from work import process_pdf_file

# Process a PDF
result = process_pdf_file("path/to/input.pdf")

# Check result
if result['status'] == 'success':
    print(f"Created {result['total_groups']} PDF files")
    print(f"Output: {result['output_dir']}")
else:
    print(f"Error: {result['message']}")
```

### From Command Line

```bash
python setup.py "path/to/input.pdf"
```

This starts interactive manual mode. The script shows the total PDF page count, then repeatedly asks:

```text
What is the No. on this first page?
How many total pages are in No.X?
```

For number prompts, type the digits and pause briefly. The script auto-submits after the pause, so pressing Enter is optional. Backspace still works while typing.
If you typed the wrong `No.` and the page-count prompt is showing, type `E` to go back and enter the `No.` again.

It creates each numbered PDF and stops when all pages in the input PDF are assigned.
Each PDF is written to the output session folder immediately after that entry is completed. The ZIP bundle is created at the end.

The interactive flow asks whether output pages should be rotated. Press Enter for no rotation, or enter `90`, `180`, or `270`.

You can also pass rotation in the command:

```bash
python setup.py "path/to/input.pdf" --rotate 90
```

You can also run the processor directly:

```bash
python work.py "path/to/input.pdf"
```

### One-Shot Manual Mode Without OCR

If you already know the first-page number and how many pages belong to that file, pass both values after the PDF path:

```bash
python setup.py "path/to/input.pdf" 107 12
```

This creates `107.pdf` from pages `1-12` of the input PDF, bundles it into a ZIP, and does not scan/read the page content.

### OCR Mode

If you want to use the older OCR marker detection, run:

```bash
python setup.py "path/to/input.pdf" --auto
```

### Switching Between Manual and OCR

Manual interactive mode is the default:

```powershell
.\venv\Scripts\python.exe setup.py "C:\path\to\your.pdf"
```

OCR mode is enabled with `--auto`:

```powershell
.\venv\Scripts\python.exe setup.py "C:\path\to\your.pdf" --auto
```

For OCR mode, make sure `config.py` has valid paths:

```python
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
POPPLER_PATH = r"C:\poppler-26.02.0\Library\bin"
```

---

## Output Structure

```
pdf_splits/
└── session_20260504_143022/
    ├── 1.pdf
    ├── 2.pdf
    ├── 3.pdf
    └── pdf_split_output.zip
```

The ZIP file contains all split PDFs ready for distribution.

---

## Configuration

Edit `config.py` to customize:

```python
OUTPUT_BASE_DIR = "pdf_splits"  # Output folder
DPI = 300  # Higher = better OCR accuracy
DEBUG = True  # Enable/disable logging
MAX_PDF_SIZE_MB = 5  # Maximum file size
OCR_ROTATIONS = (0, 90)  # Fast mode: normal and sideways-left marker crops
BEING_STAMP_LINE = 5  # Ending Being No. is read from the 5th stamp line
START_NO_REGION = (0.0, 0.0, 0.30, 1.0)  # Left strip only for the handwritten first-page No.
BEING_STAMP_REGION = (0.0, 0.0, 0.40, 1.0)  # Left strip only for the Being No. stamp
OCR_SCALE = 2  # Enlarge marker crops before OCR
OCR_PSM_MODES = (6,)  # Fast mode: one Tesseract mode per crop
OCR_PREPROCESS_VARIANTS = ("contrast",)  # Fast mode: one image cleanup variant
USE_FIFTH_LINE_FALLBACK = False  # Avoid using unrelated blue-stamp numbers as file starts
AUTO_ACCEPT_SECONDS = 0.8  # Auto-submit typed numbers after this pause
```

---

## Advanced Usage

### Custom Processing with Logging

```python
from work import process_pdf_file

result = process_pdf_file("documents/batch_file.pdf")

# Access detailed information
for file_no, start_page, end_page in result['groups']:
    num_pages = end_page - start_page + 1
    print(f"PDF No.{file_no}: Pages {start_page + 1}-{end_page + 1} ({num_pages} pages)")
```

### Batch Processing Multiple PDFs

```python
from pathlib import Path
from work import process_pdf_file

# Process all PDFs in a directory
input_dir = Path("pdfs_to_process")
for pdf_file in input_dir.glob("*.pdf"):
    print(f"\nProcessing: {pdf_file.name}")
    result = process_pdf_file(str(pdf_file))
    if result['status'] == 'success':
        print(f"✓ Created {result['total_groups']} files")
    else:
        print(f"✗ Error: {result['message']}")
```

---

## How It Works

### Step 1: PDF Analysis

- Converts PDF pages to images (OCR)
- Extracts text from each page
- Searches for "No. X" and "Being No. X" markers

### Step 2: Group Detection

- Identifies file boundaries based on markers
- Handles special cases (new No. appears before Being, etc.)
- Validates no overlaps or gaps

### Step 3: PDF Creation

- Extracts page ranges for each group
- Creates individual PDF files
- Validates file sizes (< 5MB)

### Step 4: Bundling

- Zips all PDFs together
- Creates timestamped session directories
- Ready for distribution

---

## Troubleshooting

### Issue: "pytesseract.TesseractNotFoundError"

**Solution**: Install Tesseract and set the path in `config.py`:

```python
TESSERACT_PATH = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
```

### Issue: Poppler/pdfinfo Not Found

**Solution**: Install Poppler and set the `bin` folder in `config.py`:

```python
POPPLER_PATH = r"C:\poppler\Library\bin"
```

### Issue: Poor OCR Recognition

**Solution**: Increase DPI in `config.py`:

```python
DPI = 600  # Higher DPI for better accuracy
```

### Issue: Text Detection Not Working

**Solution**: Check document quality and marker format. Ensure:

- "No. X" is clearly visible at page top
- "Being No. X" blue stamp is present
- Text is not rotated

### Issue: Memory Error with Large PDFs

**Solution**: Process in batches or reduce DPI:

```python
DPI = 150  # Lower DPI to reduce memory usage
```

---

## Validation Rules

The framework validates:

- ✓ Each PDF starts with "No. X"
- ✓ Each PDF ends with matching "Being No. X"
- ✓ No page overlaps between files
- ✓ No missing pages
- ✓ File sizes < 5MB
- ✓ Output ZIP bundled correctly

---

## API Reference

### `process_pdf_file(pdf_path: str) -> dict`

Main function to process PDF.

**Parameters**:

- `pdf_path` (str): Path to input PDF file

**Returns** (dict):

```python
{
    'status': 'success' | 'error',
    'groups': [(file_no, start_page, end_page), ...],
    'pdf_files': ['path/1.pdf', 'path/2.pdf', ...],
    'output_dir': 'path/to/session_dir',
    'zip_file': 'path/to/pdf_split_output.zip',
    'total_groups': 3,
    'message': 'error message (if status=error)'
}
```

### `analyze_pdf(pdf_path: str) -> tuple`

Analyzes PDF and detects groups.

**Returns**: `(groups, reader, total_pages)`

### `create_output_pdfs(pdf_path, groups, reader, total_pages) -> tuple`

Creates individual PDF files.

**Returns**: `(pdf_files_list, session_directory)`

### `create_zip_bundle(pdf_files, session_dir) -> Path`

Bundles all PDFs into ZIP.

**Returns**: Path to created ZIP file

---

## Examples

### Example 1: Simple Processing

```python
from work import process_pdf_file

result = process_pdf_file("C:/Downloads/document.pdf")
print(f"Output saved to: {result['output_dir']}")
```

### Example 2: Processing with Error Handling

```python
from work import process_pdf_file

try:
    result = process_pdf_file("document.pdf")
    if result['status'] == 'success':
        print(f"Successfully split into {result['total_groups']} PDFs")
        print(f"ZIP file: {result['zip_file']}")
    else:
        print(f"Processing failed: {result['message']}")
except FileNotFoundError:
    print("PDF file not found")
except Exception as e:
    print(f"Unexpected error: {e}")
```

### Example 3: Batch Processing with Report

```python
from pathlib import Path
from work import process_pdf_file
import json

input_dir = Path("input_pdfs")
report = {}

for pdf_file in input_dir.glob("*.pdf"):
    result = process_pdf_file(str(pdf_file))
    report[pdf_file.name] = {
        'status': result['status'],
        'groups': result.get('total_groups', 0),
        'output': result.get('output_dir', '')
    }

# Save report
with open("processing_report.json", "w") as f:
    json.dump(report, f, indent=2)
```

---

## Performance

- **Small PDFs (< 50 pages)**: ~5-10 seconds
- **Medium PDFs (50-200 pages)**: ~15-30 seconds
- **Large PDFs (200+ pages)**: ~1+ minute
- Memory usage: ~50-100MB per 100 pages

_Times vary based on DPI, system performance, and PDF quality_

---

## Support

For issues or improvements, refer to the framework code and adjust configuration in `config.py`.

---

**Framework Version**: 1.0  
**Last Updated**: May 4, 2026
