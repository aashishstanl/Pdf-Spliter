"""
QUICK START GUIDE - PDF Split Framework

Copy-paste these examples to get started immediately!
"""

# ============================================================================
# EXAMPLE 1: BASIC USAGE (Simplest)
# ============================================================================

def example_1_basic():
    """Simplest way to process a PDF"""
    from work import process_pdf_file
    
    # Just point to your PDF
    result = process_pdf_file("C:/Users/Dell/Downloads/page1-31.pdf")
    
    # Done! Files are named by their detected "No. X" markers from PDF
    print(f"Detected {result['total_groups']} groups")
    print(f"Created {len(result['pdf_files'])} PDF file(s)")
    print(f"Location: {result['output_dir']}")

# ============================================================================
# EXAMPLE 2: WITH ERROR HANDLING
# ============================================================================

def example_2_error_handling():
    """Process with proper error handling"""
    from work import process_pdf_file
    
    try:
        result = process_pdf_file("your_file.pdf")
        
        if result['status'] == 'success':
            print(f"✓ Success! {result['total_groups']} files created")
            for file_no, start, end in result['groups']:
                pages = end - start + 1
                print(f"  - File No.{file_no}: {pages} pages")
        else:
            print(f"✗ Failed: {result['message']}")
            
    except FileNotFoundError:
        print("PDF file not found")

# ============================================================================
# EXAMPLE 3: BATCH PROCESSING (Multiple PDFs)
# ============================================================================

def example_3_batch_processing():
    """Process multiple PDFs from a folder"""
    from pathlib import Path
    from work import process_pdf_file
    
    # Process all PDFs in a folder
    pdf_folder = Path("C:/Users/Dell/Downloads")
    
    for pdf_file in pdf_folder.glob("*.pdf"):
        print(f"\nProcessing: {pdf_file.name}")
        result = process_pdf_file(str(pdf_file))
        
        if result['status'] == 'success':
            print(f"  ✓ {result['total_groups']} files created")
        else:
            print(f"  ✗ Error: {result['message']}")

# ============================================================================
# EXAMPLE 4: WITH CUSTOM CONFIGURATION
# ============================================================================

def example_4_custom_config():
    """Process with custom OCR settings"""
    import work
    
    # Customize settings
    work.OUTPUT_BASE_DIR = "my_output"
    work.DPI = 600  # Higher quality OCR (slower)
    work.DEBUG = True  # See detailed logs
    
    # Process
    result = work.process_pdf_file("large_document.pdf")
    print(f"Processed at 600 DPI: {result['output_dir']}")

# ============================================================================
# EXAMPLE 5: USING COMMAND LINE
# ============================================================================

"""
Command Line Usage:

1. Single file:
   python batch_process.py --input "C:/pdf/document.pdf"

2. Entire folder:
   python batch_process.py --input "C:/pdf/" --output "report.json"

3. Short form:
   python batch_process.py -i "file.pdf" -o "results.json"

Output will be timestamped folders in 'pdf_splits/' with ZIP files.
"""

# ============================================================================
# EXAMPLE 6: CHECK BEFORE PROCESSING
# ============================================================================

def example_6_verify_setup():
    """Verify everything is installed correctly"""
    from verify_setup import main as verify
    
    # Runs all checks
    is_ready = verify()
    
    if is_ready:
        print("Ready to process PDFs!")
    else:
        print("Install dependencies first")

# ============================================================================
# EXAMPLE 7: DETAILED PROCESSING WITH ANALYSIS
# ============================================================================

def example_7_detailed_analysis():
    """Process with detailed group analysis"""
    from work import process_pdf_file
    
    result = process_pdf_file("document.pdf")
    
    if result['status'] == 'success':
        print(f"\nDetailed Analysis:")
        print(f"Total Groups: {result['total_groups']}")
        print(f"Total PDFs Created: {len(result['pdf_files'])}")
        print(f"\nFile Breakdown:")
        
        for i, (file_no, start, end) in enumerate(result['groups'], 1):
            pages = end - start + 1
            print(f"  {i}. No.{file_no}")
            print(f"     Pages: {start + 1} - {end + 1} ({pages} pages)")
            print(f"     Output: {result['pdf_files'][i-1]}")
        
        print(f"\nZIP Bundle: {result['zip_file']}")

# ============================================================================
# EXAMPLE 8: CUSTOM PROCESSING SCRIPT
# ============================================================================

def example_8_custom_script():
    """Full custom processing script"""
    from work import process_pdf_file
    from pathlib import Path
    import json
    
    # Configuration
    INPUT_PDF = "C:/Downloads/large_document.pdf"
    SAVE_REPORT = True
    
    # Process
    print("Starting PDF split processing...")
    result = process_pdf_file(INPUT_PDF)
    
    if result['status'] == 'success':
        # Save detailed report
        if SAVE_REPORT:
            report = {
                'source_pdf': INPUT_PDF,
                'total_groups': result['total_groups'],
                'output_directory': result['output_dir'],
                'zip_file': result['zip_file'],
                'pdfs_created': result['pdf_files'],
                'groups': [
                    {'number': f, 'pages': f'{s+1}-{e+1}'}
                    for f, s, e in result['groups']
                ]
            }
            
            report_file = Path(result['output_dir']) / "processing_report.json"
            with open(report_file, 'w') as f:
                json.dump(report, f, indent=2)
            
            print(f"\n✓ Report saved to: {report_file}")
        
        print(f"✓ All files ready in: {result['output_dir']}")
    else:
        print(f"✗ Processing failed: {result['message']}")

# ============================================================================
# QUICK SETUP INSTRUCTIONS
# ============================================================================

SETUP_GUIDE = """
╔════════════════════════════════════════════════════════════════╗
║         PDF SPLIT FRAMEWORK - QUICK START                     ║
╚════════════════════════════════════════════════════════════════╝

STEP 1: Install Dependencies
────────────────────────────
pip install -r requirements.txt

STEP 2: Install Tesseract OCR
─────────────────────────────
Windows:
  Download: https://github.com/UB-Mannheim/tesseract/wiki
  Install to: C:\\Program Files\\Tesseract-OCR

Linux (Ubuntu/Debian):
  sudo apt-get install tesseract-ocr

macOS:
  brew install tesseract

STEP 3: Verify Installation
───────────────────────────
python verify_setup.py

STEP 4: Process Your PDF
───────────────────────
Option A - Python Code:
  from work import process_pdf_file
  result = process_pdf_file("your_file.pdf")

Option B - Command Line:
  python batch_process.py --input "your_file.pdf"

STEP 5: Get Results
──────────────────
Output files will be in:
  pdf_splits/session_[timestamp]/
    ├── 123.pdf         (Named by "No. 123" found on PDF)
    ├── 456.pdf         (Named by "No. 456" found on PDF)
    ├── 789.pdf         (Named by "No. 789" found on PDF)
    └── pdf_split_output.zip  ✓ Download this!

═══════════════════════════════════════════════════════════════════

Ready to process? Run example_1_basic() above! ✓
"""

# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    print(SETUP_GUIDE)
    
    # Uncomment to run an example:
    # example_1_basic()
    # example_2_error_handling()
    # example_7_detailed_analysis()
