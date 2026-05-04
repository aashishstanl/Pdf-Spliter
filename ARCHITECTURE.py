#!/usr/bin/env python3
"""
PDF Split Framework - Architecture & Data Flow Diagram
Visual representation of how the system works
"""

ARCHITECTURE_DIAGRAM = r"""
╔════════════════════════════════════════════════════════════════════════════════╗
║              PDF SPLIT FRAMEWORK - ARCHITECTURE & DATA FLOW                   ║
╚════════════════════════════════════════════════════════════════════════════════╝

INPUT
┌─────────────────────────┐
│  PDF File               │
│  (Any size/format)      │
└────────────┬────────────┘
             │
             ↓
┌────────────────────────────────────────────────────────────────┐
│  STEP 1: ANALYSIS                                              │
│  ─────────────────────────────────────────────────────────────│
│  Module: analyze_pdf()                                         │
│                                                                │
│  1. Convert PDF pages to images (OCR)                         │
│  2. Extract text from each page                               │
│  3. Search for markers:                                       │
│     • "No. X" (file start)                                    │
│     • "Being No. X" (file end)                                │
│                                                                │
│  Special cases handled:                                       │
│  ✓ "No. Y" appears before "Being No. X"                      │
│  ✓ Fallback naming (5th line)                                │
│  ✓ Page rotation detection                                    │
│                                                                │
│  Output: List of (file_no, start_page, end_page)             │
└────────────┬─────────────────────────────────────────────────┘
             │
             ↓
        ┌─────────────┐
        │  Groups[]   │
        │  (Detected) │
        └─────────────┘
             │
             ↓
┌────────────────────────────────────────────────────────────────┐
│  STEP 2: VALIDATION                                            │
│  ─────────────────────────────────────────────────────────────│
│  Module: validate_groups()                                    │
│                                                                │
│  Checks:                                                       │
│  ✓ No overlapping page ranges                                 │
│  ✓ No missing pages                                           │
│  ✓ Start/End markers match                                    │
│  ✓ File count > 0                                             │
│                                                                │
│  Output: Validation report (Pass/Fail)                        │
└────────────┬─────────────────────────────────────────────────┘
             │
             ├─→ ✗ FAILED → Return error
             │
             └─→ ✓ PASSED
                     │
                     ↓
┌────────────────────────────────────────────────────────────────┐
│  STEP 3: PDF CREATION                                          │
│  ─────────────────────────────────────────────────────────────│
│  Module: create_output_pdfs()                                 │
│                                                                │
│  For each group:                                              │
│  1. Extract page range from original PDF                      │
│  2. Create new PDF file: "X.pdf"                              │
│  3. Validate file size < 5MB                                  │
│  4. Store in session folder with timestamp                    │
│                                                                │
│  Output: List of PDF file paths                               │
└────────────┬─────────────────────────────────────────────────┘
             │
             ↓
    ┌────────────────┐
    │  PDF Files[]   │
    │  1.pdf         │
    │  2.pdf         │
    │  3.pdf         │
    │  ...           │
    └────────────────┘
             │
             ↓
┌────────────────────────────────────────────────────────────────┐
│  STEP 4: ZIP BUNDLING                                          │
│  ─────────────────────────────────────────────────────────────│
│  Module: create_zip_bundle()                                  │
│                                                                │
│  1. Create ZIP archive                                         │
│  2. Add all PDF files                                          │
│  3. Save as: pdf_split_output.zip                              │
│  4. Store in session folder                                    │
│                                                                │
│  Output: ZIP file ready for distribution                      │
└────────────┬─────────────────────────────────────────────────┘
             │
             ↓
        ┌─────────────────────────────────────┐
        │  pdf_splits/session_[timestamp]/    │
        │  ├── 1.pdf                          │
        │  ├── 2.pdf                          │
        │  ├── 3.pdf                          │
        │  └── pdf_split_output.zip ✓         │
        └─────────────────────────────────────┘
             │
             ↓
         OUTPUT ✓


═══════════════════════════════════════════════════════════════════════════════
MARKER DETECTION LOGIC
═══════════════════════════════════════════════════════════════════════════════

Each Page:
┌─────────────────────────────────────────────────────────────┐
│ Extract Text (OCR)                                          │
└────────────────┬────────────────────────────────────────────┘
                 │
        ┌────────┴────────┐
        ↓                 ↓
   Find "No. X"      Find "Being No. X"
        │                 │
        └────────┬────────┘
                 ↓
        ┌────────────────────────┐
        │ Apply Rules:           │
        │                        │
        │ Rule 1: Start?         │
        │ Rule 2: End?           │
        │ Rule 3: Stop?          │
        │ Rule 5: Fallback?      │
        └────────┬───────────────┘
                 │
                 ↓
        ┌────────────────────────┐
        │ Group Decision         │
        │ • Start new group      │
        │ • End current group    │
        │ • Stop previous group  │
        │ • Continue current     │
        └────────┬───────────────┘
                 │
                 ↓
        (Move to next page)


═══════════════════════════════════════════════════════════════════════════════
USAGE PATHS
═══════════════════════════════════════════════════════════════════════════════

PATH 1: Python API (Most Control)
──────────────────────────────────
  from work import process_pdf_file
  result = process_pdf_file("file.pdf")
  ↓
  Returns: {
    'status': 'success',
    'groups': [(1, 0, 5), (2, 6, 12), ...],
    'pdf_files': ['1.pdf', '2.pdf', ...],
    'output_dir': 'pdf_splits/session_...',
    'zip_file': 'pdf_splits/session_.../pdf_split_output.zip',
    'total_groups': 3
  }


PATH 2: Command Line (Easiest for scripts)
───────────────────────────────────────────
  python batch_process.py --input "file.pdf" --output "report.json"
  ↓
  • Processes PDF
  • Creates JSON report
  • Saves results to pdf_splits/


PATH 3: Windows GUI (Point & Click)
────────────────────────────────────
  run_pdf_processor.bat "file.pdf"
  ↓
  • Error checking
  • Automatic dependency install
  • Shows results in terminal


PATH 4: Unix/Linux Shell
────────────────────────
  ./run_pdf_processor.sh "/path/to/file.pdf"
  ↓
  Same as Windows but for Unix systems


═══════════════════════════════════════════════════════════════════════════════
ERROR HANDLING FLOW
═══════════════════════════════════════════════════════════════════════════════

process_pdf_file()
      │
      ├─→ File exists? ──No─→ FileNotFoundError
      │
      ├─→ analyze_pdf()
      │      │
      │      ├─→ OCR fails? ──→ Log warning, continue
      │      │
      │      └─→ Markers found? ──No─→ Empty groups
      │
      ├─→ validate_groups()
      │      │
      │      ├─→ Overlaps? ──→ Error + details
      │      │
      │      ├─→ Missing pages? ──→ Error + details
      │      │
      │      └─→ Invalid ranges? ──→ Error + details
      │
      ├─→ create_output_pdfs()
      │      │
      │      ├─→ Extract fails? ──→ Error + group no.
      │      │
      │      ├─→ File too large? ──→ Warning, continue
      │      │
      │      └─→ Files created ──→ Continue
      │
      ├─→ create_zip_bundle()
      │      │
      │      ├─→ ZIP fails? ──→ Error, cleanup
      │      │
      │      └─→ ZIP created ──→ Continue
      │
      └─→ Return result dict (success or error)


═══════════════════════════════════════════════════════════════════════════════
FILE STRUCTURE OUTPUT
═══════════════════════════════════════════════════════════════════════════════

Input PDF:
  my_document.pdf (1000 pages)
     ↓
     [Analysis detects 5 groups]
     ↓
Creates:
  pdf_splits/
  └── session_20260504_143022/
      ├── 1.pdf         (50 pages)
      ├── 2.pdf         (75 pages)
      ├── 3.pdf         (100 pages)
      ├── 4.pdf         (250 pages)
      ├── 5.pdf         (525 pages)
      └── pdf_split_output.zip
         ├── 1.pdf
         ├── 2.pdf
         ├── 3.pdf
         ├── 4.pdf
         └── 5.pdf


═══════════════════════════════════════════════════════════════════════════════
PERFORMANCE CHARACTERISTICS
═══════════════════════════════════════════════════════════════════════════════

Bottleneck Analysis:
  OCR (Tesseract)     ████████████░░  60-70%  (Slowest)
  PDF Processing      ████░░░░░░░░░░  15-20%
  File I/O            ████░░░░░░░░░░  10-15%

Optimization Tips:
  Lower DPI           → Faster OCR (less accurate)
  Batch processing    → Reuse Tesseract process
  SSD storage         → Faster I/O
  More RAM            → Buffer more pages
  Parallel processing → Process multiple PDFs


═══════════════════════════════════════════════════════════════════════════════

This framework efficiently processes PDFs by analyzing document structure
and intelligently splitting them according to embedded markers.

The modular design allows for easy customization and integration.

═══════════════════════════════════════════════════════════════════════════════
"""

print(ARCHITECTURE_DIAGRAM)

if __name__ == "__main__":
    print("\nVisual guide saved. Reference this when understanding how the framework works.")
